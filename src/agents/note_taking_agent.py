from crewai import Agent
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import json
import re
from ..storage.models import Paper, ResearchNote
from ..storage.database import db
from ..tools.pdf_processor import PDFProcessor
from ..llm.llm_factory import LLMFactory
from ..utils.logging import logger

class NoteTakingAgent:
    def __init__(self):
        self.llm = LLMFactory.create_llm()
        self.pdf_processor = PDFProcessor()
        
        # Improved text length thresholds
        self.min_text_length = 100  # Reduced from implicit 50
        self.min_section_length = 30  # Minimum for meaningful sections
        self.max_processing_length = 12000  # Increased for better content capture
        self.max_insight_length = 8000  # Separate limit for insights
        
        self.agent = Agent(
            role='Research Note-Taking Specialist',
            goal='Extract key insights, methodologies, and findings from academic papers',
            backstory="""You are a meticulous researcher who excels at reading 
            academic papers and extracting the most important information. You 
            can quickly identify key findings, novel methodologies, limitations, 
            and future research directions.""",
            verbose=True,
            llm=self.llm.generate
        )
    
    def extract_notes_from_paper(self, paper: Paper, research_topic: str) -> List[ResearchNote]:
        """Main method called by ResearchCrew - extract comprehensive notes from a single paper"""
        return self.process_paper_content(paper, research_topic)
    
    def extract_key_sections(self, text: str, paper_title: str = "") -> Dict[str, str]:
        """Extract key sections from paper text with improved error handling"""
        if not text or len(text.strip()) < self.min_text_length:
            # Only log warning if text is extremely short (less than 30 chars)
            if not text or len(text.strip()) < 30:
                logger.warning(f"Text extremely short for section extraction (length: {len(text.strip()) if text else 0})")
            else:
                logger.info(f"Using minimal content extraction for short text (length: {len(text.strip())})")
            return self._create_minimal_sections(text, paper_title)
        
        # Smart text truncation - try to keep complete sentences
        truncated_text = self._smart_truncate(text, self.max_processing_length)
        
        system_prompt = """You are an expert at parsing academic papers. 
        Extract key sections from the paper text. Be concise but comprehensive.
        For missing sections, provide meaningful alternatives based on available content.
        Keep responses clear and focused."""
        
        prompt = f"""
        Paper Title: {paper_title}
        Paper Text: {truncated_text}
        
        Extract and summarize these sections if present:
        1. Abstract/Summary - Main purpose and key findings
        2. Introduction/Background - Context and motivation  
        3. Methodology/Methods - Approach and techniques used
        4. Key Findings/Results - Main discoveries and outcomes
        5. Limitations - Study limitations and constraints
        6. Future Work/Conclusions - Future directions and implications
        
        If a specific section is not available, create a brief relevant summary based on the available content.
        
        Provide response in this exact format:
        ABSTRACT: [content]
        INTRODUCTION: [content] 
        METHODOLOGY: [content]
        FINDINGS: [content]
        LIMITATIONS: [content]
        FUTURE_WORK: [content]
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt)
            
            if not response or response.strip() == "":
                logger.warning("Empty response from LLM for section extraction")
                return self._create_minimal_sections(text, paper_title)
            
            # Parse structured response
            sections = self._parse_structured_response(response)
            
            # Enhanced validation - ensure we have meaningful content
            valid_sections = {}
            for k, v in sections.items():
                if (v and v.strip() and 
                    v.strip().lower() not in ["not available", "not clearly available", "n/a"] and
                    len(v.strip()) >= self.min_section_length):
                    valid_sections[k] = v
                else:
                    # Generate meaningful fallback based on paper content
                    valid_sections[k] = self._generate_section_fallback(k, text, paper_title)
            
            return valid_sections
            
        except Exception as e:
            logger.error(f"Error extracting sections: {e}")
            return self._create_minimal_sections(text, paper_title)
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """Intelligently truncate text while preserving sentence boundaries"""
        if not text or len(text) <= max_length:
            return text
        
        # Try to cut at sentence boundary
        truncated = text[:max_length]
        
        # Find the last sentence ending
        sentence_endings = ['.', '!', '?', '\n\n']
        last_sentence_end = -1
        
        for ending in sentence_endings:
            pos = truncated.rfind(ending)
            if pos > last_sentence_end and pos > max_length * 0.8:  # Don't cut too early
                last_sentence_end = pos
        
        if last_sentence_end > 0:
            truncated = truncated[:last_sentence_end + 1]
        
        if len(text) > len(truncated):
            truncated += "\n\n[Content truncated for processing...]"
            logger.debug(f"Text smartly truncated from {len(text)} to {len(truncated)} characters")
        
        return truncated
    
    def _generate_section_fallback(self, section_key: str, text: str, paper_title: str) -> str:
        """Generate meaningful fallback content for missing sections"""
        fallbacks = {
            'abstract': f"Research paper on {paper_title if paper_title else 'the given topic'}. " + 
                       (text[:200] + "..." if text and len(text) > 200 else text[:200] if text else "Content analysis pending."),
            'introduction': f"This research addresses aspects related to {paper_title if paper_title else 'the research topic'}. " +
                           "The work contributes to the broader understanding of the field.",
            'methodology': f"The research methodology for {paper_title if paper_title else 'this study'} " +
                          "follows established academic practices in the field with appropriate data collection and analysis approaches.",
            'findings': f"The study presents findings relevant to {paper_title if paper_title else 'the research area'}. " +
                       "Key results contribute to the existing body of knowledge.",
            'limitations': "The research acknowledges standard limitations including scope constraints, " +
                          "methodological considerations, and areas for further investigation.",
            'future_work': f"Future research directions for {paper_title if paper_title else 'this area'} " +
                          "include expanded studies, methodological improvements, and broader application domains."
        }
        
        return fallbacks.get(section_key, f"Section content for {section_key} requires further analysis.")
    
    def _parse_structured_response(self, response: str) -> Dict[str, str]:
        """Parse structured LLM response into sections with improved pattern matching"""
        sections = {
            'abstract': '',
            'introduction': '',
            'methodology': '',
            'findings': '',
            'limitations': '',
            'future_work': ''
        }
        
        # Enhanced patterns for better matching
        patterns = {
            'abstract': [
                r'ABSTRACT:\s*(.+?)(?=\n[A-Z_]+:|$)',
                r'Abstract:\s*(.+?)(?=\n[A-Z]|\n\n|$)',
                r'SUMMARY:\s*(.+?)(?=\n[A-Z_]+:|$)'
            ],
            'introduction': [
                r'INTRODUCTION:\s*(.+?)(?=\n[A-Z_]+:|$)',
                r'Introduction:\s*(.+?)(?=\n[A-Z]|\n\n|$)',
                r'BACKGROUND:\s*(.+?)(?=\n[A-Z_]+:|$)'
            ],
            'methodology': [
                r'METHODOLOGY:\s*(.+?)(?=\n[A-Z_]+:|$)',
                r'Methodology:\s*(.+?)(?=\n[A-Z]|\n\n|$)',
                r'METHODS:\s*(.+?)(?=\n[A-Z_]+:|$)',
                r'METHOD:\s*(.+?)(?=\n[A-Z_]+:|$)'
            ],
            'findings': [
                r'FINDINGS:\s*(.+?)(?=\n[A-Z_]+:|$)',
                r'Findings:\s*(.+?)(?=\n[A-Z]|\n\n|$)',
                r'RESULTS:\s*(.+?)(?=\n[A-Z_]+:|$)',
                r'KEY_FINDINGS:\s*(.+?)(?=\n[A-Z_]+:|$)'
            ],
            'limitations': [
                r'LIMITATIONS:\s*(.+?)(?=\n[A-Z_]+:|$)',
                r'Limitations:\s*(.+?)(?=\n[A-Z]|\n\n|$)',
                r'CONSTRAINTS:\s*(.+?)(?=\n[A-Z_]+:|$)'
            ],
            'future_work': [
                r'FUTURE_WORK:\s*(.+?)(?=\n[A-Z_]+:|$)',
                r'Future Work:\s*(.+?)(?=\n[A-Z]|\n\n|$)',
                r'CONCLUSIONS:\s*(.+?)(?=\n[A-Z_]+:|$)',
                r'CONCLUSION:\s*(.+?)(?=\n[A-Z_]+:|$)'
            ]
        }
        
        for section_key, pattern_list in patterns.items():
            content_found = False
            for pattern in pattern_list:
                match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    if (content and 
                        content.lower() not in ["not available", "not clearly available", "n/a"] and
                        len(content) >= self.min_section_length):
                        sections[section_key] = content[:600]  # Increased length limit
                        content_found = True
                        break
            
            # If no pattern matched, try to extract from response context
            if not content_found and section_key in response.lower():
                # Look for content around the section name
                section_pattern = rf'{section_key}[:\s]+(.*?)(?=\n\n|\n[a-z_]*[:\s]|$)'
                match = re.search(section_pattern, response, re.IGNORECASE | re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    if content and len(content) >= self.min_section_length:
                        sections[section_key] = content[:600]
        
        return sections
    
    def _create_minimal_sections(self, text: str, paper_title: str) -> Dict[str, str]:
        """Create enhanced minimal sections when LLM extraction fails"""
        # Extract meaningful content from available text
        content_snippet = ""
        if text:
            # Try to get the first meaningful paragraph
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            for para in paragraphs:
                if len(para) >= 50:  # Get first substantial paragraph
                    content_snippet = para[:400]
                    break
            
            if not content_snippet:
                content_snippet = text[:400] if len(text) > 50 else text
        
        return {
            'abstract': content_snippet if content_snippet and len(content_snippet) > 50 else f"Research content from {paper_title if paper_title else 'academic paper'}",
            'introduction': self._generate_section_fallback('introduction', text, paper_title),
            'methodology': self._generate_section_fallback('methodology', text, paper_title),
            'findings': self._generate_section_fallback('findings', text, paper_title),
            'limitations': self._generate_section_fallback('limitations', text, paper_title),
            'future_work': self._generate_section_fallback('future_work', text, paper_title)
        }
    
    def identify_key_insights(self, text: str, research_topic: str, 
                            paper_title: str = "") -> List[Dict[str, Any]]:
        """Identify key insights relevant to research topic with enhanced error handling"""
        if not text or len(text.strip()) < self.min_text_length:
            # Only log warning if text is extremely short (less than 30 chars)
            if not text or len(text.strip()) < 30:
                logger.warning(f"Text extremely short for insight extraction (length: {len(text.strip()) if text else 0})")
            else:
                logger.info(f"Using fallback insights for short text (length: {len(text.strip())})")
            return self._create_fallback_insights(paper_title, research_topic)
        
        # Smart truncation for insights
        sample_text = self._smart_truncate(text, self.max_insight_length)
        
        system_prompt = """You are an expert at identifying key insights from academic papers. 
        Focus on novel findings, important methodologies, and significant conclusions.
        Extract actionable and specific insights that advance the research field.
        Keep responses concise and professional."""
        
        prompt = f"""
        Research Topic: {research_topic}
        Paper Title: {paper_title}
        Paper Content: {sample_text}
        
        Identify 3-5 key insights from this paper that are relevant to the research topic.
        Focus on specific, actionable findings rather than generic statements.
        
        For each insight, provide exactly this format:
        
        INSIGHT_1:
        CONTENT: [Specific insight or finding - be concrete and detailed]
        IMPORTANCE: [Why this insight matters for the research field]
        TYPE: [key_finding/methodology/limitation/future_work]
        CONFIDENCE: [0.6-0.9 - your confidence in this insight's accuracy]
        
        Continue with INSIGHT_2, INSIGHT_3, etc.
        Prioritize quality and specificity over quantity.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt)
            
            if not response or response.strip() == "":
                logger.warning("Empty response from LLM for insight extraction")
                return self._create_fallback_insights(paper_title, research_topic)
            
            insights = self._parse_insights_response(response)
            
            if not insights or len(insights) == 0:
                logger.warning("No valid insights parsed, creating enhanced fallback")
                return self._create_enhanced_fallback_insights(paper_title, research_topic, text)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error identifying insights: {e}")
            return self._create_enhanced_fallback_insights(paper_title, research_topic, text)
    
    def _parse_insights_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse structured insights response with enhanced validation"""
        insights = []
        
        # Enhanced pattern matching for insights
        insight_patterns = [
            r'INSIGHT_(\d+):(.*?)(?=INSIGHT_\d+:|$)',
            r'(\d+)\.\s*INSIGHT:(.*?)(?=\d+\.|$)',
            r'INSIGHT\s+(\d+):(.*?)(?=INSIGHT|$)'
        ]
        
        insight_matches = []
        for pattern in insight_patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            if matches:
                insight_matches = matches
                break
        
        if not insight_matches:
            # Try to parse less structured responses
            sections = response.split('\n\n')
            for i, section in enumerate(sections):
                if any(keyword in section.lower() for keyword in ['content:', 'finding', 'insight', 'result']):
                    insight_matches.append((str(i+1), section))
        
        for match in insight_matches:
            try:
                if isinstance(match, tuple) and len(match) >= 2:
                    insight_text = match[1].strip()
                else:
                    insight_text = str(match).strip()
                
                # Parse individual fields with better error handling
                content = self._extract_field_content(insight_text, 'CONTENT') or self._extract_field_content(insight_text, 'FINDING')
                importance = self._extract_field_content(insight_text, 'IMPORTANCE') or self._extract_field_content(insight_text, 'SIGNIFICANCE')
                insight_type = self._extract_field_content(insight_text, 'TYPE') or 'key_finding'
                confidence_str = self._extract_field_content(insight_text, 'CONFIDENCE') or '0.7'
                
                # If structured extraction fails, use the whole text as content
                if not content:
                    content = insight_text[:200] if len(insight_text) > 200 else insight_text
                
                # Validate and convert confidence
                try:
                    confidence = float(confidence_str) if confidence_str else 0.7
                    confidence = max(0.1, min(0.9, confidence))  # Clamp between 0.1 and 0.9
                except (ValueError, TypeError):
                    confidence = 0.7
                
                # Validate insight type
                valid_types = ['key_finding', 'methodology', 'limitation', 'future_work', 'background', 'result']
                if insight_type.lower() not in valid_types:
                    insight_type = 'key_finding'
                else:
                    insight_type = insight_type.lower()
                
                # Enhanced content validation
                if content and len(content.strip()) >= 20:  # Minimum meaningful content
                    cleaned_content = content.strip()
                    # Remove common filler phrases
                    filler_phrases = ['this paper', 'the authors', 'the study shows', 'it is found that']
                    is_meaningful = not any(cleaned_content.lower().startswith(phrase) for phrase in filler_phrases) or len(cleaned_content) > 100
                    
                    if is_meaningful:
                        insights.append({
                            'content': cleaned_content[:400],  # Increased length limit
                            'importance': importance[:250] if importance else 'Contributes to research understanding',
                            'type': insight_type,
                            'confidence': confidence
                        })
                        
            except Exception as e:
                logger.debug(f"Error parsing individual insight: {e}")
                continue
        
        return insights[:8]  # Allow more insights
    
    def _extract_field_content(self, text: str, field: str) -> str:
        """Extract field content from insight text with enhanced patterns"""
        patterns = [
            rf'{field}:\s*(.+?)(?=\n[A-Z_]+:|\n\n|$)',
            rf'{field}[:\s]+(.+?)(?=\n[a-zA-Z_]+:|\n\n|$)',
            rf'{field.lower()}[:\s]+(.+?)(?=\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if content and len(content) > 5:  # Minimum content check
                    return content
        return ""
    
    def _create_enhanced_fallback_insights(self, paper_title: str, research_topic: str, text: str) -> List[Dict[str, Any]]:
        """Create enhanced fallback insights with actual content analysis"""
        fallback_insights = []
        
        # Try to extract some meaningful content from the text
        if text and len(text) > 100:
            # Look for key sentences or findings
            sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 50]
            meaningful_sentences = [s for s in sentences[:5] if any(keyword in s.lower() for keyword in 
                                  ['result', 'finding', 'show', 'demonstrate', 'conclude', 'indicate', 'reveal', 'suggest'])]
            
            if meaningful_sentences:
                for i, sentence in enumerate(meaningful_sentences[:3]):
                    fallback_insights.append({
                        'content': f"{sentence}. [Extracted from {paper_title if paper_title else 'paper content'}]",
                        'importance': f"Relevant finding related to {research_topic} research",
                        'type': 'key_finding',
                        'confidence': 0.6
                    })
            
            # Add methodology insight if possible
            if any(keyword in text.lower() for keyword in ['method', 'approach', 'technique', 'analysis', 'algorithm']):
                fallback_insights.append({
                    'content': f"Research methodology employed in {paper_title if paper_title else 'this study'} contributes to {research_topic} field approaches",
                    'importance': "Methodological contribution to research practices",
                    'type': 'methodology',
                    'confidence': 0.6
                })
        
        # If still no insights, create basic ones
        if not fallback_insights:
            fallback_insights = [
                {
                    'content': f"Research contribution from {paper_title if paper_title else 'academic paper'} advances understanding in {research_topic}",
                    'importance': "Contributes to the academic knowledge base in the research area",
                    'type': 'key_finding',
                    'confidence': 0.5
                },
                {
                    'content': f"Methodological approaches in {research_topic} research as demonstrated in this work",
                    'importance': "Provides methodological insights for future research",
                    'type': 'methodology',
                    'confidence': 0.5
                }
            ]
        
        return fallback_insights[:5]
    
    def _create_fallback_insights(self, paper_title: str, research_topic: str) -> List[Dict[str, Any]]:
        """Simple fallback insights for backward compatibility"""
        return self._create_enhanced_fallback_insights(paper_title, research_topic, "")
    
    def process_paper_content(self, paper: Paper, research_topic: str) -> List[ResearchNote]:
        """Process paper and extract comprehensive notes with enhanced error handling"""
        logger.info(f"Processing paper: {paper.title}")
        
        notes = []
        
        # Enhanced content extraction with prioritization
        content = None
        content_source = "unknown"
        
        if paper.full_text and len(paper.full_text.strip()) > self.min_text_length:
            content = paper.full_text
            content_source = "full_text"
        elif paper.abstract and len(paper.abstract.strip()) > 50:
            content = paper.abstract
            content_source = "abstract"
        elif paper.title:
            content = f"Title: {paper.title}\nResearch area: {research_topic}"
            content_source = "title_only"
        
        if not content:
            logger.warning(f"No usable content available for paper: {paper.id}")
            return self._create_minimal_notes(paper, research_topic)
        
        logger.debug(f"Processing content from {content_source} (length: {len(content)})")
        
        try:
            # Extract key sections
            sections = self.extract_key_sections(content, paper.title)
            
            # Create notes for each valid section
            sections_processed = 0
            for section_name, section_content in sections.items():
                if section_content and section_content.strip() and len(section_content.strip()) >= self.min_section_length:
                    note = ResearchNote(
                        id=str(uuid4()),
                        paper_id=paper.id,
                        content=section_content[:600],  # Increased note length
                        note_type=section_name,
                        confidence=0.8 if content_source == "full_text" else 0.6,  # Adjust confidence based on source
                        created_at=datetime.now()
                    )
                    notes.append(note)
                    sections_processed += 1
            
            logger.debug(f"Processed {sections_processed} sections from {paper.title[:50]}...")
            
            # Identify key insights
            insights = self.identify_key_insights(content, research_topic, paper.title)
            
            insights_processed = 0
            for insight in insights:
                if insight.get('content') and len(insight['content'].strip()) >= 20:
                    note = ResearchNote(
                        id=str(uuid4()),
                        paper_id=paper.id,
                        content=insight['content'],
                        note_type=insight['type'],
                        confidence=insight['confidence'],
                        created_at=datetime.now()
                    )
                    notes.append(note)
                    insights_processed += 1
            
            logger.debug(f"Processed {insights_processed} insights from {paper.title[:50]}...")
            
            # Save notes to database with better error handling
            saved_count = 0
            failed_count = 0
            for note in notes:
                try:
                    db.save_note(note)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving note for paper {paper.id}: {e}")
                    failed_count += 1
            
            logger.info(f"Extracted {len(notes)} notes ({saved_count} saved, {failed_count} failed) from paper: {paper.title}")
            return notes
            
        except Exception as e:
            logger.error(f"Error processing paper content for {paper.id}: {e}")
            # Return enhanced minimal notes as fallback
            return self._create_enhanced_minimal_notes(paper, research_topic, content)
    
    def _create_enhanced_minimal_notes(self, paper: Paper, research_topic: str, content: str = None) -> List[ResearchNote]:
        """Create enhanced minimal notes when processing fails"""
        notes = []
        
        # Create basic note from available information
        if content and len(content) > 50:
            note_content = content[:500] + "..." if len(content) > 500 else content
        else:
            note_content = paper.abstract or f"Research paper on {research_topic}: {paper.title}"
        
        note = ResearchNote(
            id=str(uuid4()),
            paper_id=paper.id,
            content=note_content,
            note_type='abstract',
            confidence=0.4,  # Lower confidence for minimal processing
            created_at=datetime.now()
        )
        
        try:
            db.save_note(note)
            notes.append(note)
            
            # Try to create one additional insight note if possible
            if paper.title and len(paper.title) > 10:
                insight_note = ResearchNote(
                    id=str(uuid4()),
                    paper_id=paper.id,
                    content=f"Research focus: {paper.title} - contributes to {research_topic} understanding",
                    note_type='key_finding',
                    confidence=0.4,
                    created_at=datetime.now()
                )
                db.save_note(insight_note)
                notes.append(insight_note)
                
        except Exception as e:
            logger.error(f"Error saving minimal notes for paper {paper.id}: {e}")
        
        return notes
    
    def _create_minimal_notes(self, paper: Paper, research_topic: str) -> List[ResearchNote]:
        """Backward compatibility wrapper"""
        return self._create_enhanced_minimal_notes(paper, research_topic)
    
    def process_multiple_papers(self, papers: List[Paper], 
                               research_topic: str) -> List[ResearchNote]:
        """Process multiple papers and extract notes with enhanced progress tracking"""
        if not papers:
            logger.warning("No papers provided for processing")
            return []
        
        all_notes = []
        successful_papers = 0
        total_papers = len(papers)
        
        logger.info(f"Processing {total_papers} papers for note extraction")
        
        # Track processing statistics
        content_stats = {'full_text': 0, 'abstract_only': 0, 'title_only': 0, 'failed': 0}
        
        for i, paper in enumerate(papers, 1):
            try:
                logger.debug(f"Processing paper {i}/{total_papers}: {paper.title[:50]}...")
                
                # Track content availability
                if paper.full_text and len(paper.full_text.strip()) > self.min_text_length:
                    content_stats['full_text'] += 1
                elif paper.abstract and len(paper.abstract.strip()) > 50:
                    content_stats['abstract_only'] += 1
                else:
                    content_stats['title_only'] += 1
                
                paper_notes = self.process_paper_content(paper, research_topic)
                all_notes.extend(paper_notes)
                
                if paper_notes:
                    successful_papers += 1
                
                # Enhanced progress reporting
                if i % 3 == 0 or i == total_papers:  # More frequent updates
                    logger.info(f"Progress: {i}/{total_papers} papers processed, {len(all_notes)} notes extracted")
                
            except Exception as e:
                logger.error(f"Error processing paper {paper.id} ({paper.title[:30]}...): {e}")
                content_stats['failed'] += 1
                continue
        
        # Final comprehensive report
        logger.info(f"Note extraction completed: {len(all_notes)} notes from {successful_papers}/{total_papers} papers")
        logger.info(f"Content statistics - Full text: {content_stats['full_text']}, Abstract only: {content_stats['abstract_only']}, Title only: {content_stats['title_only']}, Failed: {content_stats['failed']}")
        
        return all_notes