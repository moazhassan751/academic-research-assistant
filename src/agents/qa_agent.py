from crewai import Agent
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import re
from collections import defaultdict

from ..storage.models import Paper
from ..storage.database import db
from ..llm.llm_factory import LLMFactory
from ..utils.logging import logger


class QuestionAnsweringAgent:
    """Agent specialized in answering questions based on retrieved research papers"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the QA agent"""
        self.config = config or {}
        self.llm = LLMFactory.create_llm()
        
        # Configuration for QA
        self.max_papers_for_context = 10
        self.max_context_length = 8000  # Tokens
        self.min_relevance_score = 0.1  # Lowered from 0.3 to 0.1
        
        self.agent = Agent(
            role='Research Question Answering Specialist',
            goal='Answer complex research questions by analyzing and synthesizing information from academic papers',
            backstory="""You are an expert research analyst who specializes in understanding and 
            synthesizing complex academic literature. You excel at finding relevant information 
            across multiple papers and providing comprehensive, well-sourced answers to research questions.""",
            verbose=True,
            llm=self.llm.generate if hasattr(self.llm, 'generate') else self.llm
        )
    
    def answer_question(self, question: str, research_topic: str = None, 
                       paper_limit: int = 10) -> Dict[str, Any]:
        """
        Answer a research question based on retrieved papers
        
        Args:
            question: The research question to answer
            research_topic: Optional topic to filter papers
            paper_limit: Maximum number of papers to consider
            
        Returns:
            Dictionary containing the answer, sources, and confidence score
        """
        try:
            logger.info(f"Answering question: {question}")
            
            # Step 1: Retrieve relevant papers
            relevant_papers = self._retrieve_relevant_papers(
                question, research_topic, paper_limit
            )
            
            if not relevant_papers:
                return {
                    'answer': "I couldn't find any relevant papers to answer your question.",
                    'sources': [],
                    'confidence': 0.0,
                    'paper_count': 0
                }
            
            # Step 2: Rank papers by relevance to the question
            ranked_papers = self._rank_papers_by_relevance(question, relevant_papers)
            
            # Step 3: Extract relevant content from papers
            paper_contexts = self._extract_relevant_contexts(question, ranked_papers)
            
            # Step 4: Generate comprehensive answer
            answer_result = self._generate_answer(question, paper_contexts)
            
            # Step 5: Add metadata
            answer_result.update({
                'paper_count': len(relevant_papers),
                'top_papers_used': min(len(ranked_papers), self.max_papers_for_context),
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Successfully answered question using {answer_result['paper_count']} papers")
            return answer_result
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                'answer': f"An error occurred while processing your question: {str(e)}",
                'sources': [],
                'confidence': 0.0,
                'paper_count': 0
            }
    
    def _retrieve_relevant_papers(self, question: str, research_topic: str = None, 
                                 limit: int = 10) -> List[Paper]:
        """Retrieve papers relevant to the question"""
        try:
            # Extract key terms from the question
            key_terms = self._extract_key_terms(question)
            
            # Use the database search method
            relevant_papers = []
            
            # Search for papers using key terms
            for term in key_terms:
                papers = db.search_papers(term, limit=limit)
                relevant_papers.extend(papers)
            
            # If we have a research topic, also search for that
            if research_topic:
                topic_papers = db.search_papers(research_topic, limit=limit)
                relevant_papers.extend(topic_papers)
            
            # Remove duplicates based on title
            seen_titles = set()
            unique_papers = []
            for paper in relevant_papers:
                if paper.title and paper.title not in seen_titles:
                    seen_titles.add(paper.title)
                    unique_papers.append(paper)
            
            # Limit to requested number
            return unique_papers[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving relevant papers: {e}")
            return []
    
    def _extract_key_terms(self, question: str) -> List[str]:
        """Extract key terms from the research question"""
        try:
            # Use LLM to extract key terms
            system_prompt = """Extract the most important technical terms and concepts from the research question. 
            Focus on specific technologies, methodologies, and domain-specific terms."""
            
            prompt = f"""
            Question: {question}
            
            Extract 3-5 key terms that would be most useful for searching academic literature.
            Return as a JSON list: ["term1", "term2", "term3"]
            """
            
            response = self.llm.generate(prompt, system_prompt) if hasattr(self.llm, 'generate') else self.llm(prompt)
            
            # Try to extract JSON from response
            json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
            if json_match:
                try:
                    key_terms = json.loads(json_match.group(0))
                    return [term.strip().lower() for term in key_terms if isinstance(term, str)]
                except json.JSONDecodeError:
                    pass
            
            # Fallback: simple keyword extraction
            return self._simple_keyword_extraction(question)
            
        except Exception as e:
            logger.warning(f"Error extracting key terms: {e}")
            return self._simple_keyword_extraction(question)
    
    def _simple_keyword_extraction(self, question: str) -> List[str]:
        """Fallback method for keyword extraction"""
        # Remove common question words and extract meaningful terms
        stop_words = {
            'what', 'are', 'the', 'how', 'why', 'when', 'where', 'which', 'who',
            'is', 'in', 'on', 'at', 'for', 'with', 'by', 'from', 'about', 'into',
            'through', 'during', 'before', 'after', 'above', 'below', 'up', 'down',
            'out', 'off', 'over', 'under', 'again', 'further', 'then', 'once'
        }
        
        words = re.findall(r'\b[a-zA-Z]+\b', question.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Return top 5 most relevant terms
        return keywords[:5]
    
    def _rank_papers_by_relevance(self, question: str, papers: List[Paper]) -> List[Tuple[Paper, float]]:
        """Rank papers by relevance to the question"""
        try:
            scored_papers = []
            question_lower = question.lower()
            
            for paper in papers:
                score = 0.0
                
                # Title relevance (highest weight)
                if paper.title:
                    title_lower = paper.title.lower()
                    title_score = self._calculate_text_similarity(question_lower, title_lower)
                    score += title_score * 0.5
                
                # Abstract relevance
                if paper.abstract:
                    abstract_lower = paper.abstract.lower()
                    abstract_score = self._calculate_text_similarity(question_lower, abstract_lower)
                    score += abstract_score * 0.3
                
                # Keywords relevance
                if paper.keywords:
                    keywords_lower = paper.keywords.lower()
                    keywords_score = self._calculate_text_similarity(question_lower, keywords_lower)
                    score += keywords_score * 0.2
                
                # Citation bonus (indicates importance)
                if hasattr(paper, 'citations') and paper.citations:
                    citation_bonus = min(0.1, paper.citations / 1000)  # Max 0.1 bonus
                    score += citation_bonus
                
                scored_papers.append((paper, score))
            
            # Sort by score (highest first)
            scored_papers.sort(key=lambda x: x[1], reverse=True)
            
            # Filter out papers with very low relevance
            relevant_papers = [
                (paper, score) for paper, score in scored_papers 
                if score >= self.min_relevance_score
            ]
            
            logger.debug(f"Ranked {len(relevant_papers)} papers by relevance")
            return relevant_papers
            
        except Exception as e:
            logger.error(f"Error ranking papers: {e}")
            return [(paper, 0.5) for paper in papers]  # Default equal scoring
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity based on common words"""
        try:
            # Extract words and filter out short ones
            words1 = set([w.lower() for w in re.findall(r'\b\w+\b', text1.lower()) if len(w) > 2])
            words2 = set([w.lower() for w in re.findall(r'\b\w+\b', text2.lower()) if len(w) > 2])
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            
            # Use Jaccard similarity but with a minimum boost for any intersection
            if intersection:
                union = words1.union(words2)
                jaccard_sim = len(intersection) / len(union) if union else 0.0
                
                # Add a small boost for having any matching words
                boost = min(0.1, len(intersection) * 0.02)
                
                return min(1.0, jaccard_sim + boost)
            else:
                return 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating text similarity: {e}")
            return 0.0
    
    def _extract_relevant_contexts(self, question: str, ranked_papers: List[Tuple[Paper, float]]) -> List[Dict[str, Any]]:
        """Extract relevant context from papers"""
        contexts = []
        
        for paper, relevance_score in ranked_papers[:self.max_papers_for_context]:
            try:
                context = {
                    'paper': paper,
                    'relevance_score': relevance_score,
                    'title': paper.title or 'Unknown Title',
                    'authors': paper.authors or 'Unknown Authors',
                    'year': getattr(paper, 'publication_date', 'Unknown Year'),
                    'citations': getattr(paper, 'citations', 0),
                    'relevant_text': self._extract_most_relevant_text(question, paper)
                }
                contexts.append(context)
                
            except Exception as e:
                logger.warning(f"Error extracting context from paper: {e}")
                continue
        
        return contexts
    
    def _extract_most_relevant_text(self, question: str, paper: Paper) -> str:
        """Extract the most relevant text snippets from a paper"""
        try:
            # Combine available text sources
            text_sources = []
            
            if paper.title:
                text_sources.append(f"Title: {paper.title}")
            
            if paper.abstract:
                text_sources.append(f"Abstract: {paper.abstract}")
            
            if paper.keywords:
                text_sources.append(f"Keywords: {paper.keywords}")
            
            # For now, return the combined text
            # In a more advanced implementation, you could:
            # 1. Split text into sentences
            # 2. Rank sentences by relevance to the question
            # 3. Return top N sentences
            
            relevant_text = " | ".join(text_sources)
            
            # Truncate if too long
            max_length = 1000
            if len(relevant_text) > max_length:
                relevant_text = relevant_text[:max_length] + "..."
            
            return relevant_text
            
        except Exception as e:
            logger.warning(f"Error extracting relevant text: {e}")
            return f"Title: {paper.title or 'N/A'}"
    
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
