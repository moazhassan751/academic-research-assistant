"""
Simplified QA Agent - bypasses complex async operations that cause hanging
"""
import time
from typing import Dict, List, Any, Optional
from ..storage.database import db
from ..utils.config import config
from ..llm.gemini_client import GeminiClient
from ..utils.app_logging import logger

class SimplifiedQAAgent:
    """Simplified QA Agent without complex async operations"""
    
    def __init__(self):
        """Initialize simplified QA agent"""
        try:
            llm_config = config.llm_config
            self.llm = GeminiClient(
                api_key=llm_config.get('api_key'),
                model=llm_config.get('model', 'gemini-2.5-flash')
            )
            logger.info("Simplified QA Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize simplified QA agent: {e}")
            raise
    
    def answer_question(self, question: str, research_topic: str = None, 
                       paper_limit: int = 10) -> Dict[str, Any]:
        """Answer a question using simplified synchronous processing"""
        start_time = time.time()
        
        try:
            logger.info(f"Simplified QA processing: {question[:50]}...")
            
            # Get relevant papers from database (simplified)
            papers = self._get_relevant_papers(research_topic, paper_limit)
            
            if not papers:
                return {
                    'answer': "I don't have enough relevant papers in the database to answer this question. Please try conducting research on this topic first using the 'research' command.",
                    'confidence': 0.0,
                    'paper_count': 0,
                    'sources': [],
                    'execution_time': f"{time.time() - start_time:.2f} seconds",
                    'follow_up_questions': []
                }
            
            # Create context from papers (simplified)
            context = self._create_context_from_papers(papers)
            
            # Generate answer using LLM
            answer = self._generate_answer(question, context)
            
            # Calculate confidence (simplified)
            confidence = min(0.8, 0.3 + (len(papers) * 0.05))
            
            execution_time = time.time() - start_time
            
            result = {
                'answer': answer,
                'confidence': confidence,
                'paper_count': len(papers),
                'sources': [self._paper_to_source_dict(p) for p in papers[:5]],
                'execution_time': f"{execution_time:.2f} seconds",
                'follow_up_questions': self._generate_simple_followups(question)
            }
            
            logger.info(f"Simplified QA completed in {execution_time:.2f}s with confidence {confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error in simplified QA: {e}")
            return {
                'answer': f"An error occurred while processing your question: {str(e)}",
                'confidence': 0.0,
                'paper_count': 0,
                'sources': [],
                'error': str(e),
                'execution_time': f"{time.time() - start_time:.2f} seconds",
                'follow_up_questions': []
            }
    
    def _get_relevant_papers(self, research_topic: str = None, limit: int = 10) -> List:
        """Get relevant papers from database (simplified search)"""
        try:
            if research_topic:
                # Search by topic
                papers = db.search_papers(research_topic, limit=limit)
            else:
                # Get recent papers
                papers = db.get_recent_papers(limit=limit)
            
            return papers
            
        except Exception as e:
            logger.error(f"Error retrieving papers: {e}")
            return []
    
    def _create_context_from_papers(self, papers: List) -> str:
        """Create context string from papers (simplified)"""
        context = ""
        for i, paper in enumerate(papers[:6], 1):  # Limit to 6 papers to avoid token limits
            title = getattr(paper, 'title', 'No title') or 'No title'
            abstract = getattr(paper, 'abstract', 'No abstract') or 'No abstract'
            authors = getattr(paper, 'authors', 'Unknown authors') or 'Unknown authors'
            year = getattr(paper, 'year', 'Unknown year') or 'Unknown year'
            
            # Truncate abstract if too long
            if len(abstract) > 250:
                abstract = abstract[:250] + "..."
            
            context += f"\n[Paper {i}]\nTitle: {title}\nAuthors: {authors}\nYear: {year}\nAbstract: {abstract}\n"
        
        return context
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using LLM (simplified prompt)"""
        prompt = f"""Based on the following research papers, please answer this question: {question}

Research Papers Context:
{context}

Instructions:
- Provide a comprehensive answer based on the available research papers
- Cite specific papers when making claims (e.g., "According to Paper 1...")  
- If the papers don't contain enough information, acknowledge this limitation
- Focus on factual information from the research
- Be concise but informative

Answer:"""
        
        try:
            answer = self.llm.generate(prompt)
            return answer
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"I encountered an error while generating the answer: {str(e)}"
    
    def _paper_to_source_dict(self, paper) -> Dict[str, Any]:
        """Convert paper object to source dictionary (simplified)"""
        # Safely get authors and handle different types
        authors = getattr(paper, 'authors', 'Unknown') or 'Unknown'
        if isinstance(authors, list):
            authors = ', '.join(str(a) for a in authors if a) if authors else 'Unknown'
        authors = str(authors)
        
        return {
            'title': str(getattr(paper, 'title', 'Unknown') or 'Unknown'),
            'authors': authors,
            'year': str(getattr(paper, 'year', 'N/A') or 'N/A'),
            'citations': int(getattr(paper, 'citations', 0) or 0),
            'relevance_score': 0.7  # Simplified scoring
        }
    
    def _generate_simple_followups(self, question: str) -> List[str]:
        """Generate simple follow-up questions"""
        topic = question.lower().replace('what is', '').replace('what are', '').replace('?', '').strip()
        followups = [
            f"What are the main challenges or limitations in {topic}?",
            f"What are recent advances or trends in {topic}?",
            f"What are the practical applications of {topic}?"
        ]
        return followups[:2]  # Return max 2 followups
