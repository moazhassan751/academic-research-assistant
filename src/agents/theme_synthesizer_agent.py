from crewai import Agent
from typing import List, Dict, Any
from collections import Counter
from uuid import uuid4
from ..storage.models import ResearchNote, ResearchTheme
from ..storage.database import db
from ..llm.llm_factory import LLMFactory
from ..utils.logging import logger

class ThemeSynthesizerAgent:
    def __init__(self):
        self.llm = LLMFactory.create_llm()
        
        self.agent = Agent(
            role='Research Theme Synthesis Expert',
            goal='Identify patterns, trends, and synthesize themes from research notes',
            backstory="""You are a brilliant research analyst who can see the big 
            picture. You excel at identifying patterns across multiple papers, 
            synthesizing common themes, and spotting research gaps that others miss.""",
            verbose=True,
            llm=self.llm.generate
        )
    
    def cluster_notes_by_similarity(self, notes: List[ResearchNote]) -> Dict[str, List[ResearchNote]]:
        """Cluster notes by content similarity"""
        # Simple keyword-based clustering for now
        clusters = {}
        
        for note in notes:
            # Extract keywords from note content
            keywords = self.extract_keywords(note.content)
            
            # Find best matching cluster
            best_cluster = None
            max_similarity = 0
            
            for cluster_name, cluster_notes in clusters.items():
                similarity = self.calculate_similarity(keywords, cluster_name)
                if similarity > max_similarity and similarity > 0.3:
                    max_similarity = similarity
                    best_cluster = cluster_name
            
            if best_cluster:
                clusters[best_cluster].append(note)
            else:
                # Create new cluster
                cluster_name = self.generate_cluster_name(keywords)
                clusters[cluster_name] = [note]
        
        return clusters
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (simplified)"""
        # Remove common words and extract meaningful terms
        words = text.lower().split()
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if word not in common_words and len(word) > 3]
        return keywords[:10]  # Top 10 keywords
    
    def calculate_similarity(self, keywords: List[str], cluster_name: str) -> float:
        """Calculate similarity between keywords and cluster name"""
        cluster_words = cluster_name.lower().split()
        common = len(set(keywords) & set(cluster_words))
        total = len(set(keywords) | set(cluster_words))
        return common / total if total > 0 else 0
    
    def generate_cluster_name(self, keywords: List[str]) -> str:
        """Generate a meaningful cluster name"""
        if not keywords:
            return "general_research"
        
        # Use most frequent keywords
        keyword_counts = Counter(keywords)
        top_keywords = [word for word, count in keyword_counts.most_common(3)]
        return "_".join(top_keywords)
    
    def synthesize_themes(self, note_clusters: Dict[str, List[ResearchNote]]) -> List[ResearchTheme]:
        """Synthesize research themes from note clusters"""
        themes = []
        
        for cluster_name, cluster_notes in note_clusters.items():
            if len(cluster_notes) < 2:  # Skip clusters with too few notes
                continue
            
            # Synthesize theme from cluster
            theme = self.create_theme_from_cluster(cluster_name, cluster_notes)
            if theme:
                themes.append(theme)
        
        return themes
    
    def create_theme_from_cluster(self, cluster_name: str, 
                                 notes: List[ResearchNote]) -> ResearchTheme:
        """Create a research theme from a cluster of notes"""
        system_prompt = """You are an expert at synthesizing research themes. 
        Create a coherent theme description from the provided research notes."""
        
        notes_content = "\n".join([f"- {note.content[:200]}..." for note in notes[:10]])
        
        prompt = f"""
        Cluster: {cluster_name}
        Research Notes:
        {notes_content}
        
        Synthesize a research theme with:
        1. Clear, descriptive title
        2. Comprehensive description of the theme
        3. Key patterns identified
        4. Research gaps or opportunities
        
        Format as:
        TITLE: theme title
        DESCRIPTION: detailed description
        PATTERNS: key patterns
        GAPS: research gaps identified
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt)
            
            # Parse response
            title = self.extract_field(response, "TITLE") or cluster_name.replace("_", " ").title()
            description = self.extract_field(response, "DESCRIPTION") or "Synthesized theme from research notes"
            
            theme = ResearchTheme(
                id=str(uuid4()),
                title=title,
                description=description,
                papers=[note.paper_id for note in notes],
                frequency=len(notes),
                confidence=min(0.9, len(notes) / 10)  # Higher confidence with more notes
            )
            
            return theme
            
        except Exception as e:
            logger.error(f"Error creating theme from cluster: {e}")
            return None
    
    def extract_field(self, text: str, field: str) -> str:
        """Extract specific field from formatted text"""
        try:
            if f"{field}:" in text:
                return text.split(f"{field}:")[1].split("\n")[0].strip()
        except:
            pass
        return ""
    
    def identify_research_gaps(self, themes: List[ResearchTheme]) -> List[str]:
        """Identify research gaps from synthesized themes"""
        system_prompt = """You are an expert at identifying research gaps and opportunities. 
        Analyze the research themes to identify areas that need more investigation."""
        
        themes_summary = "\n".join([f"- {theme.title}: {theme.description[:200]}..." for theme in themes])
        
        prompt = f"""
        Research Themes:
        {themes_summary}
        
        Identify 5-7 specific research gaps or opportunities based on these themes.
        Focus on:
        1. Understudied areas
        2. Methodological gaps
        3. Emerging opportunities
        4. Cross-cutting issues
        
        List each gap clearly and concisely.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt)
            gaps = [line.strip() for line in response.split("\n") if line.strip() and not line.startswith("#")]
            return gaps[:7]  # Limit to 7 gaps
            
        except Exception as e:
            logger.error(f"Error identifying research gaps: {e}")
            return []
    
    def synthesize_research_landscape(self, notes: List[ResearchNote]) -> Dict[str, Any]:
        """Main method to synthesize research landscape"""
        logger.info(f"Synthesizing themes from {len(notes)} research notes")
        
        # Cluster notes by similarity
        note_clusters = self.cluster_notes_by_similarity(notes)
        logger.info(f"Created {len(note_clusters)} note clusters")
        
        # Synthesize themes
        themes = self.synthesize_themes(note_clusters)
        
        # Save themes to database
        for theme in themes:
            db.save_theme(theme)
        
        # Identify research gaps
        gaps = self.identify_research_gaps(themes)
        
        logger.info(f"Synthesized {len(themes)} research themes")
        
        return {
            'themes': themes,
            'gaps': gaps,
            'clusters': note_clusters
        }