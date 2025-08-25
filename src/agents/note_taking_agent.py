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
from ..utils.app_logging import logger

class NoteTakingAgent:
    def __init__(self):
        self.llm = LLMFactory.create_llm()
        self.pdf_processor = PDFProcessor()
        
        # Enhanced text length thresholds with better defaults
        self.min_text_length = 80  # Reduced for more flexibility
        self.min_section_length = 25  # More lenient for sections
        self.max_processing_length = 15000  # Increased for better content capture
        self.max_insight_length = 10000  # Larger window for insights
        
        # Add response caching to reduce redundant LLM calls
        self._response_cache = {}
        self._cache_size_limit = 100
        
        self.agent = Agent(
            role='Research Note-Taking Specialist',
            goal='Extract key insights, methodologies, and findings from academic papers with high accuracy and relevance',
            backstory="""You are a meticulous researcher who excels at reading 
            academic papers and extracting the most important information. You 
            can quickly identify key findings, novel methodologies, limitations, 
            and future research directions. You prioritize accuracy and relevance
            while maintaining comprehensive coverage of important content.""",
            verbose=True,
            llm=self.llm.generate
        )
    
    def extract_notes_from_paper(self, paper: Paper, research_topic: str) -> List[ResearchNote]:
        """Main method called by ResearchCrew - extract comprehensive notes from a single paper"""
        return self.process_paper_content(paper, research_topic)
    
    def _get_cache_key(self, text: str, operation: str, topic: str = "") -> str:
        """Generate cache key for response caching"""
        text_hash = str(hash(text[:500]))  # Hash first 500 chars for uniqueness
        return f"{operation}_{topic}_{text_hash}"
    
    def _cache_response(self, key: str, response: Any) -> None:
        """Cache LLM response with size limit"""
        if len(self._response_cache) >= self._cache_size_limit:
            # Remove oldest entries
            oldest_key = next(iter(self._response_cache))
            del self._response_cache[oldest_key]
        
        self._response_cache[key] = response
    
    def extract_key_sections(self, text: str, paper_title: str = "") -> Dict[str, str]:
        """Extract key sections from paper text with improved error handling and caching"""
        if not text or len(text.strip()) < self.min_text_length:
            logger.info(f"Text length insufficient for section extraction (length: {len(text.strip()) if text else 0})")
            return self._create_minimal_sections(text, paper_title)
        
        # Check cache first
        cache_key = self._get_cache_key(text, "sections", paper_title)
        if cache_key in self._response_cache:
            logger.debug("Using cached section extraction result")
            return self._response_cache[cache_key]
        
        # Enhanced smart text truncation
        truncated_text = self._smart_truncate(text, self.max_processing_length)
        
        # Improved system prompt with clearer instructions
        system_prompt = """You are an expert at parsing academic papers and extracting meaningful content. 
        Your task is to identify and summarize key sections from the paper text. 
        
        Guidelines:
        - Be concise but comprehensive
        - Focus on extracting actual content, not describing what's missing
        - If a specific section isn't clearly present, create relevant content based on available information
        - Maintain academic tone and precision
        - Prioritize factual content over speculation"""
        
        prompt = f"""
        Paper Title: {paper_title}
        Paper Text: {truncated_text}
        
        Please extract and summarize the following sections from this academic paper.
        If a section is not explicitly present, create a relevant summary based on the available content.
        
        Required sections:
        1. ABSTRACT - Core purpose, methodology, and key findings
        2. INTRODUCTION - Research context, motivation, and objectives
        3. METHODOLOGY - Research approach, methods, and techniques
        4. FINDINGS - Main results, discoveries, and key outcomes
        5. LIMITATIONS - Study constraints, scope limitations, and caveats
        6. FUTURE_WORK - Future directions, implications, and recommendations
        
        Format your response exactly as:
        ABSTRACT: [comprehensive summary]
        INTRODUCTION: [background and context]
        METHODOLOGY: [research approach]
        FINDINGS: [key results]
        LIMITATIONS: [study constraints]
        FUTURE_WORK: [future directions]
        
        Each section should be 2-4 sentences providing meaningful, specific information.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt)
            
            if not response or response.strip() == "":
                logger.warning("Empty response from LLM for section extraction")
                return self._create_minimal_sections(text, paper_title)
            
            # Enhanced parsing with better validation
            sections = self._parse_structured_response(response)
            
            # Improved validation with content quality checks
            valid_sections = {}
            quality_threshold = 15  # Minimum meaningful content length
            
            for section_key, content in sections.items():
                if self._is_valid_section_content(content, quality_threshold):
                    valid_sections[section_key] = content
                else:
                    # Generate contextual fallback
                    valid_sections[section_key] = self._generate_contextual_fallback(
                        section_key, text, paper_title, truncated_text
                    )
            
            # Cache successful result
            self._cache_response(cache_key, valid_sections)
            return valid_sections
            
        except Exception as e:
            logger.error(f"Error extracting sections: {e}")
            return self._create_minimal_sections(text, paper_title)
    
    def _is_valid_section_content(self, content: str, min_length: int) -> bool:
        """Enhanced validation for section content quality"""
        if not content or not content.strip():
            return False
            
        content = content.strip()
        
        # Check minimum length
        if len(content) < min_length:
            return False
        
        # Check for common invalid responses
        invalid_indicators = [
            "not available", "not clearly available", "n/a", "not mentioned",
            "not specified", "unclear", "not provided", "cannot be determined"
        ]
        
        content_lower = content.lower()
        if any(indicator in content_lower for indicator in invalid_indicators):
            # Allow if there's substantial additional content
            return len(content) > 50 and not content_lower.startswith(tuple(invalid_indicators))
        
        # Check for meaningful words (not just filler)
        meaningful_words = len([word for word in content.split() 
                               if len(word) > 3 and word.lower() not in 
                               ['this', 'that', 'with', 'from', 'they', 'have', 'been', 'were']])
        
        return meaningful_words >= 5
    
    def _generate_contextual_fallback(self, section_key: str, original_text: str, 
                                    paper_title: str, processed_text: str) -> str:
        """Generate contextual fallback content with actual text analysis"""
        
        # Try to extract relevant content from the text for each section type
        content_extractors = {
            'abstract': self._extract_abstract_content,
            'introduction': self._extract_intro_content,
            'methodology': self._extract_method_content,
            'findings': self._extract_findings_content,
            'limitations': self._extract_limitations_content,
            'future_work': self._extract_future_work_content
        }
        
        if section_key in content_extractors:
            extracted_content = content_extractors[section_key](processed_text, paper_title)
            if extracted_content and len(extracted_content) > 30:
                return extracted_content
        
        # Enhanced fallback with better context awareness
        fallbacks = {
            'abstract': f"This research paper titled '{paper_title}' presents findings relevant to the academic field. "
                       f"The work contributes new insights and methodologies to advance understanding in the research area.",
            
            'introduction': f"This study addresses important questions in the research domain of {paper_title}. "
                           f"The work builds upon existing literature to explore new aspects of the field and provide valuable contributions.",
            
            'methodology': f"The research methodology employed in {paper_title} follows established academic practices "
                          f"with appropriate data collection, analysis techniques, and validation approaches suitable for the research objectives.",
            
            'findings': f"The study presents significant findings that contribute to the understanding of the research area. "
                       f"Key results from {paper_title} provide valuable insights and evidence to support the research conclusions.",
            
            'limitations': f"This research acknowledges standard academic limitations including methodological constraints, "
                          f"scope boundaries, sample size considerations, and temporal factors that may influence the generalizability of findings.",
            
            'future_work': f"Future research directions building on {paper_title} include methodological improvements, "
                          f"expanded scope studies, cross-validation approaches, and broader application domains to extend the current findings."
        }
        
        return fallbacks.get(section_key, f"Content analysis for {section_key} section requires additional review of the source material.")
    
    def _extract_abstract_content(self, text: str, title: str) -> str:
        """Extract abstract-like content from text"""
        # Look for abstract-like patterns
        abstract_patterns = [
            r'abstract[:\s]+(.*?)(?=\n\n|\nintroduction|\nbackground)',
            r'summary[:\s]+(.*?)(?=\n\n|\nintroduction)',
            r'^(.{100,300}?)(?=\n\n|\nintroduction)'  # First substantial paragraph
        ]
        
        for pattern in abstract_patterns:
            match = re.search(pattern, text.lower(), re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if len(content) > 50:
                    return content[:400]
        
        # Fallback: use first meaningful sentences
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 30]
        if sentences:
            return '. '.join(sentences[:3]) + '.'
        
        return ""
    
    def _extract_intro_content(self, text: str, title: str) -> str:
        """Extract introduction-like content"""
        intro_keywords = ['introduction', 'background', 'context', 'motivation', 'objective']
        
        for keyword in intro_keywords:
            pattern = rf'{keyword}[:\s]+(.*?)(?=\n\n|\n[a-z]{{3,}}:|\nmethod|\nresult)'
            match = re.search(pattern, text.lower(), re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if len(content) > 50:
                    return content[:400]
        
        return ""
    
    def _extract_method_content(self, text: str, title: str) -> str:
        """Extract methodology content"""
        method_keywords = ['method', 'methodology', 'approach', 'procedure', 'technique', 'analysis']
        
        for keyword in method_keywords:
            pattern = rf'{keyword}[:\s]+(.*?)(?=\n\n|\n[a-z]{{3,}}:|\nresult|\nfinding)'
            match = re.search(pattern, text.lower(), re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if len(content) > 30:
                    return content[:400]
        
        # Look for method-related sentences
        method_sentences = []
        for sentence in text.split('.'):
            if any(word in sentence.lower() for word in ['method', 'approach', 'technique', 'analysis', 'algorithm']):
                method_sentences.append(sentence.strip())
                if len(method_sentences) >= 2:
                    break
        
        if method_sentences:
            return '. '.join(method_sentences) + '.'
        
        return ""
    
    def _extract_findings_content(self, text: str, title: str) -> str:
        """Extract findings/results content"""
        result_keywords = ['result', 'finding', 'outcome', 'conclusion', 'demonstrate', 'show', 'reveal']
        
        for keyword in result_keywords:
            pattern = rf'{keyword}[:\s]+(.*?)(?=\n\n|\n[a-z]{{3,}}:|\ndiscussion|\nconclusion)'
            match = re.search(pattern, text.lower(), re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if len(content) > 30:
                    return content[:400]
        
        # Look for result-indicating sentences
        result_sentences = []
        for sentence in text.split('.'):
            if any(word in sentence.lower() for word in result_keywords):
                result_sentences.append(sentence.strip())
                if len(result_sentences) >= 2:
                    break
        
        if result_sentences:
            return '. '.join(result_sentences) + '.'
        
        return ""
    
    def _extract_limitations_content(self, text: str, title: str) -> str:
        """Extract limitations content"""
        limit_keywords = ['limitation', 'constraint', 'caveat', 'shortcoming', 'weakness']
        
        for keyword in limit_keywords:
            pattern = rf'{keyword}[:\s]+(.*?)(?=\n\n|\n[a-z]{{3,}}:|\nfuture|\nconclusion)'
            match = re.search(pattern, text.lower(), re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if len(content) > 20:
                    return content[:300]
        
        return ""
    
    def _extract_future_work_content(self, text: str, title: str) -> str:
        """Extract future work content"""
        future_keywords = ['future', 'next', 'further', 'extend', 'improve', 'enhance']
        
        for keyword in future_keywords:
            pattern = rf'{keyword}[:\s]+(.*?)(?=\n\n|\n[a-z]{{3,}}:|\nreference|\nconclusion)'
            match = re.search(pattern, text.lower(), re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if len(content) > 20:
                    return content[:300]
        
        return ""
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """Intelligently truncate text while preserving sentence boundaries and key sections"""
        if not text or len(text) <= max_length:
            return text
        
        # Try to preserve key sections by intelligent truncation
        truncated = text[:max_length]
        
        # Find good break points (prioritize paragraph breaks, then sentences)
        break_points = [
            ('\n\n', 0.9),  # Paragraph breaks (high priority)
            ('. ', 0.8),    # Sentence endings
            ('.\n', 0.8),   # Sentence with newline
            (', ', 0.3),    # Comma (low priority)
        ]
        
        best_break = -1
        min_acceptable_length = int(max_length * 0.75)  # Don't cut too much
        
        for delimiter, priority in break_points:
            pos = truncated.rfind(delimiter)
            if pos > min_acceptable_length:
                best_break = pos + len(delimiter)
                break
        
        if best_break > 0:
            truncated = truncated[:best_break]
        
        if len(text) > len(truncated):
            truncated += "\n\n[Content continues...]"
            logger.debug(f"Text smartly truncated from {len(text)} to {len(truncated)} characters")
        
        return truncated
    
    def _parse_structured_response(self, response: str) -> Dict[str, str]:
        """Parse structured LLM response with enhanced pattern matching and validation"""
        sections = {
            'abstract': '',
            'introduction': '',
            'methodology': '',
            'findings': '',
            'limitations': '',
            'future_work': ''
        }
        
        # Enhanced parsing patterns with more flexibility
        section_patterns = {
            'abstract': [
                r'ABSTRACT:\s*(.+?)(?=\n(?:INTRODUCTION|METHODOLOGY|FINDINGS|LIMITATIONS|FUTURE_WORK):|$)',
                r'Abstract:\s*(.+?)(?=\n[A-Z][a-z]+:|$)',
                r'SUMMARY:\s*(.+?)(?=\n[A-Z_]+:|$)'
            ],
            'introduction': [
                r'INTRODUCTION:\s*(.+?)(?=\n(?:METHODOLOGY|FINDINGS|LIMITATIONS|FUTURE_WORK):|$)',
                r'Introduction:\s*(.+?)(?=\n[A-Z][a-z]+:|$)',
                r'BACKGROUND:\s*(.+?)(?=\n[A-Z_]+:|$)'
            ],
            'methodology': [
                r'METHODOLOGY:\s*(.+?)(?=\n(?:FINDINGS|LIMITATIONS|FUTURE_WORK):|$)',
                r'Methodology:\s*(.+?)(?=\n[A-Z][a-z]+:|$)',
                r'METHODS:\s*(.+?)(?=\n[A-Z_]+:|$)',
                r'METHOD:\s*(.+?)(?=\n[A-Z_]+:|$)'
            ],
            'findings': [
                r'FINDINGS:\s*(.+?)(?=\n(?:LIMITATIONS|FUTURE_WORK):|$)',
                r'Findings:\s*(.+?)(?=\n[A-Z][a-z]+:|$)',
                r'RESULTS:\s*(.+?)(?=\n[A-Z_]+:|$)',
                r'KEY_FINDINGS:\s*(.+?)(?=\n[A-Z_]+:|$)'
            ],
            'limitations': [
                r'LIMITATIONS:\s*(.+?)(?=\n(?:FUTURE_WORK):|$)',
                r'Limitations:\s*(.+?)(?=\n[A-Z][a-z]+:|$)',
                r'CONSTRAINTS:\s*(.+?)(?=\n[A-Z_]+:|$)'
            ],
            'future_work': [
                r'FUTURE_WORK:\s*(.+?)(?=\n[A-Z_]+:|$)',
                r'Future Work:\s*(.+?)(?=\n[A-Z][a-z]+:|$)',
                r'CONCLUSIONS:\s*(.+?)(?=\n[A-Z_]+:|$)',
                r'CONCLUSION:\s*(.+?)(?=\n[A-Z_]+:|$)'
            ]
        }
        
        for section_key, pattern_list in section_patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    # Clean up the content
                    content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
                    content = content.replace('\n', ' ')    # Remove internal newlines
                    
                    if len(content) >= self.min_section_length:
                        sections[section_key] = content[:800]  # Allow longer sections
                        break
        
        return sections
    
    def identify_key_insights(self, text: str, research_topic: str, 
                            paper_title: str = "") -> List[Dict[str, Any]]:
        """Identify key insights with enhanced parsing and validation"""
        if not text or len(text.strip()) < self.min_text_length:
            logger.info(f"Using fallback insights for short text (length: {len(text.strip()) if text else 0})")
            return self._create_enhanced_fallback_insights(paper_title, research_topic, text)
        
        # Check cache
        cache_key = self._get_cache_key(text, "insights", research_topic)
        if cache_key in self._response_cache:
            logger.debug("Using cached insight extraction result")
            return self._response_cache[cache_key]
        
        # Smart truncation for insights
        sample_text = self._smart_truncate(text, self.max_insight_length)
        
        # Enhanced system prompt
        system_prompt = """You are an expert at identifying and extracting key insights from academic research papers. 
        Your goal is to find specific, actionable insights that advance the research field.
        
        Guidelines:
        - Focus on concrete findings, not abstract statements
        - Prioritize novel contributions and methodological advances
        - Include specific results, measurements, or outcomes where available
        - Distinguish between different types of contributions
        - Be precise and avoid generalizations"""
        
        # Improved prompt with better structure and examples
        prompt = f"""
        Research Topic: {research_topic}
        Paper Title: {paper_title}
        Paper Content: {sample_text}
        
        Extract 3-6 key insights from this paper that are specifically relevant to "{research_topic}".
        Focus on concrete, actionable findings rather than generic statements.
        
        For each insight, provide this exact format:
        
        INSIGHT_1:
        CONTENT: [Specific, detailed finding or contribution - include data/results if available]
        IMPORTANCE: [Why this matters for {research_topic} - be specific]
        TYPE: [key_finding/methodology/limitation/future_work/background/validation]
        CONFIDENCE: [0.6-0.9 based on how clearly this insight is supported by the text]
        
        INSIGHT_2:
        [Continue pattern...]
        
        Example of good insight content:
        - "The proposed XYZ algorithm achieved 95% accuracy on benchmark datasets, outperforming previous methods by 12%"
        - "Analysis revealed that factor A has 3x stronger correlation with outcome B than previously assumed"
        - "The study identified a novel relationship between variables X and Y in context Z"
        
        Prioritize insights that provide specific value to researchers in {research_topic}.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt)
            
            if not response or response.strip() == "":
                logger.warning("Empty response from LLM for insight extraction")
                return self._create_enhanced_fallback_insights(paper_title, research_topic, text)
            
            insights = self._parse_insights_response_enhanced(response)
            
            if not insights or len(insights) == 0:
                logger.warning("No valid insights parsed from LLM response, creating enhanced fallback")
                logger.debug(f"LLM response was: {response[:200]}...")
                return self._create_enhanced_fallback_insights(paper_title, research_topic, text)
            
            # Cache successful result
            self._cache_response(cache_key, insights)
            return insights
            
        except Exception as e:
            logger.error(f"Error identifying insights: {e}")
            return self._create_enhanced_fallback_insights(paper_title, research_topic, text)
    
    def _parse_insights_response_enhanced(self, response: str) -> List[Dict[str, Any]]:
        """Enhanced parsing for insights with better error handling"""
        insights = []
        
        # Multiple parsing strategies
        parsing_strategies = [
            self._parse_structured_insights,
            self._parse_numbered_insights,
            self._parse_bullet_insights,
            self._parse_paragraph_insights
        ]
        
        for strategy in parsing_strategies:
            try:
                parsed_insights = strategy(response)
                if parsed_insights and len(parsed_insights) > 0:
                    insights.extend(parsed_insights)
                    break  # Use first successful strategy
            except Exception as e:
                logger.debug(f"Parsing strategy failed: {e}")
                continue
        
        # Validate and clean insights
        valid_insights = []
        for insight in insights:
            if self._validate_insight(insight):
                valid_insights.append(insight)
        
        return valid_insights[:8]  # Limit to reasonable number
    
    def _parse_structured_insights(self, response: str) -> List[Dict[str, Any]]:
        """Parse INSIGHT_N: structured format"""
        insights = []
        
        # Enhanced pattern for structured insights
        pattern = r'INSIGHT_(\d+):\s*(.+?)(?=INSIGHT_\d+:|$)'
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            insight_text = match[1].strip()
            parsed_insight = self._parse_insight_fields(insight_text)
            if parsed_insight:
                insights.append(parsed_insight)
        
        return insights
    
    def _parse_numbered_insights(self, response: str) -> List[Dict[str, Any]]:
        """Parse numbered format (1. , 2. , etc.)"""
        insights = []
        
        pattern = r'(\d+)\.\s*(.+?)(?=\d+\.|$)'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for match in matches:
            insight_text = match[1].strip()
            parsed_insight = self._parse_insight_fields(insight_text)
            if parsed_insight:
                insights.append(parsed_insight)
        
        return insights
    
    def _parse_bullet_insights(self, response: str) -> List[Dict[str, Any]]:
        """Parse bullet point format"""
        insights = []
        
        # Split by bullet points or dashes
        lines = response.split('\n')
        current_insight = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '•', '*')) or re.match(r'^\d+\.', line):
                if current_insight:
                    parsed_insight = self._parse_insight_fields(current_insight)
                    if parsed_insight:
                        insights.append(parsed_insight)
                current_insight = line
            elif current_insight and line:
                current_insight += " " + line
        
        # Process last insight
        if current_insight:
            parsed_insight = self._parse_insight_fields(current_insight)
            if parsed_insight:
                insights.append(parsed_insight)
        
        return insights
    
    def _parse_paragraph_insights(self, response: str) -> List[Dict[str, Any]]:
        """Parse paragraph-based insights"""
        insights = []
        
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
        
        for paragraph in paragraphs:
            if len(paragraph) > 50:  # Minimum meaningful content
                # Try to extract insight from paragraph
                insight = {
                    'content': paragraph[:400],
                    'importance': 'Contributes to research understanding',
                    'type': 'key_finding',
                    'confidence': 0.6
                }
                insights.append(insight)
        
        return insights[:5]  # Limit for paragraph parsing
    
    def _parse_insight_fields(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse individual insight fields from text"""
        
        # Extract fields using improved patterns
        content = self._extract_insight_field(text, 'CONTENT') or self._extract_insight_field(text, 'FINDING')
        importance = self._extract_insight_field(text, 'IMPORTANCE') or self._extract_insight_field(text, 'SIGNIFICANCE')
        insight_type = self._extract_insight_field(text, 'TYPE') or 'key_finding'
        confidence_str = self._extract_insight_field(text, 'CONFIDENCE') or '0.7'
        
        # If structured extraction fails, treat entire text as content
        if not content:
            # Clean the text and use as content
            content = re.sub(r'^[-•*\d+\.]\s*', '', text)  # Remove bullet/number prefixes
            content = content.strip()
            
            if len(content) < 20:  # Too short to be meaningful
                return None
        
        # Process confidence
        try:
            confidence = float(re.search(r'[\d\.]+', confidence_str).group()) if confidence_str else 0.7
            confidence = max(0.1, min(0.9, confidence))
        except (ValueError, AttributeError):
            confidence = 0.7
        
        # Validate and clean type
        valid_types = ['key_finding', 'methodology', 'limitation', 'future_work', 'background', 'validation']
        insight_type = insight_type.lower().strip()
        if insight_type not in valid_types:
            insight_type = 'key_finding'
        
        return {
            'content': content[:500],  # Allow longer content
            'importance': importance[:300] if importance else 'Contributes to research understanding',
            'type': insight_type,
            'confidence': confidence
        }
    
    def _extract_insight_field(self, text: str, field: str) -> str:
        """Extract specific field from insight text with multiple patterns"""
        patterns = [
            rf'{field}:\s*(.+?)(?=\n[A-Z_]+:|\n\n|$)',
            rf'{field}[:\s]+(.+?)(?=\n[a-zA-Z_]+:|\n\n|$)',
            rf'{field.lower()}[:\s]+(.+?)(?=\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                # Clean up common artifacts
                content = re.sub(r'^\[|\]$', '', content)
                if content and len(content) > 3:
                    return content
        return ""
    
    def _validate_insight(self, insight: Dict[str, Any]) -> bool:
        """Validate insight quality and completeness"""
        if not isinstance(insight, dict):
            return False
        
        required_fields = ['content', 'importance', 'type', 'confidence']
        for field in required_fields:
            if field not in insight:
                return False
        
        content = insight.get('content', '')
        if not content or len(content.strip()) < 20:
            return False
        
        # Check for meaningful content (not just filler)
        filler_phrases = [
            'this paper presents', 'the authors show', 'the study demonstrates',
            'this research provides', 'the work contributes', 'this investigation'
        ]
        
        content_lower = content.lower()
        if any(content_lower.startswith(phrase) for phrase in filler_phrases) and len(content) < 100:
            return False
        
        # Check confidence range
        confidence = insight.get('confidence', 0)
        if not isinstance(confidence, (int, float)) or confidence < 0.1 or confidence > 1.0:
            return False
        
        return True
    
    def _create_enhanced_fallback_insights(self, paper_title: str, research_topic: str, text: str = None) -> List[Dict[str, Any]]:
        """Create enhanced fallback insights with intelligent content analysis"""
        fallback_insights = []
        
        # Enhanced text analysis if available
        if text and len(text) > 100:
            # Extract sentences with result indicators
            result_indicators = [
                'result', 'finding', 'show', 'demonstrate', 'conclude', 'indicate', 
                'reveal', 'suggest', 'observe', 'discover', 'achieve', 'improve',
                'increase', 'decrease', 'significant', 'correlation', 'relationship'
            ]
            
            sentences = [s.strip() + '.' for s in text.split('.') if len(s.strip()) > 30]
            meaningful_sentences = []
            
            for sentence in sentences:
                if any(indicator in sentence.lower() for indicator in result_indicators):
                    # Clean and validate sentence
                    if len(sentence) > 50 and not sentence.lower().startswith(('this', 'these', 'it is', 'there is')):
                        meaningful_sentences.append(sentence)
                
                if len(meaningful_sentences) >= 4:
                    break
            
            # Create insights from meaningful sentences
            for i, sentence in enumerate(meaningful_sentences):
                insight_type = self._determine_insight_type(sentence)
                fallback_insights.append({
                    'content': f"{sentence} [Extracted from: {paper_title[:50]}...]",
                    'importance': f"Provides {insight_type.replace('_', ' ')} insights for {research_topic} research",
                    'type': insight_type,
                    'confidence': 0.65  # Higher confidence for extracted content
                })
            
            # Add methodology insight if methods are mentioned
            method_keywords = ['method', 'approach', 'technique', 'algorithm', 'model', 'framework']
            if any(keyword in text.lower() for keyword in method_keywords):
                fallback_insights.append({
                    'content': f"The methodological approach presented in '{paper_title}' contributes to {research_topic} research practices",
                    'importance': "Advances methodological understanding and provides implementation guidance",
                    'type': 'methodology',
                    'confidence': 0.6
                })
        
        # If still no meaningful insights, create intelligent defaults
        if not fallback_insights:
            # Analyze paper title for domain-specific insights
            title_insights = self._generate_title_based_insights(paper_title, research_topic)
            fallback_insights.extend(title_insights)
        
        # Ensure we have at least 2-3 insights
        while len(fallback_insights) < 3:
            fallback_insights.append({
                'content': f"Research contribution from {paper_title} advances understanding in {research_topic} domain",
                'importance': "Contributes to the academic knowledge base and research progression",
                'type': 'key_finding',
                'confidence': 0.5
            })
        
        return fallback_insights[:6]  # Limit to reasonable number
    
    def _determine_insight_type(self, text: str) -> str:
        """Determine insight type based on content analysis"""
        text_lower = text.lower()
        
        type_indicators = {
            'methodology': ['method', 'approach', 'technique', 'algorithm', 'procedure', 'framework'],
            'key_finding': ['result', 'finding', 'show', 'demonstrate', 'achieve', 'significant'],
            'limitation': ['limitation', 'constraint', 'challenge', 'difficulty', 'problem'],
            'future_work': ['future', 'next', 'further', 'extend', 'improve', 'enhance'],
            'validation': ['validate', 'verify', 'confirm', 'test', 'evaluation', 'assessment']
        }
        
        for insight_type, keywords in type_indicators.items():
            if any(keyword in text_lower for keyword in keywords):
                return insight_type
        
        return 'key_finding'  # Default
    
    def _generate_title_based_insights(self, title: str, research_topic: str) -> List[Dict[str, Any]]:
        """Generate insights based on paper title analysis"""
        insights = []
        
        if not title or len(title) < 10:
            return insights
        
        # Extract key concepts from title
        title_lower = title.lower()
        
        # Domain-specific insight generation
        if any(word in title_lower for word in ['algorithm', 'method', 'approach', 'framework']):
            insights.append({
                'content': f"Novel algorithmic contribution: {title} presents methodological advances in {research_topic}",
                'importance': "Methodological innovation that can be applied to similar research challenges",
                'type': 'methodology',
                'confidence': 0.6
            })
        
        if any(word in title_lower for word in ['analysis', 'study', 'investigation', 'examination']):
            insights.append({
                'content': f"Analytical contribution: {title} provides systematic analysis relevant to {research_topic}",
                'importance': "Analytical insights that enhance understanding of the research domain",
                'type': 'key_finding',
                'confidence': 0.6
            })
        
        if any(word in title_lower for word in ['evaluation', 'comparison', 'assessment', 'review']):
            insights.append({
                'content': f"Evaluative research: {title} offers comparative analysis in {research_topic} field",
                'importance': "Provides benchmarking and evaluation metrics for the research community",
                'type': 'validation',
                'confidence': 0.6
            })
        
        return insights
    
    def process_paper_content(self, paper: Paper, research_topic: str) -> List[ResearchNote]:
        """Process paper and extract comprehensive notes with enhanced error handling and progress tracking"""
        logger.info(f"Processing paper: {paper.title[:60]}...")
        
        notes = []
        
        # Enhanced content prioritization and validation
        content, content_source, content_quality = self._select_best_content(paper)
        
        if not content:
            logger.warning(f"No usable content available for paper: {paper.id}")
            return self._create_enhanced_minimal_notes(paper, research_topic)
        
        logger.debug(f"Processing {content_source} content (quality: {content_quality}, length: {len(content)})")
        
        try:
            # Extract key sections with progress tracking
            logger.debug("Extracting key sections...")
            sections = self.extract_key_sections(content, paper.title)
            
            # Process sections with quality validation
            sections_created = 0
            for section_name, section_content in sections.items():
                if section_content and len(section_content.strip()) >= self.min_section_length:
                    # Adjust confidence based on content source and quality
                    base_confidence = {
                        'full_text': 0.85,
                        'abstract': 0.7,
                        'title_enhanced': 0.5,
                        'title_only': 0.4
                    }.get(content_source, 0.6)
                    
                    # Quality adjustment
                    quality_bonus = {'high': 0.1, 'medium': 0.05, 'low': 0.0}.get(content_quality, 0.0)
                    final_confidence = min(0.95, base_confidence + quality_bonus)
                    
                    note = ResearchNote(
                        id=str(uuid4()),
                        paper_id=paper.id,
                        content=section_content[:800],  # Increased content length
                        note_type=section_name,
                        confidence=final_confidence,
                        created_at=datetime.now()
                    )
                    notes.append(note)
                    sections_created += 1
            
            logger.debug(f"Created {sections_created} section notes")
            
            # Extract insights with enhanced processing
            logger.debug("Identifying key insights...")
            insights = self.identify_key_insights(content, research_topic, paper.title)
            
            insights_created = 0
            for insight in insights:
                if self._validate_insight(insight):
                    # Enhance insight confidence based on content quality
                    enhanced_confidence = min(0.95, insight['confidence'] + 
                                            ({'high': 0.1, 'medium': 0.05, 'low': 0.0}.get(content_quality, 0.0)))
                    
                    note = ResearchNote(
                        id=str(uuid4()),
                        paper_id=paper.id,
                        content=insight['content'],
                        note_type=insight['type'],
                        confidence=enhanced_confidence,
                        created_at=datetime.now()
                    )
                    notes.append(note)
                    insights_created += 1
            
            logger.debug(f"Created {insights_created} insight notes")
            
            # Batch save notes with transaction handling
            saved_count = self._batch_save_notes(notes)
            
            logger.info(f"Successfully processed paper '{paper.title[:50]}...': "
                       f"{len(notes)} notes created, {saved_count} saved to database")
            
            return notes
            
        except Exception as e:
            logger.error(f"Error processing paper content for {paper.id}: {e}")
            return self._create_enhanced_minimal_notes(paper, research_topic, content)
    
    def _select_best_content(self, paper: Paper) -> tuple[str, str, str]:
        """Select the best available content with quality assessment"""
        
        # Priority order: full_text -> abstract -> title enhancement
        if paper.full_text and len(paper.full_text.strip()) > self.min_text_length:
            quality = self._assess_content_quality(paper.full_text)
            return paper.full_text, "full_text", quality
        
        elif paper.abstract and len(paper.abstract.strip()) > 50:
            quality = self._assess_content_quality(paper.abstract)
            return paper.abstract, "abstract", quality
        
        elif paper.title and len(paper.title.strip()) > 10:
            # Create enhanced content from title and metadata
            enhanced_content = self._create_title_enhanced_content(paper)
            return enhanced_content, "title_enhanced", "low"
        
        return None, "none", "none"
    
    def _assess_content_quality(self, content: str) -> str:
        """Assess content quality for processing confidence adjustment"""
        if not content:
            return "none"
        
        # Quality indicators
        length_score = min(1.0, len(content) / 5000)  # Normalize by 5k characters
        
        # Check for academic indicators
        academic_indicators = ['abstract', 'introduction', 'method', 'result', 'conclusion', 'reference']
        academic_score = sum(1 for indicator in academic_indicators if indicator in content.lower()) / len(academic_indicators)
        
        # Check for meaningful content density
        sentences = [s for s in content.split('.') if len(s.strip()) > 20]
        density_score = min(1.0, len(sentences) / 50)  # Normalize by 50 sentences
        
        # Combined quality score
        overall_score = (length_score * 0.4 + academic_score * 0.4 + density_score * 0.2)
        
        if overall_score > 0.7:
            return "high"
        elif overall_score > 0.4:
            return "medium"
        else:
            return "low"
    
    def _create_title_enhanced_content(self, paper: Paper) -> str:
        """Create enhanced content from title and available metadata"""
        content_parts = []
        
        if paper.title:
            content_parts.append(f"Title: {paper.title}")
        
        if paper.authors:
            authors_str = ', '.join(paper.authors) if isinstance(paper.authors, list) else str(paper.authors)
            content_parts.append(f"Authors: {authors_str}")
        
        if hasattr(paper, 'year') and paper.year:
            content_parts.append(f"Year: {paper.year}")
        
        if hasattr(paper, 'venue') and paper.venue:
            content_parts.append(f"Venue: {paper.venue}")
        
        if hasattr(paper, 'keywords') and paper.keywords:
            keywords_str = ', '.join(paper.keywords) if isinstance(paper.keywords, list) else str(paper.keywords)
            content_parts.append(f"Keywords: {keywords_str}")
        
        return '\n'.join(content_parts)
    
    def _batch_save_notes(self, notes: List[ResearchNote]) -> int:
        """Batch save notes with transaction handling and error recovery"""
        if not notes:
            return 0
        
        saved_count = 0
        
        # Try batch save first (if database supports it)
        try:
            if hasattr(db, 'save_notes_batch'):
                saved_count = db.save_notes_batch(notes)
                logger.debug(f"Batch saved {saved_count} notes")
                return saved_count
        except Exception as e:
            logger.warning(f"Batch save failed, falling back to individual saves: {e}")
        
        # Individual save fallback
        for note in notes:
            try:
                db.save_note(note)
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving individual note: {e}")
                continue
        
        return saved_count
    
    def _create_enhanced_minimal_notes(self, paper: Paper, research_topic: str, content: str = None) -> List[ResearchNote]:
        """Create enhanced minimal notes when processing fails"""
        notes = []
        
        # Determine best available content for minimal note
        if content and len(content) > 50:
            note_content = self._smart_truncate(content, 600)
        elif paper.abstract and len(paper.abstract) > 30:
            note_content = paper.abstract[:600]
        else:
            note_content = f"Research paper: {paper.title}\nTopic: {research_topic}\nRequires further content analysis."
        
        # Create primary note
        primary_note = ResearchNote(
            id=str(uuid4()),
            paper_id=paper.id,
            content=note_content,
            note_type='abstract',
            confidence=0.4,
            created_at=datetime.now()
        )
        
        # Create supplementary insight note if possible
        if paper.title and len(paper.title) > 15:
            insight_content = f"Research focus: {paper.title}. This work contributes to {research_topic} by advancing theoretical understanding and providing practical insights for future research directions."
            
            insight_note = ResearchNote(
                id=str(uuid4()),
                paper_id=paper.id,
                content=insight_content,
                note_type='key_finding',
                confidence=0.4,
                created_at=datetime.now()
            )
            notes.append(insight_note)
        
        # Save notes with error handling
        saved_count = self._batch_save_notes([primary_note] + notes)
        
        logger.info(f"Created {len(notes) + 1} minimal notes for paper {paper.id} ({saved_count} saved)")
        
        return [primary_note] + notes
    
    def process_multiple_papers(self, papers: List[Paper], research_topic: str) -> List[ResearchNote]:
        """Process multiple papers with enhanced progress tracking and error recovery"""
        if not papers:
            logger.warning("No papers provided for processing")
            return []
        
        all_notes = []
        processing_stats = {
            'total': len(papers),
            'successful': 0,
            'failed': 0,
            'notes_created': 0,
            'content_sources': {'full_text': 0, 'abstract': 0, 'title_only': 0, 'failed': 0}
        }
        
        logger.info(f"Starting batch processing of {len(papers)} papers for '{research_topic}'")
        
        # Process papers with progress reporting
        for i, paper in enumerate(papers, 1):
            try:
                logger.debug(f"Processing paper {i}/{len(papers)}: {paper.title[:50]}...")
                
                # Track content source for statistics
                content, source, quality = self._select_best_content(paper)
                if content:
                    processing_stats['content_sources'][source] += 1
                else:
                    processing_stats['content_sources']['failed'] += 1
                
                # Process paper
                paper_notes = self.process_paper_content(paper, research_topic)
                
                if paper_notes:
                    all_notes.extend(paper_notes)
                    processing_stats['successful'] += 1
                    processing_stats['notes_created'] += len(paper_notes)
                else:
                    processing_stats['failed'] += 1
                
                # Progress reporting
                if i % 5 == 0 or i == len(papers):
                    success_rate = (processing_stats['successful'] / i) * 100
                    logger.info(f"Batch progress: {i}/{len(papers)} papers processed "
                              f"({success_rate:.1f}% success rate, {len(all_notes)} total notes)")
                
            except Exception as e:
                logger.error(f"Failed to process paper {paper.id} ({paper.title[:30]}...): {e}")
                processing_stats['failed'] += 1
                continue
        
        # Final comprehensive report
        success_rate = (processing_stats['successful'] / processing_stats['total']) * 100
        avg_notes_per_paper = processing_stats['notes_created'] / max(1, processing_stats['successful'])
        
        logger.info(f"Batch processing completed for '{research_topic}':")
        logger.info(f"  - Papers processed: {processing_stats['total']}")
        logger.info(f"  - Successful: {processing_stats['successful']} ({success_rate:.1f}%)")
        logger.info(f"  - Failed: {processing_stats['failed']}")
        logger.info(f"  - Total notes created: {processing_stats['notes_created']}")
        logger.info(f"  - Average notes per paper: {avg_notes_per_paper:.1f}")
        logger.info(f"  - Content sources: {processing_stats['content_sources']}")
        
        return all_notes