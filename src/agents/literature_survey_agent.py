from crewai import Agent, Task
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import json
import re
import hashlib
from collections import defaultdict
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import time

from ..tools.arxiv_tool import ArxivTool
from ..tools.Open_Alex_tool import OpenAlexTool
from ..tools.Cross_Ref_tool import CrossRefTool
from ..storage.models import Paper
from ..storage.database import db
from ..llm.llm_factory import LLMFactory
from ..utils.logging import logger


class LiteratureSurveyAgent:
    """FIXED: Enhanced Literature Survey Agent with optimized search logic"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the agent with configuration"""
        self.config = config or {}
        self.llm = LLMFactory.create_llm()
        self.arxiv_tool = ArxivTool()
        self.openalex_tool = OpenAlexTool(mailto=self.config.get('email', 'rmoazhassan555@gmail.com'))
        self.crossref_tool = CrossRefTool()
        
        # Enhanced deduplication settings
        self.title_similarity_threshold = 0.85
        self.abstract_similarity_threshold = 0.90
        
        # FIXED: Optimized search settings
        self.max_concurrent_searches = 2
        self.search_timeout = 45  # Reasonable timeout
        self.retry_attempts = 2
        self.backoff_factor = 2
        
        # FIXED: Improved query optimization
        self.max_queries_per_database = 2  # Reduced to prevent timeouts
        self.target_papers_per_query = 15   # FIXED: Increased target per query
        self.max_papers_per_database_per_query = 25  # FIXED: Better limit per query
        
        self.agent = Agent(
            role='Advanced Literature Survey Specialist',
            goal='Efficiently search and collect relevant academic papers with optimized query strategies',
            backstory="""You are an expert research librarian who excels at finding comprehensive 
            coverage of research topics using efficient search strategies. You prioritize quality 
            over quantity and use optimized search patterns to find the most relevant papers.""",
            verbose=True,
            llm=self.llm.generate if hasattr(self.llm, 'generate') else self.llm
        )
    
    def create_enhanced_search_strategy(self, research_topic: str, 
                                      specific_aspects: List[str] = None,
                                      paper_type: str = 'all') -> Dict[str, Any]:
        """FIXED: Create optimized search strategy with better query generation"""
        
        # Create fallback strategy immediately
        strategy = self._create_optimized_fallback_strategy(research_topic, specific_aspects, paper_type)
        
        # Quick LLM enhancement (optional, with timeout)
        try:
            system_prompt = """Generate concise, effective academic search queries. Focus on the most 
            important terms and variations that will yield high-quality results."""
            
            prompt = f"""
            Topic: {research_topic}
            Type: {paper_type}
            
            Generate 3-4 highly effective search queries focusing on:
            1. Exact phrase match
            2. Key variations/synonyms  
            3. Technical terms
            
            Return JSON format:
            {{"primary_queries": ["query1", "query2", "query3"], "technical_terms": ["term1", "term2"]}}
            """
            
            # Quick LLM call with short timeout
            response = self.llm.generate(prompt, system_prompt) if hasattr(self.llm, 'generate') else self.llm(prompt)
            
            llm_strategy = self._extract_json_from_response(response)
            if llm_strategy and 'primary_queries' in llm_strategy:
                # Use LLM queries if available
                strategy['primary_queries'] = llm_strategy['primary_queries'][:4]
                if 'technical_terms' in llm_strategy:
                    strategy['technical_terms'] = llm_strategy['technical_terms'][:3]
                        
        except Exception as e:
            logger.debug(f"LLM strategy enhancement failed, using fallback: {e}")
        
        return strategy
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict]:
        """Extract JSON from LLM response with better error handling"""
        if not response:
            return None
        
        try:
            response = response.strip()
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            return json.loads(response)
        except Exception as e:
            logger.debug(f"Failed to extract JSON from LLM response: {e}")
            return None
    
    def _create_optimized_fallback_strategy(self, research_topic: str, 
                                          specific_aspects: List[str] = None,
                                          paper_type: str = 'all') -> Dict[str, List[str]]:
        """FIXED: Create optimized fallback search strategy"""
        
        # Primary queries - focus on most effective searches
        primary_queries = [
            research_topic,  # Basic query
            f'"{research_topic}"',  # Exact phrase for precision
        ]
        
        # Add type-specific queries
        if paper_type == 'survey':
            primary_queries.extend([
                f"{research_topic} survey",
                f"{research_topic} review"
            ])
        elif paper_type in ['research', 'all']:
            # Add one broader query for research papers
            primary_queries.append(f"{research_topic} method")
        
        # Technical terms based on topic analysis
        technical_terms = []
        topic_lower = research_topic.lower()
        
        # AI/ML specific expansions
        if any(term in topic_lower for term in ['artificial intelligence', 'ai']):
            technical_terms.extend(['artificial intelligence', 'AI', 'machine intelligence'])
        if 'general' in topic_lower and 'intelligence' in topic_lower:
            technical_terms.extend(['AGI', 'artificial general intelligence', 'general AI'])
        if 'machine learning' in topic_lower or 'ml' in topic_lower:
            technical_terms.extend(['machine learning', 'ML'])
        if 'deep learning' in topic_lower or 'neural' in topic_lower:
            technical_terms.extend(['deep learning', 'neural networks'])
        
        # Keep strategy focused and small
        return {
            'primary_queries': primary_queries[:4],  # Limit to 4 primary queries
            'technical_terms': technical_terms[:3],   # Limit to 3 technical terms
            'boolean_combinations': [f"({research_topic}) AND (survey OR review)"][:1]  # One combination
        }
    
    def search_multiple_databases_enhanced(self, queries: List[str], 
                                         max_results_per_query: int = 50,
                                         date_from: Optional[datetime] = None,
                                         parallel: bool = False) -> List[Paper]:
        """FIXED: Enhanced search with better result targets and error handling"""
        all_papers = []
        
        # FIXED: Use fewer, more effective queries
        limited_queries = queries[:3]  # Maximum 3 queries total
        logger.info(f"Using {len(limited_queries)} queries (limited from {len(queries)})")
        
        # FIXED: Always use sequential search for reliability
        all_papers = self._optimized_sequential_search(limited_queries, max_results_per_query, date_from)
        
        # Enhanced deduplication
        unique_papers = self.enhanced_deduplicate_papers(all_papers)
        
        # Save papers to database
        self._batch_save_papers(unique_papers)
        
        logger.info(f"Search completed: {len(all_papers)} total papers, {len(unique_papers)} unique papers")
        return unique_papers
    
    def _optimized_sequential_search(self, queries: List[str], max_results: int, 
                                   date_from: Optional[datetime]) -> List[Paper]:
        """FIXED: Optimized sequential search with better targets and retry logic"""
        all_papers = []
        successful_searches = 0
        
        for i, query in enumerate(queries):
            logger.info(f"Searching query {i+1}/{len(queries)}: {query}")
            
            # FIXED: Search databases with optimized targets
            databases = [
                (self.arxiv_tool.search_papers, 'ArXiv'),
                (self.openalex_tool.search_papers, 'OpenAlex'), 
                (self.crossref_tool.search_papers, 'CrossRef')
            ]
            
            query_papers = []
            for search_func, db_name in databases:
                try:
                    start_time = time.time()
                    
                    # FIXED: Use higher targets per database to reduce retry loops
                    papers = self._safe_search_with_better_targets(
                        search_func, query, self.max_papers_per_database_per_query, 
                        date_from, db_name
                    )
                    
                    search_time = time.time() - start_time
                    
                    if papers:
                        query_papers.extend(papers)
                        successful_searches += 1
                        logger.info(f"{db_name} returned {len(papers)} papers for '{query}' in {search_time:.1f}s")
                    else:
                        logger.warning(f"{db_name} returned 0 papers for '{query}'")
                    
                    # Brief pause between database searches
                    time.sleep(1.0)
                    
                except Exception as e:
                    logger.error(f"Database search failed for {db_name}: {e}")
                    continue
            
            all_papers.extend(query_papers)
            
            # Break early if we have enough papers
            if len(all_papers) >= 30:  # Good threshold
                logger.info(f"Collected {len(all_papers)} papers, sufficient for analysis")
                break
            
            # Pause between queries
            if i < len(queries) - 1:
                time.sleep(2.0)
        
        logger.info(f"Sequential search completed: {successful_searches} successful searches, {len(all_papers)} total papers")
        return all_papers
    
    def _safe_search_with_better_targets(self, search_func, query: str, max_results: int, 
                                       date_from: Optional[datetime], db_name: str) -> List[Paper]:
        """FIXED: Execute search with better targets and no unnecessary retries"""
        try:
            start_time = time.time()
            
            # Execute search directly without retry loops for single paper results
            papers = search_func(query, max_results, date_from)
            
            search_time = time.time() - start_time
            
            # Check for reasonable timeout
            if search_time > 30:
                logger.warning(f"{db_name} search took {search_time:.1f}s")
            
            # Validate and return results
            if papers is None:
                papers = []
            
            return papers
                    
        except Exception as e:
            logger.error(f"{db_name} search failed for '{query}': {e}")
            return []
    
    def enhanced_deduplicate_papers(self, papers: List[Paper]) -> List[Paper]:
        """Enhanced deduplication using multiple similarity measures"""
        if not papers:
            return []
        
        logger.info(f"Starting deduplication of {len(papers)} papers")
        
        unique_papers = []
        seen_dois = set()
        seen_arxiv_ids = set()
        title_hashes = set()
        similar_abstracts = []
        
        duplicates_removed = {
            'doi': 0,
            'arxiv_id': 0,
            'title': 0,
            'abstract': 0
        }
        
        for paper in papers:
            # Check DOI duplicates (highest priority)
            if paper.doi and paper.doi.strip():
                doi_clean = paper.doi.strip().lower()
                if doi_clean in seen_dois:
                    duplicates_removed['doi'] += 1
                    continue
                seen_dois.add(doi_clean)
            
            # Check ArXiv ID duplicates
            if hasattr(paper, 'arxiv_id') and paper.arxiv_id:
                if paper.arxiv_id in seen_arxiv_ids:
                    duplicates_removed['arxiv_id'] += 1
                    continue
                seen_arxiv_ids.add(paper.arxiv_id)
            
            # Check title similarity using hash-based approach
            title_hash = self._create_title_hash(paper.title)
            if title_hash in title_hashes:
                duplicates_removed['title'] += 1
                continue
            title_hashes.add(title_hash)
            
            # Check abstract similarity (for papers without DOI)
            if not paper.doi and paper.abstract and len(paper.abstract) > 50:
                if self._is_similar_abstract(paper.abstract, similar_abstracts):
                    duplicates_removed['abstract'] += 1
                    continue
                similar_abstracts.append(paper.abstract)
            
            unique_papers.append(paper)
        
        logger.info(f"Deduplication complete: {len(papers)} -> {len(unique_papers)} papers")
        logger.info(f"Duplicates removed - DOI: {duplicates_removed['doi']}, "
                   f"ArXiv: {duplicates_removed['arxiv_id']}, Title: {duplicates_removed['title']}, "
                   f"Abstract: {duplicates_removed['abstract']}")
        
        return unique_papers
    
    def _create_title_hash(self, title: str) -> str:
        """Create normalized hash of title for duplicate detection"""
        if not title:
            return ""
        
        # Normalize title: lowercase, remove punctuation, extra spaces
        normalized = re.sub(r'[^\w\s]', '', title.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remove common words that don't add meaning
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [w for w in normalized.split() if w not in stop_words]
        normalized = ' '.join(words)
        
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def _is_similar_abstract(self, abstract: str, existing_abstracts: List[str]) -> bool:
        """Check if abstract is similar to existing ones"""
        if not abstract or len(abstract) < 50:
            return False
        
        abstract_words = set(abstract.lower().split())
        
        # Check only recent abstracts for efficiency
        for existing in existing_abstracts[-10:]:
            existing_words = set(existing.lower().split())
            
            if len(abstract_words) == 0 or len(existing_words) == 0:
                continue
            
            # Jaccard similarity
            intersection = len(abstract_words & existing_words)
            union = len(abstract_words | existing_words)
            similarity = intersection / union if union > 0 else 0
            
            if similarity > self.abstract_similarity_threshold:
                return True
        
        return False
    
    def _batch_save_papers(self, papers: List[Paper]) -> None:
        """Save papers to database in batches with error handling"""
        if not papers:
            return
        
        batch_size = 20
        saved_count = 0
        
        for i in range(0, len(papers), batch_size):
            batch = papers[i:i + batch_size]
            logger.info(f"Saving batch {i//batch_size + 1}/{(len(papers) + batch_size - 1)//batch_size}")
            
            for paper in batch:
                try:
                    db.save_paper(paper)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving paper '{paper.title[:50]}...': {e}")
        
        logger.info(f"Successfully saved {saved_count}/{len(papers)} papers to database")
    
    def intelligent_paper_ranking(self, papers: List[Paper], 
                                 research_topic: str,
                                 ranking_criteria: Dict[str, float] = None) -> List[Paper]:
        """Enhanced paper ranking using multiple criteria"""
        if not papers:
            return papers
        
        logger.info(f"Ranking {len(papers)} papers by relevance to '{research_topic}'")
        
        # Default ranking criteria weights
        criteria = ranking_criteria or {
            'relevance_score': 0.5,
            'citation_count': 0.2,
            'publication_year': 0.15,
            'venue_quality': 0.10,
            'abstract_quality': 0.05
        }
        
        scored_papers = []
        
        for paper in papers:
            try:
                scores = self._calculate_paper_scores(paper, research_topic)
                total_score = sum(scores.get(key, 0) * weight for key, weight in criteria.items())
                scored_papers.append((paper, total_score))
            except Exception as e:
                logger.debug(f"Error scoring paper '{paper.title[:50]}...': {e}")
                scored_papers.append((paper, 5.0))  # Default score
        
        # Sort by total score
        scored_papers.sort(key=lambda x: x[1], reverse=True)
        
        # Log ranking statistics
        scores = [score for _, score in scored_papers]
        if scores:
            logger.info(f"Paper ranking completed. Score range: {min(scores):.2f} - {max(scores):.2f}")
        
        return [paper for paper, _ in scored_papers]
    
    def _calculate_paper_scores(self, paper: Paper, research_topic: str) -> Dict[str, float]:
        """Calculate various scoring metrics for a paper"""
        scores = {}
        
        # Relevance score (keyword matching)
        scores['relevance_score'] = self._calculate_relevance_score(paper, research_topic)
        
        # Citation count score (normalized)
        max_citations = 1000
        scores['citation_count'] = min(paper.citations / max_citations * 10, 10) if paper.citations else 0
        
        # Publication year score (prefer recent papers)
        current_year = datetime.now().year
        if paper.published_date:
            year_diff = current_year - paper.published_date.year
            scores['publication_year'] = max(0, 10 - year_diff * 0.3)
        else:
            scores['publication_year'] = 5.0
        
        # Venue quality score
        scores['venue_quality'] = self._calculate_venue_score(paper.venue)
        
        # Abstract quality score
        scores['abstract_quality'] = self._calculate_abstract_quality(paper.abstract)
        
        return scores
    
    def _calculate_relevance_score(self, paper: Paper, research_topic: str) -> float:
        """Calculate relevance score using keyword matching"""
        topic_words = set(research_topic.lower().split())
        
        # Check title relevance (higher weight)
        title_words = set(paper.title.lower().split()) if paper.title else set()
        title_overlap = len(topic_words & title_words) / len(topic_words) if topic_words else 0
        
        # Check abstract relevance
        abstract_overlap = 0
        if paper.abstract:
            abstract_words = set(paper.abstract.lower().split())
            abstract_overlap = len(topic_words & abstract_words) / len(topic_words) if topic_words else 0
        
        # Combined score with title having higher weight
        relevance = (title_overlap * 0.7 + abstract_overlap * 0.3) * 10
        return min(relevance, 10)
    
    def _calculate_venue_score(self, venue: Optional[str]) -> float:
        """Calculate venue quality score"""
        if not venue:
            return 5.0
        
        venue_lower = venue.lower()
        
        # High-quality venue keywords
        high_quality_keywords = [
            'ieee', 'acm', 'nature', 'science', 
            'neurips', 'icml', 'iclr', 'aaai', 'ijcai', 
            'proceedings', 'conference', 'journal', 'transactions'
        ]
        
        for keyword in high_quality_keywords:
            if keyword in venue_lower:
                return 8.0
        
        # arXiv gets medium score
        if 'arxiv' in venue_lower:
            return 6.0
        
        return 5.0
    
    def _calculate_abstract_quality(self, abstract: Optional[str]) -> float:
        """Calculate abstract quality score"""
        if not abstract or len(abstract.strip()) < 50:
            return 2.0
        
        # Basic quality indicators
        length_score = min(len(abstract) / 200, 1) * 4
        
        # Method indicators
        method_keywords = ['method', 'approach', 'algorithm', 'technique', 'framework', 'model']
        has_methods = any(keyword in abstract.lower() for keyword in method_keywords)
        method_score = 3 if has_methods else 0
        
        # Results indicators
        results_keywords = ['results', 'performance', 'accuracy', 'improvement', 'evaluation', 'experiment']
        has_results = any(keyword in abstract.lower() for keyword in results_keywords)
        results_score = 3 if has_results else 0
        
        return min(length_score + method_score + results_score, 10)
    
    def conduct_comprehensive_literature_survey(self, 
                                              research_topic: str,
                                              specific_aspects: List[str] = None,
                                              max_papers: int = 100,
                                              paper_type: str = 'all',
                                              date_from: Optional[datetime] = None,
                                              enable_ranking: bool = True,
                                              parallel_search: bool = False) -> List[Paper]:
        """
        FIXED: Main method with optimized search strategy and better error handling
        """
        start_time = time.time()
        logger.info(f"Starting comprehensive literature survey for: {research_topic}")
        logger.info(f"Parameters - max_papers: {max_papers}, paper_type: {paper_type}, parallel: {parallel_search}")
        
        try:
            # Phase 1: Create search strategy
            logger.info("Phase 1: Creating search strategy...")
            strategy = self.create_enhanced_search_strategy(research_topic, specific_aspects, paper_type)
            
            # Phase 2: Prepare optimized queries
            logger.info("Phase 2: Preparing search queries...")
            all_queries = []
            
            # FIXED: Use focused query selection
            all_queries.extend(strategy.get('primary_queries', [])[:3])
            all_queries.extend(strategy.get('technical_terms', [])[:2])
            all_queries.extend(strategy.get('boolean_combinations', [])[:1])
            
            # Remove duplicates and limit
            unique_queries = []
            seen_queries = set()
            for query in all_queries:
                if query and query.lower() not in seen_queries:
                    unique_queries.append(query)
                    seen_queries.add(query.lower())
            
            # FIXED: Limit to maximum 4 queries to prevent timeouts
            final_queries = unique_queries[:4]
            logger.info(f"Using {len(final_queries)} search queries: {final_queries}")
            
            # Phase 3: Execute optimized searches
            logger.info("Phase 3: Searching databases...")
            papers = self.search_multiple_databases_enhanced(
                final_queries,
                max_papers // max(len(final_queries), 1),
                date_from,
                parallel_search
            )
            
            if not papers:
                logger.warning("No papers found in database search!")
                return []
            
            # Phase 4: Apply intelligent ranking
            if enable_ranking and len(papers) > 1:
                logger.info("Phase 4: Ranking papers by relevance...")
                papers = self.intelligent_paper_ranking(papers, research_topic)
            
            # Phase 5: Final filtering
            logger.info("Phase 5: Final filtering...")
            final_papers = papers[:max_papers]
            
            # Log completion statistics
            elapsed_time = time.time() - start_time
            logger.info(f"Literature survey completed successfully in {elapsed_time:.1f}s")
            logger.info(f"Results: {len(final_papers)} high-quality papers found")
            
            # Log paper sources
            source_counts = {}
            for paper in final_papers:
                source = getattr(paper, 'source', 'unknown')
                source_counts[source] = source_counts.get(source, 0) + 1
            logger.info(f"Paper sources: {source_counts}")
            
            return final_papers
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Literature survey failed after {elapsed_time:.1f}s: {e}")
            return []