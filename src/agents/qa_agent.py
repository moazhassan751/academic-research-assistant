from crewai import Agent
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import json
import re
import hashlib
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from functools import lru_cache
import numpy as np

from ..storage.models import Paper
from ..storage.database import db, get_async_db_manager
from ..llm.llm_factory import LLMFactory
from ..utils.app_logging import logger
from ..utils.performance_optimizer import optimizer, ultra_cache, turbo_batch_processor, fast_text

# Try to import advanced NLP libraries with fallbacks
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    logger.warning("sentence-transformers not installed. Using basic similarity.")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("scikit-learn not installed. Using basic similarity.")

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False
    logger.warning("rank-bm25 not installed. Using basic scoring.")


class QuestionAnsweringAgent:
    """High-performance QA agent with advanced optimization features"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the optimized QA agent"""
        self.config = config or {}
        self.llm = LLMFactory.create_llm()
        
        # Enhanced configuration with performance optimizations
        self.max_papers_for_context = self.config.get('max_papers_for_context', 12)  # Reduced for speed
        self.max_context_length = self.config.get('max_context_length', 8000)  # Optimized length
        self.min_relevance_score = self.config.get('min_relevance_score', 0.1)  # Very inclusive threshold
        self.max_parallel_papers = min(8, optimizer.get_optimal_thread_count('io'))  # Adaptive
        self.cache_ttl_hours = self.config.get('cache_ttl_hours', 24)
        
        # Performance optimization toggles
        self.use_semantic_embeddings = self.config.get('use_semantic_embeddings', HAS_SENTENCE_TRANSFORMERS)
        self.use_bm25_scoring = self.config.get('use_bm25_scoring', HAS_BM25)
        self.use_parallel_processing = self.config.get('use_parallel_processing', True)
        self.enable_caching = self.config.get('enable_caching', True)
        self.use_async_db = self.config.get('use_async_db', True)  # New: async database operations
        
        # Initialize async database manager
        if self.use_async_db:
            self.async_db = get_async_db_manager()
        else:
            self.async_db = None
        
        # Performance-optimized caches
        self.question_cache = {}
        self.paper_embedding_cache = {}
        self.relevance_cache = {}  # New: cache relevance calculations
        self.bm25_index = None
        self.bm25_papers = []
        
        # Initialize semantic models with optimizations
        self.sentence_model = None
        if self.use_semantic_embeddings and HAS_SENTENCE_TRANSFORMERS:
            try:
                import torch
                # Use smaller, faster model for better performance
                model_name = self.config.get('semantic_model', 'all-MiniLM-L6-v2')
                
                # Load model on CPU first to avoid meta tensor issues
                self.sentence_model = SentenceTransformer(model_name, device='cpu')
                
                # Move to appropriate device after loading
                if torch.cuda.is_available():
                    try:
                        self.sentence_model = self.sentence_model.to('cuda')
                    except Exception:
                        # Fallback to CPU if CUDA move fails
                        self.sentence_model = self.sentence_model.to('cpu')
                
                # Enable model optimizations
                if hasattr(self.sentence_model, 'eval'):
                    self.sentence_model.eval()  # Set to evaluation mode
                
                logger.info(f"Optimized semantic model loaded: {model_name}")
            except Exception as e:
                error_msg = str(e).lower()
                if any(term in error_msg for term in ["dns", "getaddrinfo", "connection", "timeout", "huggingface"]):
                    logger.warning(f"Network error loading semantic model: {e}")
                    logger.info("Falling back to TF-IDF vectorization only")
                else:
                    logger.warning(f"Failed to load semantic model: {e}")
                self.use_semantic_embeddings = False
        
        # Optimized TF-IDF vectorizer
        self.tfidf_vectorizer = None
        if HAS_SKLEARN:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=3000,  # Reduced for performance
                stop_words='english',
                ngram_range=(1, 2),
                dtype=np.float32  # Use float32 for memory efficiency
            )
        
        # Enhanced question patterns for faster classification
        self.question_patterns = {
            'what': ['what', 'which', 'who'],
            'how': ['how'],
            'why': ['why'],
            'when': ['when'],
            'where': ['where'],
            'comparison': ['compare', 'versus', 'vs', 'difference', 'similar'],
            'list': ['list', 'enumerate', 'name'],
            'definition': ['define', 'definition', 'meaning', 'what is'],
            'trend': ['trend', 'recent', 'latest', 'current', 'new'],
            'challenge': ['challenge', 'problem', 'issue', 'difficulty', 'limitation']
        }
        
        # Pre-compile regex patterns for performance
        self._compiled_patterns = {
            'key_terms': re.compile(r'\b[a-zA-Z]{3,}\b'),
            'stop_words': re.compile(r'\b(?:the|a|an|and|or|but|in|on|at|to|for|of|with|by|from|about|into|through|during|before|after|above|below|up|down|out|off|over|under|again|further|then|once|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|could|should|may|might)\b', re.IGNORECASE),
            'phrases': re.compile(r'\b[a-zA-Z]+(?:\s+[a-zA-Z]+){1,2}\b')
        }
        
        # Performance metrics
        self._performance_stats = {
            'total_questions': 0,
            'cache_hits': 0,
            'avg_response_time': 0.0,
            'db_query_time': 0.0,
            'llm_time': 0.0
        }
        
        # Optimize garbage collection
        optimizer.optimize_gc()
        
        logger.info(f"High-performance QA agent initialized with {self.max_parallel_papers} parallel workers")
        
        # Performance metrics
        self.metrics = {
            'total_questions': 0,
            'cache_hits': 0,
            'average_response_time': 0,
            'last_reset': datetime.now()
        }
        
        self.agent = Agent(
            role='Enhanced Research Question Answering Specialist',
            goal='Provide highly accurate, comprehensive answers by leveraging advanced NLP techniques and intelligent paper analysis',
            backstory="""You are an advanced AI research analyst equipped with state-of-the-art 
            natural language processing capabilities. You excel at semantic understanding, 
            multi-source information synthesis, and providing precise, well-cited answers to 
            complex research questions.""",
            verbose=True,
            llm=self.llm.generate if hasattr(self.llm, 'generate') else self.llm
        )
        
        logger.info(f"High-performance QA agent initialized with {self.max_parallel_papers} parallel workers")
    
    async def answer_question_async(self, question: str, research_topic: str = None, 
                                  paper_limit: int = None) -> Dict[str, Any]:
        """High-performance async question answering with optimization"""
        with optimizer.measure_performance('qa_total'):
            self._performance_stats['total_questions'] += 1
            start_time = time.perf_counter()
            
            try:
                # Quick cache check
                if self.enable_caching:
                    cache_key = self._generate_cache_key_fast(question, research_topic, paper_limit)
                    cached_result = await self._get_cached_result_async(cache_key)
                    if cached_result:
                        self._performance_stats['cache_hits'] += 1
                        logger.info(f"Cache hit for question: {question[:50]}...")
                        return cached_result
                
                logger.info(f"Processing optimized QA: {question[:100]}...")
                
                # Fast question preprocessing
                processed_question = self._preprocess_question_fast(question)
                question_type = self._classify_question_fast(processed_question)
                
                # Enhanced async paper retrieval
                with optimizer.measure_performance('paper_retrieval'):
                    relevant_papers = await self._enhanced_paper_retrieval_async(
                        processed_question, research_topic, paper_limit or self.max_papers_for_context
                    )
                
                if not relevant_papers:
                    return self._generate_no_results_response(question)
                
                # Parallel relevance scoring with async optimization
                with optimizer.measure_performance('relevance_scoring'):
                    ranked_papers = await self._parallel_relevance_scoring_async(
                        processed_question, relevant_papers, question_type
                    )
                
                # Select top papers with performance consideration
                top_papers = self._select_top_papers_optimized(ranked_papers)
                
                if not top_papers:
                    return self._generate_low_relevance_response(question)
                
                # Extract contexts efficiently
                with optimizer.measure_performance('context_extraction'):
                    contexts = await self._extract_contexts_async(
                        processed_question, top_papers, question_type
                    )
                
                # Generate answer with LLM optimization
                with optimizer.measure_performance('llm_generation'):
                    answer_data = await self._generate_answer_async(
                        processed_question, contexts, question_type
                    )
                
                # Compile final result
                final_result = self._compile_optimized_result(
                    question, answer_data, top_papers, contexts, question_type
                )
                
                # Cache result if enabled
                if self.enable_caching:
                    await self._cache_result_async(cache_key, final_result)
                
                # Update performance stats
                processing_time = time.perf_counter() - start_time
                self._update_performance_stats(processing_time)
                
                logger.info(f"Optimized QA completed in {processing_time:.2f}s")
                
                return final_result
                
            except Exception as e:
                logger.error(f"Optimized QA error: {e}", exc_info=True)
                return self._generate_error_response(str(e))
    

    def _create_fallback_response(self, question: str, paper_contexts: List[str] = None) -> Dict[str, Any]:
        """Create a comprehensive fallback response when LLM fails"""
        
        # Extract key terms from question
        import re
        key_terms = re.findall(r'\b[a-zA-Z]{4,}\b', question)
        key_terms = [term for term in key_terms if term.lower() not in 
                    ['what', 'when', 'where', 'which', 'this', 'that', 'with', 'from']][:5]
        
        # Create structured academic response
        if paper_contexts and len(paper_contexts) > 0:
            answer = f"""Based on the available research literature, I can provide some insights regarding {' '.join(key_terms[:3])}:

## Academic Research Overview

The current literature in this area suggests several important considerations:

1. **Research Context**: Multiple studies have examined this topic from various perspectives
2. **Methodological Approaches**: Researchers have employed different analytical frameworks
3. **Key Findings**: The evidence points to several significant patterns and trends

## Research Gaps and Future Directions

Current research indicates opportunities for:
- Further empirical investigation
- Methodological refinement  
- Cross-disciplinary collaboration
- Practical application development

*Note: This response was generated when the primary AI system encountered technical difficulties. For more detailed analysis, please rephrase your question or try again.*"""
        else:
            answer = f"""I understand you're asking about {' '.join(key_terms[:3])}. 

While I'm experiencing technical difficulties accessing the full research database, I can suggest some general research directions:

## Research Approach
1. **Literature Search**: Focus on peer-reviewed journals in relevant databases
2. **Key Terms**: Consider variations of: {', '.join(key_terms[:5])}
3. **Timeframe**: Include both recent studies and foundational works
4. **Methodology**: Look for both theoretical and empirical approaches

## Next Steps
- Try rephrasing your question with more specific terms
- Consider breaking complex questions into smaller parts
- Check if additional papers need to be added to the database

*This is a fallback response due to technical limitations. Please try your query again.*"""
        
        return {
            'answer': answer,
            'confidence': 0.3,
            'paper_count': len(paper_contexts) if paper_contexts else 0,
            'top_papers_used': min(3, len(paper_contexts)) if paper_contexts else 0,
            'sources': [],
            'status': 'fallback_response'
        }

    def answer_question(self, question: str, research_topic: str = None, 
                       paper_limit: int = None) -> Dict[str, Any]:
        """Synchronous wrapper for optimized async question answering"""
        try:
            # Use existing event loop if available, otherwise create new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create task for concurrent execution
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(self.answer_question_async(
                                question, research_topic, paper_limit
                            ))
                        )
                        return future.result()
                else:
                    return loop.run_until_complete(
                        self.answer_question_async(question, research_topic, paper_limit)
                    )
            except RuntimeError:
                # No event loop available, create new one
                return asyncio.run(
                    self.answer_question_async(question, research_topic, paper_limit)
                )
        except Exception as e:
            logger.error(f"Sync QA wrapper error: {e}")
            return self._generate_error_response(str(e))
            
            # Cache the result
            if self.enable_caching:
                self._cache_result(cache_key, final_result)
            
            # Update metrics
            self._update_metrics(processing_time)
            
            logger.info(f"Enhanced QA completed in {processing_time:.2f}s with "
                       f"{final_result.get('confidence', 0):.3f} confidence")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Enhanced QA error: {e}", exc_info=True)
            return self._generate_error_response(str(e))
    
    # Optimized helper methods for performance
    @ultra_cache(maxsize=1000, ttl=3600)  # 1 hour cache with ultra performance
    def _generate_cache_key_fast(self, question: str, research_topic: str = None, 
                               paper_limit: int = None) -> str:
        """Generate cache key with minimal processing"""
        key_parts = [question.lower()[:100]]  # Truncate for performance
        if research_topic:
            key_parts.append(research_topic.lower()[:50])
        if paper_limit:
            key_parts.append(str(paper_limit))
        return hashlib.md5('|'.join(key_parts).encode()).hexdigest()
    
    async def _get_cached_result_async(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Async cache retrieval"""
        if not self.enable_caching or cache_key not in self.question_cache:
            return None
        
        cached_data = self.question_cache[cache_key]
        if self._is_cache_valid_fast(cached_data):
            return cached_data['data']
        else:
            # Remove expired cache entry
            del self.question_cache[cache_key]
            return None
    
    def _is_cache_valid_fast(self, cached_data: Dict) -> bool:
        """Fast cache validation"""
        if 'timestamp' not in cached_data:
            return False
        
        cache_age = time.time() - cached_data['timestamp']
        return cache_age < (self.cache_ttl_hours * 3600)
    
    def _preprocess_question_fast(self, question: str) -> str:
        """Optimized question preprocessing"""
        # Fast preprocessing with pre-compiled regex
        processed = re.sub(r'\s+', ' ', question.strip().lower())
        
        # Fast abbreviation expansion (only common ones)
        abbreviations = {
            'ml': 'machine learning', 'ai': 'artificial intelligence', 
            'dl': 'deep learning', 'nlp': 'natural language processing'
        }
        
        for abbr, full in abbreviations.items():
            if abbr in processed:
                processed = processed.replace(abbr, full)
        
        return processed
    
    def _classify_question_fast(self, question: str) -> str:
        """Fast question classification using pre-compiled patterns"""
        question_lower = question.lower()
        
        # Use most common patterns first for early exit
        for q_type, patterns in [
            ('what', ['what', 'which', 'who']),
            ('how', ['how']),
            ('comparison', ['compare', 'versus', 'vs', 'difference']),
            ('definition', ['define', 'definition', 'meaning']),
            ('list', ['list', 'enumerate', 'name'])
        ]:
            if any(pattern in question_lower for pattern in patterns):
                return q_type
        
        return 'general'
    
    async def _enhanced_paper_retrieval_async(self, question: str, research_topic: str = None, 
                                            limit: int = 15) -> List[Paper]:
        """High-performance async paper retrieval using existing database methods"""
        try:
            all_papers = []
            key_terms = self._extract_key_terms_fast(question)
            
            # Use the sync database methods which are known to work
            # Build comprehensive search query
            search_terms = []
            if research_topic:
                search_terms.append(research_topic)
            search_terms.extend(key_terms[:3])  # Limit for performance
            
            # Search with each term and combine results
            for term in search_terms:
                papers = db.search_papers(term, limit=max(10, limit // len(search_terms)))
                all_papers.extend(papers)
            
            # Also search with the full question
            if question:
                papers = db.search_papers(question[:100], limit=limit//2)  # Truncate long questions
                all_papers.extend(papers)
            
            # Fast deduplication
            seen_ids = set()
            unique_papers = []
            for paper in all_papers:
                if paper.id not in seen_ids:
                    seen_ids.add(paper.id)
                    unique_papers.append(paper)
                    if len(unique_papers) >= limit * 2:  # Limit for performance
                        break
            
            logger.info(f"Retrieved {len(unique_papers)} unique papers for question: {question[:50]}...")
            return unique_papers
            
        except Exception as e:
            logger.error(f"Paper retrieval error: {e}")
            # Fallback: get recent papers
            try:
                return db.get_recent_papers(limit=min(20, limit))
            except:
                return []
    
    def _extract_key_terms_fast(self, question: str) -> List[str]:
        """Fast key term extraction using pre-compiled patterns"""
        try:
            # Use pre-compiled regex for performance
            words = self._compiled_patterns['key_terms'].findall(question.lower())
            
            # Filter stop words using pre-compiled regex
            words = [w for w in words if not self._compiled_patterns['stop_words'].match(w)]
            
            # Return top terms by length (longer = more specific)
            return sorted(set(words), key=len, reverse=True)[:8]
            
        except Exception as e:
            logger.warning(f"Fast key term extraction error: {e}")
            return [question.lower()]
    
    async def _parallel_relevance_scoring_async(self, question: str, papers: List[Paper], 
                                              question_type: str) -> List[Tuple[Paper, float]]:
        """High-performance parallel relevance scoring"""
        if not papers:
            return []
        
        try:
            # Determine optimal batch size based on system resources
            batch_size = min(len(papers), optimizer.get_optimal_thread_count('cpu') * 2)
            
            # Process papers in batches for optimal performance
            scored_papers = []
            
            for i in range(0, len(papers), batch_size):
                batch = papers[i:i + batch_size]
                batch_tasks = [
                    self._calculate_relevance_score_fast(question, paper, question_type)
                    for paper in batch
                ]
                
                batch_scores = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for j, score in enumerate(batch_scores):
                    if isinstance(score, (int, float)) and score >= self.min_relevance_score:
                        scored_papers.append((batch[j], score))
            
            # Sort by relevance score (descending)
            scored_papers.sort(key=lambda x: x[1], reverse=True)
            
            return scored_papers
            
        except Exception as e:
            logger.error(f"Parallel relevance scoring error: {e}")
            return [(paper, 0.1) for paper in papers]  # Fallback scoring
    
    async def _calculate_relevance_score_fast(self, question: str, paper: Paper, 
                                            question_type: str) -> float:
        """Fast relevance score calculation with improved scoring and caching"""
        cache_key = f"{hash(question)}{paper.id}{question_type}"
        
        if cache_key in self.relevance_cache:
            return self.relevance_cache[cache_key]
        
        try:
            # Fast text similarity with improved baseline
            title_score = self._fast_text_similarity(question, paper.title or "")
            abstract_score = self._fast_text_similarity(question, (paper.abstract or "")[:500])  # Truncate for speed
            
            # Weighted score with more generous baseline
            base_score = (title_score * 0.6) + (abstract_score * 0.4)
            
            # Give a minimum score for any paper that exists
            if base_score < 0.15:
                base_score = 0.15  # Minimum relevance for any paper
            
            # Citation boost for quality
            citation_boost = min(0.1, (paper.citations or 0) / 1000)
            
            # Question type specific boosts
            type_boost = 0.0
            if question_type in ['what', 'how', 'why']:
                type_boost = 0.05  # Basic question types get slight boost
            
            final_score = min(1.0, base_score + citation_boost + type_boost)
            
            # Cache result
            if len(self.relevance_cache) < 10000:  # Limit cache size
                self.relevance_cache[cache_key] = final_score
            
            return final_score
            
        except Exception as e:
            logger.warning(f"Relevance scoring error for paper {paper.id}: {e}")
            return 0.15  # More generous fallback
    
    def _fast_text_similarity(self, text1: str, text2: str) -> float:
        """Optimized text similarity calculation with improved scoring"""
        if not text1 or not text2:
            return 0.0
        
        # Normalize and split texts
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        jaccard_score = intersection / union if union > 0 else 0.0
        
        # Add fuzzy matching for partial word matches
        partial_matches = 0
        for w1 in words1:
            for w2 in words2:
                if len(w1) > 3 and len(w2) > 3:
                    # Check if words share significant prefixes/suffixes
                    if (w1.startswith(w2[:3]) or w2.startswith(w1[:3]) or 
                        w1.endswith(w2[-3:]) or w2.endswith(w1[-3:])):
                        partial_matches += 0.5
                        break
        
        # Boost score with partial matches
        partial_score = min(0.3, partial_matches / max(len(words1), len(words2)))
        
        # Give bonus for exact keyword matches
        tech_keywords = ['machine', 'learning', 'neural', 'network', 'algorithm', 'model', 
                        'data', 'analysis', 'research', 'study', 'method', 'approach']
        keyword_bonus = 0.0
        common_keywords = words1 & words2 & set(tech_keywords)
        if common_keywords:
            keyword_bonus = min(0.2, len(common_keywords) * 0.1)
        
        # Combined score with minimum baseline
        final_score = max(0.1, jaccard_score + partial_score + keyword_bonus)
        return min(1.0, final_score)
    
    def _select_top_papers_optimized(self, ranked_papers: List[Tuple[Paper, float]]) -> List[Tuple[Paper, float]]:
        """Select top papers with performance considerations"""
        if not ranked_papers:
            return []
        
        # Adaptive selection based on score distribution
        if len(ranked_papers) <= self.max_papers_for_context:
            return ranked_papers
        
        # Use top N papers and add diversity
        top_papers = ranked_papers[:self.max_papers_for_context]
        
        # Quick diversity check (different venues)
        seen_venues = set()
        diverse_papers = []
        
        for paper, score in top_papers:
            venue = (paper.venue or "").lower()
            if venue not in seen_venues or len(diverse_papers) < self.max_papers_for_context // 2:
                diverse_papers.append((paper, score))
                seen_venues.add(venue)
        
        return diverse_papers[:self.max_papers_for_context]
    
    async def _extract_contexts_async(self, question: str, top_papers: List[Tuple[Paper, float]], 
                                   question_type: str) -> List[Dict[str, Any]]:
        """Async context extraction with optimization"""
        if not top_papers:
            return []
        
        contexts = []
        max_context_per_paper = self.max_context_length // len(top_papers)
        
        # Process papers concurrently
        context_tasks = []
        for paper, score in top_papers:
            task = self._extract_paper_context_async(
                question, paper, score, question_type, max_context_per_paper
            )
            context_tasks.append(task)
        
        context_results = await asyncio.gather(*context_tasks, return_exceptions=True)
        
        for result in context_results:
            if isinstance(result, dict):
                contexts.append(result)
        
        return contexts[:self.max_papers_for_context]
    
    async def _extract_paper_context_async(self, question: str, paper: Paper, 
                                         score: float, question_type: str, 
                                         max_length: int) -> Dict[str, Any]:
        """Extract context from a single paper asynchronously"""
        try:
            # Prioritize abstract and title for speed
            full_text = f"{paper.title or ''} {paper.abstract or ''}"
            
            # Truncate for performance
            if len(full_text) > max_length:
                full_text = full_text[:max_length] + "..."
            
            return {
                'paper_id': paper.id,
                'title': paper.title,
                'authors': paper.authors,
                'content': full_text,
                'relevance_score': score,
                'citations': paper.citations or 0,
                'venue': paper.venue,
                'published_date': paper.published_date,
                'url': paper.url
            }
        except Exception as e:
            logger.warning(f"Context extraction error for paper {paper.id}: {e}")
            return {
                'paper_id': paper.id,
                'title': paper.title or 'Unknown',
                'content': 'Context extraction failed',
                'relevance_score': score
            }
    
    async def _generate_answer_async(self, question: str, contexts: List[Dict[str, Any]], 
                                   question_type: str) -> Dict[str, Any]:
        """Async answer generation with LLM optimization"""
        try:
            if not contexts:
                return {'answer': 'No relevant papers found for this question.', 'confidence': 0.0}
            
            # Create optimized prompt
            prompt = self._create_optimized_prompt(question, contexts, question_type)
            
            # Generate answer with async LLM if available
            if hasattr(self.llm, 'generate_async'):
                answer_text = await self.llm.generate_async(prompt)
            else:
                # Fallback to sync generation in thread
                loop = asyncio.get_event_loop()
                answer_text = await loop.run_in_executor(
                    None, lambda: self.llm.generate(prompt)
                )
            
            # Quick confidence estimation
            confidence = self._estimate_confidence_fast(answer_text, contexts)
            
            return {
                'answer': answer_text,
                'confidence': confidence,
                'source_count': len(contexts)
            }
            
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            return {
                'answer': 'Error generating answer. Please try again.',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _create_optimized_prompt(self, question: str, contexts: List[Dict[str, Any]], 
                               question_type: str) -> str:
        """Create optimized prompt for faster LLM processing"""
        # Shorter, more focused prompts for better performance
        context_text = "\n\n".join([
            f"Paper {i+1}: {ctx.get('title', 'Unknown')}\n{ctx.get('content', '')[:300]}..."
            for i, ctx in enumerate(contexts[:5])  # Limit contexts for speed
        ])
        
        prompt_templates = {
            'definition': f"Define and explain: {question}\n\nBased on these papers:\n{context_text}\n\nProvide a concise definition:",
            'comparison': f"Compare and analyze: {question}\n\nBased on these papers:\n{context_text}\n\nProvide a structured comparison:",
            'how': f"Explain the method/process: {question}\n\nBased on these papers:\n{context_text}\n\nProvide step-by-step explanation:",
        }
        
        return prompt_templates.get(question_type, 
            f"Answer this question: {question}\n\nBased on these research papers:\n{context_text}\n\nProvide a comprehensive answer:"
        )
    
    def _estimate_confidence_fast(self, answer: str, contexts: List[Dict[str, Any]]) -> float:
        """Fast confidence estimation with improved scoring"""
        if not answer or len(answer) < 50:
            return 0.2
        
        # Base confidence starts higher
        base_confidence = 0.4
        
        # Length factor - more substantial answers get higher confidence
        length_factor = 0.0
        if len(answer) > 100:
            length_factor = 0.1
        if len(answer) > 200:
            length_factor = 0.2
        if len(answer) > 500:
            length_factor = 0.3
        
        # Source factor - multiple sources increase confidence
        source_factor = 0.0
        if len(contexts) >= 1:
            source_factor = 0.2
        if len(contexts) >= 3:
            source_factor = 0.3
        if len(contexts) >= 5:
            source_factor = 0.4
        
        # Content quality indicators
        quality_factor = 0.0
        
        # Citation mentions
        citation_keywords = ['citation', 'study', 'research', 'paper', 'author']
        if any(keyword in answer.lower() for keyword in citation_keywords):
            quality_factor += 0.1
        
        # Definitiveness indicators
        definitive_words = ['research shows', 'studies indicate', 'evidence suggests', 
                          'findings demonstrate', 'results show', 'data reveals']
        if any(word in answer.lower() for word in definitive_words):
            quality_factor += 0.1
        
        # Technical terminology suggests domain knowledge
        tech_words = ['method', 'approach', 'analysis', 'framework', 'model', 'algorithm']
        if any(word in answer.lower() for word in tech_words):
            quality_factor += 0.05
        
        total_confidence = base_confidence + length_factor + source_factor + quality_factor
        return min(0.95, max(0.2, total_confidence))
    
    def _compile_optimized_result(self, question: str, answer_data: Dict[str, Any], 
                                top_papers: List[Tuple[Paper, float]], 
                                contexts: List[Dict[str, Any]], 
                                question_type: str) -> Dict[str, Any]:
        """Compile optimized final result"""
        return {
            'question': question,
            'answer': answer_data.get('answer', ''),
            'confidence': answer_data.get('confidence', 0.0),
            'question_type': question_type,
            'source_papers': [
                {
                    'id': paper.id,
                    'title': paper.title,
                    'authors': paper.authors,
                    'relevance_score': score,
                    'citations': paper.citations or 0,
                    'url': paper.url
                }
                for paper, score in top_papers[:5]  # Limit for performance
            ],
            'metadata': {
                'paper_count': len(top_papers),
                'processing_optimized': True,
                'cache_enabled': self.enable_caching,
                'timestamp': datetime.now().isoformat()
            }
        }
    
    async def _cache_result_async(self, cache_key: str, result: Dict[str, Any]):
        """Async cache storage with cleanup"""
        if not self.enable_caching:
            return
        
        # Limit cache size for memory management
        if len(self.question_cache) >= 1000:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self.question_cache))
            del self.question_cache[oldest_key]
        
        self.question_cache[cache_key] = {
            'data': result,
            'timestamp': time.time()
        }
    
    def _update_performance_stats(self, processing_time: float):
        """Update performance statistics"""
        self._performance_stats['avg_response_time'] = (
            self._performance_stats['avg_response_time'] * (self._performance_stats['total_questions'] - 1) +
            processing_time
        ) / self._performance_stats['total_questions']
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        return {
            **self._performance_stats,
            'cache_hit_rate': (
                self._performance_stats['cache_hits'] / 
                max(1, self._performance_stats['total_questions'])
            ),
            'optimizer_stats': optimizer.get_performance_summary()
        }
        """Enhanced question preprocessing"""
        processed = re.sub(r'\s+', ' ', question.strip())
        
        # Expand common abbreviations
        abbreviations = {
            'ml': 'machine learning', 'ai': 'artificial intelligence', 
            'dl': 'deep learning', 'nlp': 'natural language processing',
            'cv': 'computer vision', 'nn': 'neural network'
        }
        
        for abbr, full in abbreviations.items():
            processed = re.sub(r'\b' + abbr + r'\b', full, processed, flags=re.IGNORECASE)
        
        return processed
    
    def _classify_question(self, question: str) -> str:
        """Classify question type for better processing"""
        question_lower = question.lower()
        
        for q_type, patterns in self.question_patterns.items():
            for pattern in patterns:
                if pattern in question_lower:
                    return q_type
        
        return 'general'
    
    def _enhanced_paper_retrieval(self, question: str, research_topic: str = None, 
                                limit: int = 15) -> List[Paper]:
        """Enhanced paper retrieval using multiple strategies"""
        try:
            all_papers = []
            key_terms = self._extract_enhanced_key_terms(question)
            
            # Strategy 1: Semantic search if available
            if self.use_semantic_embeddings and self.sentence_model:
                semantic_papers = self._semantic_paper_search(question, limit)
                all_papers.extend(semantic_papers)
            
            # Strategy 2: Traditional keyword search
            for term in key_terms[:5]:
                papers = db.search_papers(term, limit=max(10, limit // len(key_terms)))
                all_papers.extend(papers)
            
            # Strategy 3: Topic-based filtering
            if research_topic:
                topic_papers = db.search_papers(research_topic, limit=limit)
                all_papers.extend(topic_papers)
            
            # Remove duplicates
            seen_titles = set()
            unique_papers = []
            for paper in all_papers:
                if paper.title and paper.title not in seen_titles:
                    seen_titles.add(paper.title)
                    unique_papers.append(paper)
            
            return unique_papers[:limit * 2]
            
        except Exception as e:
            logger.error(f"Enhanced paper retrieval error: {e}")
            return []
    
    def _extract_enhanced_key_terms(self, question: str) -> List[str]:
        """Enhanced key term extraction"""
        try:
            system_prompt = "Extract the most important technical terms for academic paper search."
            prompt = f"Question: {question}\nExtract key terms as JSON array: [\"term1\", \"term2\"]"
            
            try:
                response = self.llm.generate(prompt, system_prompt) if hasattr(self.llm, 'generate') else self.llm(prompt)
                json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
                if json_match:
                    terms = json.loads(json_match.group(0))
                    return [term.strip().lower() for term in terms if isinstance(term, str)]
            except Exception:
                pass
            
            return self._regex_key_extraction(question)
            
        except Exception as e:
            logger.warning(f"Key term extraction error: {e}")
            return self._regex_key_extraction(question)
    
    def _regex_key_extraction(self, question: str) -> List[str]:
        """Fallback regex-based key extraction"""
        stop_words = {
            'what', 'are', 'the', 'how', 'why', 'when', 'where', 'which', 'who',
            'is', 'in', 'on', 'at', 'for', 'with', 'by', 'from', 'about'
        }
        
        words = re.findall(r'\b[a-zA-Z]+\b', question.lower())
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        
        terms = []
        for word in words:
            if len(word) > 3 and word not in stop_words:
                terms.append(word)
        
        for phrase in bigrams:
            if not any(stop in phrase.split() for stop in stop_words):
                terms.append(phrase)
        
        return terms[:8]
    
    def _semantic_paper_search(self, question: str, limit: int) -> List[Paper]:
        """Semantic search using sentence embeddings"""
        try:
            question_embedding = self.sentence_model.encode([question])
            all_papers = db.get_all_papers()
            
            paper_similarities = []
            for paper in all_papers:
                paper_text = f"{paper.title or ''} {paper.abstract or ''}"
                if not paper_text.strip():
                    continue
                
                try:
                    paper_embedding = self.sentence_model.encode([paper_text])
                    similarity = cosine_similarity(question_embedding, paper_embedding)[0][0]
                    paper_similarities.append((paper, similarity))
                except Exception:
                    continue
            
            paper_similarities.sort(key=lambda x: x[1], reverse=True)
            return [paper for paper, sim in paper_similarities[:limit] if sim > 0.3]
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    def _enhanced_relevance_ranking(self, question: str, papers: List[Paper], 
                                  question_type: str) -> List[Tuple[Paper, float]]:
        """Enhanced relevance ranking with multiple scoring methods"""
        try:
            scored_papers = []
            
            for paper in papers:
                score = 0.0
                
                # Semantic similarity (if available)
                if self.use_semantic_embeddings and self.sentence_model:
                    semantic_score = self._calculate_semantic_similarity(question, paper)
                    score += semantic_score * 0.4
                
                # Enhanced text similarity
                text_score = self._calculate_enhanced_text_similarity(question, paper)
                score += text_score * 0.4
                
                # Question-type specific scoring
                type_score = self._calculate_type_specific_score(question, paper, question_type)
                score += type_score * 0.1
                
                # Citation bonus
                if hasattr(paper, 'citations') and paper.citations:
                    citation_bonus = min(0.1, paper.citations / 1000)
                    score += citation_bonus
                
                scored_papers.append((paper, score))
            
            scored_papers.sort(key=lambda x: x[1], reverse=True)
            
            relevant_papers = [
                (paper, score) for paper, score in scored_papers 
                if score >= self.min_relevance_score
            ]
            
            return relevant_papers
            
        except Exception as e:
            logger.error(f"Enhanced ranking error: {e}")
            return [(paper, 0.5) for paper in papers]
    
    def _calculate_semantic_similarity(self, question: str, paper: Paper) -> float:
        """Calculate semantic similarity using embeddings"""
        try:
            paper_text = f"{paper.title or ''} {paper.abstract or ''}"
            if not paper_text.strip():
                return 0.0
            
            question_emb = self.sentence_model.encode([question])
            paper_emb = self.sentence_model.encode([paper_text])
            
            similarity = cosine_similarity(question_emb, paper_emb)[0][0]
            return max(0.0, similarity)
            
        except Exception:
            return 0.0
    
    def _calculate_enhanced_text_similarity(self, question: str, paper: Paper) -> float:
        """Enhanced text similarity with improved algorithms"""
        try:
            title_sim = self._improved_text_similarity(question, paper.title or "")
            abstract_sim = self._improved_text_similarity(question, paper.abstract or "")
            keywords_sim = self._improved_text_similarity(question, paper.keywords or "")
            
            total_score = (title_sim * 0.5) + (abstract_sim * 0.4) + (keywords_sim * 0.1)
            return min(1.0, total_score)
            
        except Exception:
            return 0.0
    
    def _improved_text_similarity(self, text1: str, text2: str) -> float:
        """Improved text similarity calculation"""
        try:
            if not text1 or not text2:
                return 0.0
            
            words1 = set(self._extract_meaningful_words(text1.lower()))
            words2 = set(self._extract_meaningful_words(text2.lower()))
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            if not union:
                return 0.0
            
            jaccard_sim = len(intersection) / len(union)
            
            # Add bonus for exact phrase matches
            phrase_bonus = 0.0
            if len(intersection) > 0:
                text1_phrases = self._extract_phrases(text1.lower())
                text2_phrases = self._extract_phrases(text2.lower())
                phrase_matches = len(text1_phrases.intersection(text2_phrases))
                phrase_bonus = min(0.2, phrase_matches * 0.05)
            
            return min(1.0, jaccard_sim + phrase_bonus)
            
        except Exception:
            return 0.0
    
    def _extract_meaningful_words(self, text: str) -> List[str]:
        """Extract meaningful words filtering out stop words"""
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'up', 'down', 'out', 'off',
            'over', 'under', 'again', 'further', 'then', 'once', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might'
        }
        
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        return [word for word in words if len(word) > 2 and word not in stop_words]
    
    def _extract_phrases(self, text: str) -> Set[str]:
        """Extract meaningful phrases from text"""
        words = self._extract_meaningful_words(text)
        phrases = set()
        
        for i in range(len(words) - 1):
            phrases.add(f"{words[i]} {words[i+1]}")
        
        for i in range(len(words) - 2):
            phrases.add(f"{words[i]} {words[i+1]} {words[i+2]}")
        
        return phrases
    
    def _calculate_type_specific_score(self, question: str, paper: Paper, question_type: str) -> float:
        """Calculate question-type specific relevance score"""
        try:
            paper_text = f"{paper.title or ''} {paper.abstract or ''}"
            
            type_keywords = {
                'comparison': ['compare', 'versus', 'contrast', 'difference', 'similar'],
                'trend': ['recent', 'latest', 'current', 'new', 'emerging', 'trend'],
                'challenge': ['challenge', 'problem', 'issue', 'limitation', 'difficulty'],
                'definition': ['define', 'definition', 'concept', 'framework', 'model'],
                'how': ['method', 'approach', 'technique', 'process', 'algorithm'],
                'list': ['survey', 'review', 'overview', 'taxonomy', 'classification']
            }
            
            if question_type not in type_keywords:
                return 0.0
            
            keywords = type_keywords[question_type]
            paper_lower = paper_text.lower()
            
            matches = sum(1 for keyword in keywords if keyword in paper_lower)
            return min(0.3, matches * 0.1)
            
        except Exception:
            return 0.0
    
    def _extract_enhanced_contexts(self, question: str, ranked_papers: List[Tuple[Paper, float]], 
                                 question_type: str) -> List[Dict[str, Any]]:
        """Extract enhanced contexts with intelligent content selection"""
        contexts = []
        
        for paper, relevance_score in ranked_papers[:self.max_papers_for_context]:
            try:
                context = {
                    'paper': paper,
                    'relevance_score': relevance_score,
                    'title': paper.title or 'Unknown Title',
                    'authors': self._format_authors(paper.authors),
                    'year': self._extract_year(paper),
                    'citations': getattr(paper, 'citations', 0),
                    'relevant_text': self._extract_most_relevant_text(question, paper, question_type)
                }
                contexts.append(context)
                
            except Exception as e:
                logger.warning(f"Error extracting context from paper: {e}")
                continue
        
        return contexts
    
    def _format_authors(self, authors) -> str:
        """Format authors list for display"""
        if not authors:
            return "Unknown Authors"
        
        if isinstance(authors, str):
            return authors
        
        if isinstance(authors, list):
            if len(authors) <= 3:
                return ', '.join(authors)
            else:
                return f"{', '.join(authors[:3])} et al."
        
        return str(authors)
    
    def _extract_year(self, paper: Paper) -> str:
        """Extract publication year"""
        try:
            if hasattr(paper, 'published_date') and paper.published_date:
                if hasattr(paper.published_date, 'year'):
                    return str(paper.published_date.year)
                else:
                    return str(paper.published_date)[:4]
            return "Unknown Year"
        except Exception:
            return "Unknown Year"
    
    def _extract_most_relevant_text(self, question: str, paper: Paper, question_type: str) -> str:
        """Extract the most relevant text snippets from a paper"""
        try:
            text_sources = []
            
            if paper.title:
                text_sources.append(f"Title: {paper.title}")
            
            if paper.abstract:
                relevant_abstract = self._extract_relevant_sentences(
                    question, paper.abstract, max_sentences=3
                )
                text_sources.append(f"Abstract: {relevant_abstract}")
            
            if paper.keywords:
                text_sources.append(f"Keywords: {paper.keywords}")
            
            combined_text = " | ".join(text_sources)
            
            if len(combined_text) > 1200:
                title_part = text_sources[0] if text_sources else ""
                abstract_part = text_sources[1] if len(text_sources) > 1 else ""
                
                available_length = 1200 - len(title_part) - 20
                if len(abstract_part) > available_length:
                    abstract_part = abstract_part[:available_length] + "..."
                
                combined_text = f"{title_part} | {abstract_part}"
            
            return combined_text
            
        except Exception as e:
            logger.warning(f"Error extracting relevant text: {e}")
            return f"Title: {paper.title or 'N/A'}"
    
    def _extract_relevant_sentences(self, question: str, text: str, max_sentences: int = 3) -> str:
        """Extract most relevant sentences from text"""
        try:
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            if len(sentences) <= max_sentences:
                return text
            
            question_words = set(self._extract_meaningful_words(question.lower()))
            scored_sentences = []
            
            for sentence in sentences:
                sentence_words = set(self._extract_meaningful_words(sentence.lower()))
                overlap = len(question_words.intersection(sentence_words))
                score = overlap / len(question_words) if question_words else 0
                scored_sentences.append((sentence, score))
            
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [sent for sent, score in scored_sentences[:max_sentences]]
            
            return '. '.join(top_sentences) + '.'
            
        except Exception:
            return text
    
    def _generate_enhanced_answer(self, question: str, paper_contexts: List[Dict[str, Any]], 
                                question_type: str) -> Dict[str, Any]:
        """Generate enhanced answer using question-type specific prompts"""
        try:
            if not paper_contexts:
                return {
                    'answer': "No relevant papers found to answer the question.",
                    'sources': [],
                    'confidence': 0.0
                }
            
            context_text = self._prepare_enhanced_context_for_llm(paper_contexts, question_type)
            
            # Question-type specific system prompt
            type_prompts = {
                'comparison': "Focus on identifying similarities, differences, and relative advantages/disadvantages.",
                'trend': "Focus on recent developments, emerging patterns, and future directions.", 
                'challenge': "Focus on identifying problems, limitations, and obstacles in the field.",
                'definition': "Focus on clear, comprehensive definitions with context and examples.",
                'how': "Focus on methods, processes, and step-by-step explanations.",
                'list': "Focus on comprehensive, well-organized lists with explanations."
            }
            
            specific_guidance = type_prompts.get(question_type, "Provide comprehensive, well-structured answers with proper citations.")
            
            system_prompt = f"You are an expert research analyst. {specific_guidance}"
            
            prompt = f"""
            Question: {question}
            Question Type: {question_type}
            
            Based on the following research papers, provide a comprehensive answer:
            
            {context_text}
            
            Structure your answer clearly with proper citations in [Author, Year] format.
            """
            
            response = self.llm.generate(prompt, system_prompt) if hasattr(self.llm, 'generate') else self.llm(prompt)
            
            confidence = self._calculate_enhanced_confidence(paper_contexts, response)
            sources = self._extract_enhanced_sources_from_contexts(paper_contexts)
            
            return {
                'answer': response,
                'sources': sources,
                'confidence': confidence,
                'answer_quality_score': self._assess_answer_quality(response, question)
            }
            
        except Exception as e:
            logger.error(f"Error generating enhanced answer: {e}")
            return {
                'answer': f"Error generating answer: {str(e)}",
                'sources': [],
                'confidence': 0.0
            }
    
    def _prepare_enhanced_context_for_llm(self, paper_contexts: List[Dict[str, Any]], 
                                        question_type: str) -> str:
        """Prepare enhanced context optimized for question type"""
        context_parts = []
        
        for i, context in enumerate(paper_contexts, 1):
            paper_info = f"""
            Paper {i} (Relevance: {context['relevance_score']:.3f}):
            Title: {context['title']}
            Authors: {context['authors']}
            Year: {context['year']}
            Citations: {context['citations']}
            
            Content: {context['relevant_text']}
            ---"""
            context_parts.append(paper_info)
        
        full_context = "\n".join(context_parts)
        
        if len(full_context) > self.max_context_length:
            truncated_parts = []
            current_length = 0
            
            for part in context_parts:
                if current_length + len(part) <= self.max_context_length - 100:
                    truncated_parts.append(part)
                    current_length += len(part)
                else:
                    break
            
            full_context = "\n".join(truncated_parts)
            full_context += "\n\n[Additional papers available but truncated for context length...]"
        
        return full_context
    
    def _calculate_enhanced_confidence(self, paper_contexts: List[Dict[str, Any]], answer: str) -> float:
        """Calculate enhanced confidence score"""
        try:
            if not paper_contexts or not answer:
                return 0.0
            
            # Average paper relevance
            avg_relevance = sum(ctx['relevance_score'] for ctx in paper_contexts) / len(paper_contexts)
            relevance_factor = min(1.0, avg_relevance / 0.5)
            
            # Number of papers
            paper_count_factor = min(1.0, len(paper_contexts) / 8)
            
            # Answer length and detail
            answer_length = len(answer.split())
            length_factor = min(1.0, max(0.3, answer_length / 200))
            
            # Citation presence
            citation_count = len(re.findall(r'\[.*?\]', answer))
            citation_factor = min(1.0, citation_count / len(paper_contexts))
            
            confidence = (
                relevance_factor * 0.4 +
                paper_count_factor * 0.2 +
                length_factor * 0.2 +
                citation_factor * 0.2
            )
            
            return min(1.0, confidence)
            
        except Exception as e:
            logger.warning(f"Error calculating confidence: {e}")
            return 0.5
    
    def _assess_answer_quality(self, answer: str, question: str) -> float:
        """Assess the quality of the generated answer"""
        try:
            score = 0.0
            
            word_count = len(answer.split())
            if 50 <= word_count <= 500:
                score += 0.2
            
            if '**' in answer or '#' in answer:
                score += 0.2
            
            citation_count = len(re.findall(r'\[.*?\]', answer))
            if citation_count > 0:
                score += 0.2
            
            question_words = set(self._extract_meaningful_words(question.lower()))
            answer_words = set(self._extract_meaningful_words(answer.lower()))
            overlap_ratio = len(question_words.intersection(answer_words)) / len(question_words)
            score += overlap_ratio * 0.4
            
            return min(1.0, score)
            
        except Exception:
            return 0.5
    
    def _extract_enhanced_sources_from_contexts(self, paper_contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract enhanced source information"""
        sources = []
        
        for context in paper_contexts:
            paper = context['paper']
            source = {
                'title': context['title'],
                'authors': context['authors'],
                'year': context['year'],
                'citations': context['citations'],
                'relevance_score': context['relevance_score'],
                'url': getattr(paper, 'url', None),
                'doi': getattr(paper, 'doi', None),
                'source_database': getattr(paper, 'source', 'Unknown')
            }
            sources.append(source)
        
        return sources
    
    def _post_process_answer(self, answer_result: Dict[str, Any], question_type: str) -> Dict[str, Any]:
        """Post-process the answer for final enhancements"""
        try:
            answer = answer_result.get('answer', '')
            
            # Clean up the answer text
            answer = re.sub(r'\n\s*\n\s*\n', '\n\n', answer)
            answer = re.sub(r'\s+', ' ', answer)
            
            answer_result['answer'] = answer.strip()
            
            return answer_result
            
        except Exception as e:
            logger.warning(f"Post-processing error: {e}")
            return answer_result
    
    def get_enhanced_follow_up_questions(self, question: str, answer_result: Dict[str, Any]) -> List[str]:
        """Generate enhanced follow-up questions"""
        try:
            if not answer_result.get('answer') or answer_result.get('confidence', 0) < 0.3:
                return []
            
            question_type = answer_result.get('question_type', 'general')
            
            system_prompt = f"Generate insightful follow-up questions for {question_type} questions."
            
            prompt = f"""
            Original Question: {question}
            Question Type: {question_type}
            Answer Summary: {answer_result['answer'][:300]}...
            
            Generate 3-5 relevant follow-up questions as JSON array: ["question1", "question2"]
            """
            
            response = self.llm.generate(prompt, system_prompt) if hasattr(self.llm, 'generate') else self.llm(prompt)
            
            json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
            if json_match:
                try:
                    questions = json.loads(json_match.group(0))
                    return [q.strip() for q in questions if isinstance(q, str)][:5]
                except json.JSONDecodeError:
                    pass
            
            return self._generate_simple_followups(question, question_type)
            
        except Exception as e:
            logger.warning(f"Error generating follow-up questions: {e}")
            return []
    
    def _generate_simple_followups(self, question: str, question_type: str) -> List[str]:
        """Generate simple follow-up questions based on patterns"""
        base_followups = {
            'trend': [
                f"What are the future directions in this area?",
                f"What are the main challenges in implementing these trends?",
                f"How do these trends compare to previous approaches?"
            ],
            'challenge': [
                f"What solutions have been proposed for these challenges?",
                f"Which challenges are most critical to address?",
                f"How are researchers currently tackling these problems?"
            ]
        }
        
        return base_followups.get(question_type, [
            "What are the current research challenges in this area?",
            "What are the practical applications of these findings?",
            "How is this field likely to evolve in the future?"
        ])
    
    # Cache management methods
    def _generate_cache_key(self, question: str, research_topic: str, paper_limit: int) -> str:
        """Generate cache key for question"""
        key_string = f"{question}|{research_topic}|{paper_limit}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cached_result: Dict[str, Any]) -> bool:
        """Check if cached result is still valid"""
        try:
            cache_time = datetime.fromisoformat(cached_result['timestamp'])
            age_hours = (datetime.now() - cache_time).total_seconds() / 3600
            return age_hours < self.cache_ttl_hours
        except Exception:
            return False
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache the result"""
        if not self.enable_caching:
            return
        
        try:
            self.question_cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now().isoformat()
            }
            
            if len(self.question_cache) > 100:
                sorted_items = sorted(self.question_cache.items(), key=lambda x: x[1]['timestamp'])
                for key, _ in sorted_items[:20]:
                    del self.question_cache[key]
                    
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
    
    def _update_metrics(self, processing_time: float) -> None:
        """Update performance metrics"""
        try:
            self.metrics['average_response_time'] = (
                (self.metrics['average_response_time'] * (self.metrics['total_questions'] - 1) + 
                 processing_time) / self.metrics['total_questions']
            )
        except Exception:
            pass
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            **self.metrics,
            'cache_size': len(self.question_cache),
            'features_enabled': {
                'semantic_embeddings': self.use_semantic_embeddings,
                'bm25_scoring': self.use_bm25_scoring,
                'parallel_processing': self.use_parallel_processing,
                'caching': self.enable_caching
            }
        }
    
    def clear_cache(self) -> None:
        """Clear the question cache"""
        self.question_cache.clear()
        logger.info("Question cache cleared")
    
    def _generate_no_papers_response(self, question: str) -> Dict[str, Any]:
        """Generate response when no papers are found"""
        return {
            'answer': f"I couldn't find relevant papers to answer your question: '{question}'. "
                     f"Try broadening your search terms or researching this topic first.",
            'sources': [],
            'confidence': 0.0,
            'paper_count': 0
        }
    
    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            'answer': f"An error occurred while processing your question: {error_message}",
            'sources': [],
            'confidence': 0.0,
            'paper_count': 0,
            'error': error_message
        }
    
    def _generate_no_results_response(self, question: str) -> Dict[str, Any]:
        """Generate response when no relevant papers are found"""
        return {
            'answer': f"I don't have enough relevant papers in the database to answer the question: '{question}'. Please try conducting research on this topic first using the 'research' command, or search for papers related to your question.",
            'sources': [],
            'confidence': 0.0,
            'paper_count': 0,
            'follow_up_questions': [
                f"What papers should I search for related to: {question}?",
                "How can I find more research on this topic?"
            ]
        }
    
    def _generate_low_relevance_response(self, question: str) -> Dict[str, Any]:
        """Generate response when papers have low relevance scores"""
        return {
            'answer': f"I found some papers in the database, but they don't seem highly relevant to your question: '{question}'. The available papers may contain some related information, but I cannot provide a confident answer. Please try rephrasing your question or conducting more specific research on this topic.",
            'sources': [],
            'confidence': 0.2,
            'paper_count': 0,
            'follow_up_questions': [
                f"Can you rephrase this question: {question}?",
                "What specific aspects would you like to know more about?",
                "Should I search for more papers on this topic?"
            ]
        }
    
    # Backward compatibility methods
    def get_follow_up_questions(self, question: str, answer_result: Dict[str, Any]) -> List[str]:
        """Backward compatibility method"""
        return self.get_enhanced_follow_up_questions(question, answer_result)
    
    def _generate_answer(self, question: str, paper_contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive answer based on paper contexts"""
        try:
            if not paper_contexts:
                return {
                    'answer': "No relevant papers found to answer the question.",
                    'sources': [],
                    'confidence': 0.0
                }
            
            # Prepare context for LLM
            context_text = self._prepare_context_for_llm(paper_contexts)
            
            system_prompt = """You are a research expert who synthesizes information from academic papers 
            to answer complex research questions. Provide comprehensive, well-structured answers with proper citations."""
            
            prompt = f"""
            Question: {question}
            
            Based on the following research papers, provide a comprehensive answer:
            
            {context_text}
            
            Instructions:
            1. Provide a detailed, well-structured answer
            2. Synthesize information from multiple sources when possible
            3. Include specific findings, trends, and challenges mentioned in the papers
            4. Cite sources using [Author, Year] format
            5. If there are conflicting findings, mention them
            6. Conclude with key insights and future directions if mentioned
            
            Format your response as:
            
            **Answer:**
            [Your comprehensive answer here]
            
            **Key Findings:**
            - [Bullet points of key findings]
            
            **Sources Used:**
            [List of sources cited]
            """
            
            response = self.llm.generate(prompt, system_prompt) if hasattr(self.llm, 'generate') else self.llm(prompt)
            
            # Calculate confidence based on paper relevance and count
            confidence = self._calculate_answer_confidence(paper_contexts)
            
            # Extract sources for structured output
            sources = self._extract_sources_from_contexts(paper_contexts)
            
            return {
                'answer': response,
                'sources': sources,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return {
                'answer': f"Error generating answer: {str(e)}",
                'sources': [],
                'confidence': 0.0
            }
    
    def _prepare_context_for_llm(self, paper_contexts: List[Dict[str, Any]]) -> str:
        """Prepare paper contexts for LLM input"""
        context_parts = []
        
        for i, context in enumerate(paper_contexts, 1):
            paper_info = f"""
            Paper {i}:
            Title: {context['title']}
            Authors: {context['authors']}
            Year: {context['year']}
            Citations: {context['citations']}
            Relevance Score: {context['relevance_score']:.3f}
            
            Content: {context['relevant_text']}
            
            ---
            """
            context_parts.append(paper_info)
        
        full_context = "\n".join(context_parts)
        
        # Truncate if too long to fit in context window
        if len(full_context) > self.max_context_length:
            full_context = full_context[:self.max_context_length] + "\n\n[Context truncated...]"
        
        return full_context
    
    def _calculate_answer_confidence(self, paper_contexts: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for the answer"""
        if not paper_contexts:
            return 0.0
        
        # Base confidence on average relevance score and number of papers
        avg_relevance = sum(ctx['relevance_score'] for ctx in paper_contexts) / len(paper_contexts)
        paper_count_factor = min(1.0, len(paper_contexts) / 5)  # Max factor at 5+ papers
        
        confidence = (avg_relevance * 0.7) + (paper_count_factor * 0.3)
        return min(1.0, confidence)
    
    def _extract_sources_from_contexts(self, paper_contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract structured source information"""
        sources = []
        
        for context in paper_contexts:
            paper = context['paper']
            source = {
                'title': context['title'],
                'authors': context['authors'],
                'year': context['year'],
                'citations': context['citations'],
                'relevance_score': context['relevance_score'],
                'url': getattr(paper, 'url', None),
                'doi': getattr(paper, 'doi', None)
            }
            sources.append(source)
        
        return sources
    
    def get_follow_up_questions(self, question: str, answer_result: Dict[str, Any]) -> List[str]:
        """Generate follow-up questions based on the answer"""
        try:
            if not answer_result.get('answer') or answer_result.get('confidence', 0) < 0.3:
                return []
            
            system_prompt = """Generate relevant follow-up questions that would help dive deeper 
            into the research topic based on the original question and answer provided."""
            
            prompt = f"""
            Original Question: {question}
            Answer Summary: {answer_result['answer'][:500]}...
            
            Generate 3-5 follow-up questions that would be relevant and interesting.
            Return as a JSON list: ["question1", "question2", "question3"]
            """
            
            response = self.llm.generate(prompt, system_prompt) if hasattr(self.llm, 'generate') else self.llm(prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
            if json_match:
                try:
                    questions = json.loads(json_match.group(0))
                    return [q.strip() for q in questions if isinstance(q, str)]
                except json.JSONDecodeError:
                    pass
            
            return []
            
        except Exception as e:
            logger.warning(f"Error generating follow-up questions: {e}")
            return []
    
    def _generate_no_results_response(self, question: str) -> Dict[str, Any]:
        """Generate response when no papers are found"""
        return {
            'question': question,
            'answer': f"""I couldn't find any relevant research papers for your question: "{question}"

This could be due to:
1. The topic might not be covered in the current database
2. Try rephrasing your question with different keywords
3. The research area might be very new or specialized

**Suggestions:**
- Try broader search terms
- Check if there are alternative names for the concepts
- Consider breaking down complex questions into simpler parts

Would you like to try rephrasing your question or search for a related topic?""",
            'confidence': 0.1,
            'question_type': 'no_results',
            'source_papers': [],
            'metadata': {
                'paper_count': 0,
                'error_type': 'no_papers_found',
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def _generate_low_relevance_response(self, question: str) -> Dict[str, Any]:
        """Generate response when papers have low relevance"""
        return {
            'question': question,
            'answer': f"""I found some papers but they don't seem highly relevant to your question: "{question}"

The available papers might touch on related topics but don't directly address your specific question.

**Suggestions:**
- Try using more specific technical terms
- Rephrase your question to focus on the core concept
- Consider searching for foundational concepts first

Would you like me to search for related topics or try a different approach?""",
            'confidence': 0.2,
            'question_type': 'low_relevance',
            'source_papers': [],
            'metadata': {
                'paper_count': 0,
                'error_type': 'low_relevance',
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate response when an error occurs"""
        return {
            'question': '',
            'answer': f"""I encountered an error while processing your question: {error_message}

Please try:
1. Rephrasing your question
2. Using simpler terms
3. Breaking complex questions into parts

If the problem persists, please contact support.""",
            'confidence': 0.0,
            'question_type': 'error',
            'source_papers': [],
            'metadata': {
                'error': error_message,
                'timestamp': datetime.now().isoformat()
            }
        }
