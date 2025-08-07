from crewai import Agent, Task
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..tools.arxiv_tool import ArxivTool
from ..tools.Open_Alex_tool import OpenAlexTool
from ..tools.Cross_Ref_tool import CrossRefTool
from ..storage.models import Paper
from ..storage.database import db
from ..llm.llm_factory import LLMFactory
from ..utils.logging import logger

class LiteratureSurveyAgent:
    def __init__(self):
        self.llm = LLMFactory.create_llm()
        self.arxiv_tool = ArxivTool()
        self.openalex_tool = OpenAlexTool(mailto="rmoazhassan555@gmail.com")
        self.crossref_tool = CrossRefTool()
        
        self.agent = Agent(
            role='Literature Survey Specialist',
            goal='Search, filter, and collect relevant academic papers from multiple databases',
            backstory="""You are an expert research librarian with deep knowledge of 
            academic databases and search strategies. You excel at finding the most 
            relevant papers for any research topic and can identify key works that 
            others might miss.""",
            verbose=True,
            llm=self.llm.generate
        )
    
    def create_search_strategy(self, research_topic: str, 
                             specific_aspects: List[str] = None) -> Dict[str, List[str]]:
        """Create comprehensive search strategy"""
        system_prompt = """You are an expert at creating academic search strategies. 
        Generate search queries that will comprehensively cover the research topic."""
        
        prompt = f"""
        Research Topic: {research_topic}
        Specific Aspects: {specific_aspects or []}
        
        Create a comprehensive search strategy with:
        1. Primary search queries (3-5 main queries)
        2. Alternative keyword variations
        3. Specific technical terms to include
        4. Boolean search combinations
        
        Format as JSON with keys: primary_queries, alternative_keywords, technical_terms, boolean_combinations
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt)
            # Parse response and create search strategy
            # For now, return a basic strategy
            return {
                'primary_queries': [research_topic],
                'alternative_keywords': [],
                'technical_terms': [],
                'boolean_combinations': []
            }
        except Exception as e:
            logger.error(f"Error creating search strategy: {e}")
            return {'primary_queries': [research_topic]}
    
    def search_multiple_databases(self, queries: List[str], 
                                 max_results_per_query: int = 50,
                                 date_from: Optional[datetime] = None) -> List[Paper]:
        """Search multiple databases with given queries"""
        all_papers = []
        
        for query in queries:
            logger.info(f"Searching for: {query}")
            
            # Search ArXiv
            try:
                arxiv_papers = self.arxiv_tool.search_papers(
                    query, max_results_per_query, date_from
                )
                all_papers.extend(arxiv_papers)
                logger.info(f"ArXiv returned {len(arxiv_papers)} papers for '{query}'")
            except Exception as e:
                logger.error(f"ArXiv search failed for '{query}': {e}")
            
            # Search OpenAlex
            try:
                openalex_papers = self.openalex_tool.search_papers(
                    query, max_results_per_query, date_from
                )
                all_papers.extend(openalex_papers)
                logger.info(f"OpenAlex returned {len(openalex_papers)} papers for '{query}'")
            except Exception as e:
                logger.error(f"OpenAlex search failed for '{query}': {e}")
            
            # Search CrossRef
            try:
                crossref_papers = self.crossref_tool.search_papers(
                    query, max_results_per_query, date_from
                )
                all_papers.extend(crossref_papers)
                logger.info(f"CrossRef returned {len(crossref_papers)} papers for '{query}'")
            except Exception as e:
                logger.error(f"CrossRef search failed for '{query}': {e}")
        
        # Remove duplicates based on title similarity and DOI
        unique_papers = self.deduplicate_papers(all_papers)
        
        # Save papers to database
        for paper in unique_papers:
            try:
                db.save_paper(paper)
            except Exception as e:
                logger.error(f"Error saving paper to database: {e}")
        
        return unique_papers
    
    def deduplicate_papers(self, papers: List[Paper]) -> List[Paper]:
        """Remove duplicate papers based on title similarity and DOI"""
        unique_papers = []
        seen_titles = set()
        seen_dois = set()
        
        for paper in papers:
            # Check for DOI duplicates first (most reliable)
            if paper.doi and paper.doi in seen_dois:
                continue
                
            # Check for title duplicates
            title_clean = paper.title.lower().strip().replace(' ', '').replace('-', '')
            if title_clean in seen_titles:
                continue
            
            # Add to unique papers
            unique_papers.append(paper)
            seen_titles.add(title_clean)
            if paper.doi:
                seen_dois.add(paper.doi)
        
        logger.info(f"Removed {len(papers) - len(unique_papers)} duplicates")
        return unique_papers
    
    def filter_and_rank_papers(self, papers: List[Paper], 
                              research_topic: str) -> List[Paper]:
        """Filter and rank papers by relevance"""
        system_prompt = """You are an expert at evaluating academic paper relevance. 
        Score papers from 0-10 based on their relevance to the research topic."""
        
        scored_papers = []
        
        for paper in papers[:20]:  # Limit to prevent API overuse
            prompt = f"""
            Research Topic: {research_topic}
            
            Paper Title: {paper.title}
            Abstract: {paper.abstract[:500]}...
            Authors: {', '.join(paper.authors[:3]) if paper.authors else 'Unknown'}
            Venue: {paper.venue or 'Unknown'}
            Citations: {paper.citations}
            
            Score this paper's relevance from 0-10 and provide a brief justification.
            Format: SCORE: X, JUSTIFICATION: brief explanation
            """
            
            try:
                response = self.llm.generate(prompt, system_prompt)
                score = self.extract_score(response)
                scored_papers.append((paper, score))
            except Exception as e:
                logger.error(f"Error scoring paper: {e}")
                scored_papers.append((paper, 5))  # Default score
        
        # Add remaining papers with default score
        for paper in papers[20:]:
            scored_papers.append((paper, 5))
        
        # Sort by score and return papers
        scored_papers.sort(key=lambda x: x[1], reverse=True)
        return [paper for paper, score in scored_papers if score >= 6]
    
    def extract_score(self, response: str) -> float:
        """Extract score from LLM response"""
        try:
            if "SCORE:" in response:
                score_part = response.split("SCORE:")[1].split(",")[0].strip()
                return float(score_part)
        except:
            pass
        return 5.0  # Default score
    
    def conduct_literature_survey(self, research_topic: str,
                                 specific_aspects: List[str] = None,
                                 max_papers: int = 100,
                                 date_from: Optional[datetime] = None) -> List[Paper]:
        """Main method to conduct comprehensive literature survey"""
        logger.info(f"Starting literature survey for: {research_topic}")
        
        # Create search strategy
        strategy = self.create_search_strategy(research_topic, specific_aspects)
        
        # Search multiple databases
        papers = self.search_multiple_databases(
            strategy['primary_queries'], 
            max_papers // len(strategy['primary_queries']),
            date_from
        )
        
        # Filter and rank papers
        relevant_papers = self.filter_and_rank_papers(papers, research_topic)
        
        logger.info(f"Literature survey completed: {len(relevant_papers)} relevant papers found")
        return relevant_papers