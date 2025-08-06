from crewai import Agent
from typing import List, Dict, Any
from collections import Counter, defaultdict
from uuid import uuid4
import re
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
    
    def extract_keywords(self, text: str, min_length: int = 4, max_keywords: int = 15) -> List[str]:
        """Extract meaningful keywords from text"""
        if not text:
            return []
        
        # Convert to lowercase and remove special characters
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Common stop words to filter out
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'from', 'they', 'them', 'their', 'there', 'where', 'when', 'what', 'who', 'how',
            'can', 'may', 'must', 'shall', 'not', 'no', 'yes', 'also', 'such', 'very', 'more',
            'most', 'much', 'many', 'some', 'any', 'all', 'each', 'every', 'other', 'another',
            'first', 'second', 'third', 'last', 'next', 'previous', 'new', 'old', 'good', 'bad',
            'great', 'small', 'large', 'big', 'little', 'high', 'low', 'long', 'short', 'wide',
            'using', 'used', 'use', 'based', 'approach', 'method', 'technique', 'methods',
            'results', 'result', 'conclusion', 'conclusions', 'study', 'research', 'paper',
            'work', 'article', 'analysis', 'review', 'survey', 'overview', 'summary'
        }
        
        # Filter and count words
        filtered_words = [
            word for word in words 
            if len(word) >= min_length and word not in stop_words and word.isalpha()
        ]
        
        # Count word frequency and return top keywords
        word_counts = Counter(filtered_words)
        return [word for word, count in word_counts.most_common(max_keywords)]
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts based on keyword overlap"""
        if not text1 or not text2:
            return 0.0
        
        keywords1 = set(self.extract_keywords(text1, max_keywords=20))
        keywords2 = set(self.extract_keywords(text2, max_keywords=20))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        
        return intersection / union if union > 0 else 0.0
    
    def cluster_notes_by_similarity(self, notes: List[ResearchNote], 
                                   similarity_threshold: float = 0.2) -> Dict[str, List[ResearchNote]]:
        """Cluster notes by content similarity using improved algorithm"""
        if not notes:
            return {}
        
        clusters = {}
        note_keywords = {}
        
        # Extract keywords for each note
        for note in notes:
            note_keywords[note.id] = self.extract_keywords(note.content)
        
        for note in notes:
            best_cluster = None
            max_similarity = 0
            
            # Try to find best matching cluster
            for cluster_name, cluster_notes in clusters.items():
                # Calculate average similarity with cluster
                similarities = []
                for cluster_note in cluster_notes[:5]:  # Check against first 5 notes in cluster
                    sim = self.calculate_text_similarity(note.content, cluster_note.content)
                    similarities.append(sim)
                
                avg_similarity = sum(similarities) / len(similarities) if similarities else 0
                
                if avg_similarity > max_similarity and avg_similarity > similarity_threshold:
                    max_similarity = avg_similarity
                    best_cluster = cluster_name
            
            if best_cluster:
                clusters[best_cluster].append(note)
            else:
                # Create new cluster
                cluster_name = self.generate_cluster_name(note_keywords.get(note.id, []), note.note_type)
                clusters[cluster_name] = [note]
        
        return clusters
    
    def generate_cluster_name(self, keywords: List[str], note_type: str = "general") -> str:
        """Generate a meaningful cluster name from keywords and note type"""
        if not keywords:
            return f"{note_type}_research_{len(keywords)}"
        
        # Use top 2-3 most meaningful keywords
        top_keywords = keywords[:3]
        
        # Combine with note type if relevant
        if note_type and note_type not in ['general', 'key_finding']:
            cluster_name = f"{note_type}_{'-'.join(top_keywords)}"
        else:
            cluster_name = '-'.join(top_keywords)
        
        return cluster_name[:50]  # Limit length
    
    def synthesize_themes(self, note_clusters: Dict[str, List[ResearchNote]], 
                         min_cluster_size: int = 3) -> List[ResearchTheme]:
        """Synthesize research themes from note clusters"""
        themes = []
        
        for cluster_name, cluster_notes in note_clusters.items():
            if len(cluster_notes) < min_cluster_size:
                logger.debug(f"Skipping cluster '{cluster_name}' with {len(cluster_notes)} notes (below minimum)")
                continue
            
            try:
                theme = self.create_theme_from_cluster(cluster_name, cluster_notes)
                if theme:
                    themes.append(theme)
                    logger.info(f"Created theme: {theme.title}")
            except Exception as e:
                logger.error(f"Error creating theme from cluster '{cluster_name}': {e}")
                continue
        
        # If no themes created from clusters, create fallback themes
        if not themes and note_clusters:
            logger.warning("No themes created from clusters, creating fallback themes")
            themes = self.create_fallback_themes(note_clusters)
        
        return themes
    
    def create_theme_from_cluster(self, cluster_name: str, 
                                 notes: List[ResearchNote]) -> ResearchTheme:
        """Create a research theme from a cluster of notes with better error handling"""
        if not notes:
            return None
        
        # Prepare content for LLM
        notes_sample = notes[:8]  # Limit to avoid token limits
        notes_content = []
        
        for i, note in enumerate(notes_sample, 1):
            content_preview = note.content[:150] + "..." if len(note.content) > 150 else note.content
            notes_content.append(f"{i}. [{note.note_type}] {content_preview}")
        
        notes_text = "\n".join(notes_content)
        
        system_prompt = """You are an expert research analyst. Create a concise research theme from the provided notes. 
        Focus on identifying the main concept, key patterns, and research significance.
        Provide a clear title and description in under 200 words total."""
        
        prompt = f"""
        Research Notes Cluster: {cluster_name.replace('-', ' ').replace('_', ' ').title()}
        Number of related notes: {len(notes)}
        
        Sample Notes:
        {notes_text}
        
        Create a research theme with:
        TITLE: One clear, descriptive title (max 80 characters)
        DESCRIPTION: Detailed description of the theme and its significance (max 150 words)
        
        Focus on the main research concept these notes represent.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt)
            
            if not response or response.strip() == "":
                raise ValueError("Empty response from LLM")
            
            # Parse response more robustly
            title = self.extract_field(response, "TITLE") 
            description = self.extract_field(response, "DESCRIPTION")
            
            # Fallback if parsing fails
            if not title:
                title = cluster_name.replace('-', ' ').replace('_', ' ').title()[:80]
            if not description:
                description = f"Research theme focusing on {title.lower()}. Based on analysis of {len(notes)} related research notes covering various aspects of this topic."
            
            # Calculate confidence based on cluster size and note types
            confidence = min(0.9, 0.4 + (len(notes) * 0.05))  # Base 0.4, +0.05 per note, max 0.9
            
            theme = ResearchTheme(
                id=str(uuid4()),
                title=title[:100],  # Ensure title isn't too long
                description=description[:500],  # Limit description length
                papers=list(set([note.paper_id for note in notes if note.paper_id])),
                frequency=len(notes),
                confidence=confidence
            )
            
            return theme
            
        except Exception as e:
            logger.error(f"Error in LLM theme creation: {e}")
            # Create fallback theme
            return self.create_fallback_theme(cluster_name, notes)
    
    def create_fallback_theme(self, cluster_name: str, notes: List[ResearchNote]) -> ResearchTheme:
        """Create a fallback theme when LLM processing fails"""
        # Extract common keywords from all notes
        all_text = " ".join([note.content for note in notes[:10]])
        keywords = self.extract_keywords(all_text, max_keywords=5)
        
        title = cluster_name.replace('-', ' ').replace('_', ' ').title()
        if keywords:
            title = f"{' '.join(keywords[:3]).title()} Research"
        
        # Count note types
        note_types = Counter([note.note_type for note in notes if note.note_type])
        main_type = note_types.most_common(1)[0][0] if note_types else "research"
        
        description = f"Research theme in {main_type} focusing on {title.lower()}. "
        description += f"This theme emerges from analysis of {len(notes)} research notes "
        
        if keywords:
            description += f"covering topics related to {', '.join(keywords[:3])}."
        else:
            description += "across multiple research papers."
        
        return ResearchTheme(
            id=str(uuid4()),
            title=title[:100],
            description=description[:500],
            papers=list(set([note.paper_id for note in notes if note.paper_id])),
            frequency=len(notes),
            confidence=0.6  # Lower confidence for fallback
        )
    
    def create_fallback_themes(self, note_clusters: Dict[str, List[ResearchNote]]) -> List[ResearchTheme]:
        """Create fallback themes when normal processing fails"""
        themes = []
        all_notes = []
        
        for cluster_notes in note_clusters.values():
            all_notes.extend(cluster_notes)
        
        if not all_notes:
            return themes
        
        # Group by note type
        type_groups = defaultdict(list)
        for note in all_notes:
            note_type = note.note_type or "general"
            type_groups[note_type].append(note)
        
        # Create themes from note types
        for note_type, type_notes in type_groups.items():
            if len(type_notes) >= 3:  # Minimum threshold
                theme = self.create_fallback_theme(note_type, type_notes)
                themes.append(theme)
        
        # If still no themes, create one general theme
        if not themes and len(all_notes) >= 5:
            theme = self.create_fallback_theme("general_research", all_notes)
            themes.append(theme)
        
        return themes
    
    def extract_field(self, text: str, field: str) -> str:
        """Extract specific field from formatted text with better parsing"""
        if not text or not field:
            return ""
        
        # Try multiple patterns
        patterns = [
            f"{field}:\\s*(.+?)(?=\\n[A-Z]+:|$)",  # Field: content
            f"{field}\\s*:(.+?)(?=\\n|$)",          # More flexible
            f"\\*\\*{field}\\*\\*:?\\s*(.+?)(?=\\n|$)",  # **FIELD**: content
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                # Clean up common artifacts
                result = re.sub(r'^[*\-\s]+', '', result)  # Remove leading symbols
                result = re.sub(r'[*\-\s]+$', '', result)  # Remove trailing symbols
                if result:
                    return result
        
        return ""
    
    def identify_research_gaps(self, themes: List[ResearchTheme], 
                              all_notes: List[ResearchNote]) -> List[str]:
        """Identify research gaps from synthesized themes"""
        if not themes:
            return ["Limited research themes identified - more comprehensive analysis needed"]
        
        # Simple gap identification based on theme analysis
        gaps = []
        
        # Analyze theme coverage
        theme_titles = [theme.title.lower() for theme in themes]
        all_content = " ".join([note.content for note in all_notes[:50]])  # Sample content
        
        # Common research areas that might be missing
        common_areas = [
            "longitudinal studies", "clinical trials", "real-world evidence",
            "cost-effectiveness", "patient outcomes", "implementation challenges",
            "regulatory considerations", "ethical implications", "scalability",
            "interoperability", "data quality", "bias mitigation"
        ]
        
        # Check for missing areas
        for area in common_areas:
            if area not in all_content.lower():
                gaps.append(f"Limited research on {area} in the current literature")
        
        # Theme-based gaps
        if len(themes) < 3:
            gaps.append("Limited diversity in research themes - broader investigation needed")
        
        # High confidence themes suggest well-studied areas, low confidence suggests gaps
        low_confidence_themes = [t for t in themes if t.confidence < 0.6]
        if low_confidence_themes:
            gaps.append("Several research areas show low confidence, indicating need for more comprehensive studies")
        
        return gaps[:7]  # Limit to 7 gaps
    
    def synthesize_research_landscape(self, notes: List[ResearchNote]) -> Dict[str, Any]:
        """Main method to synthesize research landscape with improved error handling"""
        logger.info(f"Synthesizing themes from {len(notes)} research notes")
        
        if not notes:
            logger.warning("No notes provided for theme synthesis")
            return {
                'themes': [],
                'gaps': ["No research notes available for analysis"],
                'clusters': {}
            }
        
        try:
            # Cluster notes by similarity
            note_clusters = self.cluster_notes_by_similarity(notes)
            logger.info(f"Created {len(note_clusters)} note clusters")
            
            if not note_clusters:
                logger.warning("No clusters created, creating single cluster")
                note_clusters = {"general_research": notes}
            
            # Synthesize themes
            themes = self.synthesize_themes(note_clusters)
            
            # Save themes to database
            for theme in themes:
                try:
                    db.save_theme(theme)
                    logger.debug(f"Saved theme: {theme.title}")
                except Exception as e:
                    logger.error(f"Error saving theme {theme.title}: {e}")
            
            # Identify research gaps
            gaps = self.identify_research_gaps(themes, notes)
            
            logger.info(f"Synthesized {len(themes)} research themes")
            
            return {
                'themes': themes,
                'gaps': gaps,
                'clusters': note_clusters,
                'statistics': {
                    'total_notes': len(notes),
                    'clusters_created': len(note_clusters),
                    'themes_synthesized': len(themes),
                    'gaps_identified': len(gaps)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in research landscape synthesis: {e}")
            # Return minimal result
            return {
                'themes': [],
                'gaps': [f"Error in theme synthesis: {str(e)}"],
                'clusters': {},
                'statistics': {
                    'total_notes': len(notes),
                    'clusters_created': 0,
                    'themes_synthesized': 0,
                    'gaps_identified': 1
                }
            }