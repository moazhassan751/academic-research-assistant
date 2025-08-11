#!/usr/bin/env python3
"""
Debug script to check what papers are in the database
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.storage.database import db
from rich.console import Console
from rich.table import Table

def debug_database():
    console = Console()
    
    # Check some papers
    papers = db.search_papers("machine learning", limit=5)
    
    console.print(f"Found {len(papers)} papers for 'machine learning'")
    
    if papers:
        table = Table(title="Sample Papers")
        table.add_column("Title")
        table.add_column("Authors")
        table.add_column("Abstract (first 100 chars)")
        
        for paper in papers[:3]:
            title = paper.title[:50] + "..." if paper.title and len(paper.title) > 50 else str(paper.title or "N/A")
            authors = str(paper.authors)[:50] + "..." if paper.authors and len(str(paper.authors)) > 50 else str(paper.authors or "N/A")
            abstract = paper.abstract[:100] + "..." if paper.abstract and len(paper.abstract) > 100 else str(paper.abstract or "N/A")
            table.add_row(title, authors, abstract)
        
        console.print(table)
        
        # Check attributes of first paper
        if papers:
            paper = papers[0]
            console.print(f"\nFirst paper attributes:")
            console.print(f"Title: {paper.title}")
            console.print(f"Authors: {paper.authors}")
            console.print(f"Abstract length: {len(paper.abstract) if paper.abstract else 0}")
            console.print(f"Keywords: {paper.keywords}")
            console.print(f"Has citations attr: {hasattr(paper, 'citations')}")
            if hasattr(paper, 'citations'):
                console.print(f"Citations: {paper.citations}")
    
    # Test the QA agent directly
    console.print("\n" + "="*50)
    console.print("Testing QA Agent directly...")
    
    from src.agents.qa_agent import QuestionAnsweringAgent
    
    qa_agent = QuestionAnsweringAgent()
    
    # Test key term extraction
    question = "What are the recent trends in machine learning?"
    key_terms = qa_agent._extract_key_terms(question)
    console.print(f"Key terms extracted: {key_terms}")
    
    # Test paper retrieval
    relevant_papers = qa_agent._retrieve_relevant_papers(question, limit=5)
    console.print(f"Retrieved {len(relevant_papers)} relevant papers")
    
    if relevant_papers:
        # Test ranking
        ranked_papers = qa_agent._rank_papers_by_relevance(question, relevant_papers)
        console.print(f"Ranked {len(ranked_papers)} papers")
        
        if ranked_papers:
            for i, (paper, score) in enumerate(ranked_papers[:3]):
                console.print(f"Paper {i+1}: Score {score:.3f} - {paper.title[:60]}...")
        else:
            console.print("No papers passed the relevance threshold")
            
            # Let's debug the scoring directly
            console.print("\nTesting ranking without threshold...")
            scored_papers = []
            question_lower = question.lower()
            
            for paper in relevant_papers:
                score = 0.0
                
                # Title relevance
                if paper.title:
                    title_lower = paper.title.lower()
                    title_score = qa_agent._calculate_text_similarity(question_lower, title_lower)
                    score += title_score * 0.5
                    console.print(f"Title score for '{paper.title[:40]}...': {title_score:.3f}")
                
                # Abstract relevance
                if paper.abstract:
                    abstract_lower = paper.abstract.lower()
                    abstract_score = qa_agent._calculate_text_similarity(question_lower, abstract_lower)
                    score += abstract_score * 0.3
                    console.print(f"Abstract score: {abstract_score:.3f}")
                
                console.print(f"Total score: {score:.3f}, Threshold: {qa_agent.min_relevance_score}")
                scored_papers.append((paper, score))
            
            # Show all scores
            scored_papers.sort(key=lambda x: x[1], reverse=True)
            console.print("\nAll papers with scores:")
            for i, (paper, score) in enumerate(scored_papers[:5]):
                console.print(f"{i+1}. Score: {score:.3f} - {paper.title[:50]}...")

if __name__ == "__main__":
    debug_database()
