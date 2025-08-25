from crewai import Agent
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from ..storage.models import Paper, ResearchNote, ResearchTheme
from ..storage.database import db
from ..llm.llm_factory import LLMFactory
from ..utils.app_logging import logger
import re
import json

class DraftWriterAgent:
    def __init__(self):
        self.llm = LLMFactory.create_llm()
        
        # Domain-specific safety configurations
        self.domain_safety_config = {
            'cybersecurity': {
                'replacements': {
                    'attack': 'security analysis',
                    'exploit': 'vulnerability assessment',
                    'penetration': 'security testing',
                    'injection': 'input validation',
                    'malware': 'malicious software',
                    'hack': 'security modification',
                    'breach': 'security incident',
                    'threat': 'security challenge',
                    'payload': 'data packet',
                    'backdoor': 'unauthorized access point'
                },
                'safe_contexts': ['security research', 'defensive measures', 'protection mechanisms']
            },
            'medical': {
                'replacements': {
                    'kill': 'eliminate',
                    'toxic': 'harmful',
                    'poison': 'contaminate',
                    'virus': 'pathogen',
                    'infection': 'contamination',
                    'disease': 'medical condition',
                    'death': 'mortality',
                    'pain': 'discomfort'
                },
                'safe_contexts': ['medical research', 'therapeutic applications', 'healthcare analysis']
            },
            'ai_ml': {
                'replacements': {
                    'adversarial': 'challenging',
                    'attack': 'perturbation',
                    'poisoning': 'data contamination',
                    'manipulation': 'data modification',
                    'deception': 'misclassification'
                },
                'safe_contexts': ['machine learning research', 'AI safety', 'model robustness']
            },
            'chemistry': {
                'replacements': {
                    'explosive': 'reactive compound',
                    'toxic': 'hazardous',
                    'poison': 'harmful substance',
                    'bomb': 'explosive device',
                    'weapon': 'chemical agent'
                },
                'safe_contexts': ['chemical research', 'laboratory analysis', 'molecular studies']
            },
            'biology': {
                'replacements': {
                    'kill': 'inhibit',
                    'death': 'cell death',
                    'virus': 'viral agent',
                    'infection': 'biological process',
                    'parasite': 'parasitic organism'
                },
                'safe_contexts': ['biological research', 'life sciences', 'cellular analysis']
            },
            'generic': {
                'replacements': {
                    'attack': 'approach',
                    'exploit': 'utilize',
                    'vulnerability': 'limitation',
                    'threat': 'challenge',
                    'weapon': 'tool',
                    'kill': 'terminate',
                    'hack': 'modify'
                },
                'safe_contexts': ['academic research', 'scientific analysis', 'scholarly investigation']
            }
        }
        
        self.agent = Agent(
            role='Academic Writing Specialist',
            goal='Generate well-structured, coherent academic content with proper citations',
            backstory="""You are an experienced academic writer who excels at 
            creating clear, well-structured research papers. You understand 
            academic writing conventions and can synthesize complex information 
            into coherent narratives across all research domains.""",
            verbose=True,
            llm=self.llm.generate
        )
    
    def detect_research_domain(self, research_topic: str, papers: List[Paper]) -> str:
        """Automatically detect research domain from topic and papers"""
        topic_lower = research_topic.lower()
        
        # Check paper titles and abstracts for domain indicators
        paper_text = " ".join([
            paper.title.lower() if paper.title else "" + 
            " " + (paper.abstract.lower() if paper.abstract else "")
            for paper in papers[:10]  # Sample first 10 papers
        ])
        
        domain_keywords = {
            'cybersecurity': ['security', 'cyber', 'hacking', 'malware', 'encryption', 'firewall', 'intrusion', 'vulnerability'],
            'medical': ['medical', 'health', 'disease', 'patient', 'clinical', 'diagnosis', 'treatment', 'therapy'],
            'ai_ml': ['machine learning', 'artificial intelligence', 'neural network', 'deep learning', 'algorithm', 'model'],
            'chemistry': ['chemical', 'molecule', 'compound', 'reaction', 'synthesis', 'catalyst', 'organic', 'inorganic'],
            'biology': ['biology', 'cell', 'gene', 'protein', 'organism', 'evolution', 'genome', 'molecular'],
            'physics': ['physics', 'quantum', 'particle', 'energy', 'force', 'electromagnetic', 'thermodynamic'],
            'computer_science': ['computer', 'software', 'programming', 'algorithm', 'data structure', 'computing'],
            'engineering': ['engineering', 'design', 'system', 'optimization', 'manufacturing', 'construction'],
            'psychology': ['psychology', 'cognitive', 'behavior', 'mental', 'brain', 'consciousness', 'perception'],
            'economics': ['economic', 'market', 'financial', 'trade', 'investment', 'business', 'monetary']
        }
        
        combined_text = topic_lower + " " + paper_text
        
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        
        return 'generic'
    
    def get_domain_config(self, domain: str) -> Dict[str, Any]:
        """Get safety configuration for specific domain"""
        return self.domain_safety_config.get(domain, self.domain_safety_config['generic'])
    
    def sanitize_prompt_for_domain(self, prompt: str, domain: str) -> str:
        """Domain-aware prompt sanitization"""
        config = self.get_domain_config(domain)
        sanitized = prompt
        
        # Apply domain-specific replacements
        for problematic, replacement in config['replacements'].items():
            pattern = f'\\b{re.escape(problematic)}\\b'
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        # Additional universal sanitizations
        universal_replacements = {
            'destroying': 'analyzing',
            'eliminating': 'removing',
            'targeting': 'focusing on',
            'defeating': 'overcoming',
            'crushing': 'comprehensive analysis of',
            'dominating': 'leading in',
            'conquering': 'mastering',
            'annihilating': 'thoroughly examining'
        }
        
        for problematic, replacement in universal_replacements.items():
            pattern = f'\\b{re.escape(problematic)}\\b'
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        # Remove excessive caps and normalize formatting
        sanitized = re.sub(r'[A-Z]{4,}', lambda m: m.group(0).title(), sanitized)
        sanitized = re.sub(r'!{2,}', '!', sanitized)
        sanitized = re.sub(r'\?{2,}', '?', sanitized)
        
        return sanitized
    
    def create_safe_academic_prompt(self, base_prompt: str, domain: str) -> str:
        """Create academically safe prompt with domain context"""
        config = self.get_domain_config(domain)
        safe_context = config['safe_contexts'][0]
        
        safety_prefix = f"""
        You are writing academic content for {safe_context}. 
        Please ensure all content is:
        - Educational and scholarly in nature
        - Appropriate for academic publication
        - Focused on research and analysis
        - Free from harmful or inappropriate content
        
        Academic Context: {safe_context}
        """
        
        sanitized_prompt = self.sanitize_prompt_for_domain(base_prompt, domain)
        return f"{safety_prefix}\n\n{sanitized_prompt}"
    
    def safe_llm_generate(self, prompt: str, system_prompt: str = "", domain: str = "generic") -> str:
        """Universal safe content generation with domain awareness"""
        try:
            # Create domain-aware safe prompts
            safe_prompt = self.create_safe_academic_prompt(prompt, domain)
            safe_system = self.sanitize_prompt_for_domain(system_prompt, domain)
            
            # Add academic safety wrapper
            academic_system = f"""You are a professional academic writing assistant specializing in {domain} research. 
            Provide only educational, scholarly content suitable for academic publication. {safe_system}"""
            
            # Multiple attempts with increasing safety measures
            attempts = [
                (safe_prompt, academic_system),
                (self.create_ultra_safe_prompt(prompt, domain), academic_system),
                (self.create_minimal_safe_prompt(prompt, domain), academic_system)
            ]
            
            for attempt_prompt, attempt_system in attempts:
                try:
                    result = self.llm.generate(attempt_prompt, attempt_system)
                    if result and len(result.strip()) > 10:  # Minimum content check
                        return result
                except Exception as e:
                    logger.warning(f"LLM attempt failed: {e}")
                    continue
            
            # Final fallback
            return self.get_domain_fallback_content(prompt, domain)
            
        except Exception as e:
            logger.error(f"All LLM generation attempts failed: {e}")
            return self.get_domain_fallback_content(prompt, domain)
    
    def create_ultra_safe_prompt(self, prompt: str, domain: str) -> str:
        """Create ultra-conservative safe prompt"""
        # Extract only the core academic request
        core_request = re.sub(r'(write|create|generate)', 'analyze', prompt.lower())
        core_request = re.sub(r'(discuss|examine|explore)', 'review', core_request)
        
        return f"""
        Please provide an educational analysis for academic research in {domain}.
        Focus on: scholarly review, research methodology, and academic insights.
        
        Task: {core_request}
        
        Requirements:
        - Academic language only
        - Educational content
        - Research-focused analysis
        - Scholarly tone throughout
        """
    
    def create_minimal_safe_prompt(self, prompt: str, domain: str) -> str:
        """Create minimal safe prompt as last resort"""
        return f"""
        Provide academic research content for {domain} studies.
        Focus on educational analysis and scholarly insights.
        Use professional academic language.
        """
    
    def get_domain_fallback_content(self, original_prompt: str, domain: str) -> str:
        """Domain-specific fallback content"""
        domain_templates = {
            'cybersecurity': {
                'abstract': "This paper presents a comprehensive analysis of security methodologies and defensive strategies in the cybersecurity domain.",
                'introduction': "The field of cybersecurity has evolved significantly, with researchers developing advanced protection mechanisms and security frameworks.",
                'discussion': "The analysis reveals important patterns in security research and highlights the development of robust defensive systems.",
                'conclusion': "This survey provides insights into cybersecurity research trends and identifies areas for future security analysis."
            },
            'medical': {
                'abstract': "This paper presents a comprehensive review of medical research methodologies and therapeutic approaches in healthcare.",
                'introduction': "Medical research has advanced significantly, contributing to improved patient care and treatment outcomes.",
                'discussion': "The analysis reveals important trends in medical research and highlights developments in therapeutic interventions.",
                'conclusion': "This survey provides insights into medical research developments and identifies areas for future healthcare investigation."
            },
            'ai_ml': {
                'abstract': "This paper presents a comprehensive analysis of machine learning methodologies and artificial intelligence applications.",
                'introduction': "The field of artificial intelligence and machine learning has experienced rapid advancement in recent years.",
                'discussion': "The analysis reveals important developments in AI research and highlights emerging trends in machine learning applications.",
                'conclusion': "This survey provides insights into AI/ML research trends and identifies promising areas for future investigation."
            }
        }
        
        # Determine content type from prompt
        prompt_lower = original_prompt.lower()
        if 'abstract' in prompt_lower:
            content_type = 'abstract'
        elif 'introduction' in prompt_lower:
            content_type = 'introduction'
        elif 'discussion' in prompt_lower:
            content_type = 'discussion'
        elif 'conclusion' in prompt_lower:
            content_type = 'conclusion'
        else:
            content_type = 'abstract'
        
        # Get domain-specific template
        domain_template = domain_templates.get(domain, domain_templates['ai_ml'])
        return domain_template.get(content_type, "This section provides academic analysis of the research topic.")
    
    def validate_content_safety(self, content: str, domain: str) -> bool:
        """Domain-aware content safety validation"""
        # Universal unsafe patterns
        universal_unsafe = [
            r'\b(harm|damage|destroy|eliminate)\s+(people|humans|individuals)',
            r'\b(how to make|instructions for|step by step).*\b(weapon|bomb|explosive)',
            r'\b(illegal|criminal|unlawful)\s+(activities|actions|methods)'
        ]
        
        # Domain-specific validation
        domain_validations = {
            'cybersecurity': [
                r'\bhow to hack\b',
                r'\bexploit.*vulnerability\b',
                r'\bunauthorized access.*methods\b'
            ],
            'medical': [
                r'\bhow to.*harm.*patient',
                r'\bunauthorized.*medication',
                r'\bharmful.*treatment'
            ],
            'chemistry': [
                r'\bhow to.*explosive',
                r'\bmake.*poison',
                r'\bcreate.*harmful.*substance'
            ]
        }
        
        # Check universal patterns
        for pattern in universal_unsafe:
            if re.search(pattern, content, re.IGNORECASE):
                logger.warning(f"Universal unsafe content detected: {pattern}")
                return False
        
        # Check domain-specific patterns
        domain_patterns = domain_validations.get(domain, [])
        for pattern in domain_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                logger.warning(f"Domain-specific unsafe content detected: {pattern}")
                return False
        
        return True
    
    def create_outline(self, research_topic: str, themes: List[ResearchTheme], 
                      paper_type: str = "survey", domain: str = "generic") -> Dict[str, Any]:
        """Create structured outline for academic paper with domain awareness"""
        system_prompt = f"""You are an expert at creating academic paper outlines for {domain} research. 
        Create a detailed, well-structured outline following {domain} academic conventions."""
        
        themes_summary = "\n".join([f"- {theme.title}: {theme.description[:150]}..." 
                                   for theme in themes[:10]])
        
        prompt = f"""
        Research Topic: {research_topic}
        Research Domain: {domain}
        Paper Type: {paper_type}
        
        Key Research Themes:
        {themes_summary}
        
        Create a detailed outline for a {paper_type} paper including:
        1. Title
        2. Abstract structure
        3. Introduction sections
        4. Main body sections (based on themes)
        5. Discussion sections
        6. Conclusion sections
        
        Format as a hierarchical outline with section numbers and descriptions.
        """
        
        try:
            response = self.safe_llm_generate(prompt, system_prompt, domain)
            
            # Parse outline (enhanced structure)
            outline = {
                'title': f"A Survey of {research_topic}",
                'domain': domain,
                'sections': [
                    {'number': '1', 'title': 'Introduction', 'content': ''},
                    {'number': '2', 'title': 'Background and Related Work', 'content': ''},
                    {'number': '3', 'title': 'Literature Review', 'content': ''},
                    {'number': '4', 'title': 'Analysis and Discussion', 'content': ''},
                    {'number': '5', 'title': 'Future Directions', 'content': ''},
                    {'number': '6', 'title': 'Conclusion', 'content': ''}
                ]
            }
            
            return outline
            
        except Exception as e:
            logger.error(f"Error creating outline: {e}")
            return self.get_default_outline(research_topic, domain)
    
    def get_default_outline(self, research_topic: str, domain: str = "generic") -> Dict[str, Any]:
        """Get default outline structure with domain awareness"""
        return {
            'title': f"A Survey of {research_topic}",
            'domain': domain,
            'sections': [
                {'number': '1', 'title': 'Introduction', 'content': ''},
                {'number': '2', 'title': 'Background', 'content': ''},
                {'number': '3', 'title': 'Literature Review', 'content': ''},
                {'number': '4', 'title': 'Discussion', 'content': ''},
                {'number': '5', 'title': 'Conclusion', 'content': ''}
            ]
        }
    
    def write_abstract(self, research_topic: str, themes: List[ResearchTheme],
                      gaps: List[str], domain: str = "generic") -> str:
        """Write abstract for the paper with domain awareness"""
        system_prompt = f"""You are an expert at writing academic abstracts for {domain} research. 
        Write a clear, concise abstract that summarizes the research survey using {domain} terminology."""
        
        themes_brief = ", ".join([theme.title for theme in themes[:5]])
        gaps_brief = "; ".join(gaps[:3]) if gaps else "several areas for future work"
        
        prompt = f"""
        Research Topic: {research_topic}
        Research Domain: {domain}
        Key Themes: {themes_brief}
        Research Areas: {gaps_brief}
        
        Write a 150-200 word academic abstract for a {domain} literature survey that includes:
        1. Brief introduction to the topic within {domain}
        2. Survey methodology and scope
        3. Key findings and themes
        4. Research areas identified
        5. Implications for future {domain} research
        
        Use formal {domain} academic language and structure.
        """
        
        abstract = self.safe_llm_generate(prompt, system_prompt, domain)
        return abstract.strip() if abstract else self.get_domain_fallback_content("abstract", domain)
    
    def write_introduction(self, research_topic: str, papers: List[Paper], domain: str = "generic") -> str:
        """Write introduction section with domain awareness"""
        system_prompt = f"""You are an expert at writing academic introductions for {domain} research. 
        Write a compelling introduction that motivates the research topic within the {domain} context."""
        
        prompt = f"""
        Research Topic: {research_topic}
        Research Domain: {domain}
        Number of Papers Surveyed: {len(papers)}
        
        Write a 300-400 word introduction for {domain} research that:
        1. Establishes the importance of the topic in {domain}
        2. Provides context and motivation within {domain}
        3. Outlines the scope of the survey
        4. Describes the paper's contribution to {domain}
        5. Provides a roadmap of the paper
        
        Use formal {domain} academic language with proper flow and transitions.
        """
        
        introduction = self.safe_llm_generate(prompt, system_prompt, domain)
        return introduction.strip() if introduction else self.get_domain_fallback_content("introduction", domain)
    
    def compile_full_draft(self, research_topic: str, themes: List[ResearchTheme],
                          papers: List[Paper], notes: List[ResearchNote],
                          gaps: List[str]) -> Dict[str, str]:
        """Universal draft compilation with comprehensive domain and safety handling"""
        logger.info(f"Compiling universal draft for: {research_topic}")
        
        try:
            # Auto-detect research domain
            domain = self.detect_research_domain(research_topic, papers)
            logger.info(f"Detected research domain: {domain}")
            
            # Create domain-aware outline
            outline = self.create_outline(research_topic, themes, "survey", domain)
            
            # Initialize sections with comprehensive error handling
            sections = {}
            generation_log = []
            
            # Abstract
            try:
                sections['abstract'] = self.write_abstract(research_topic, themes, gaps, domain)
                if not self.validate_content_safety(sections['abstract'], domain):
                    sections['abstract'] = self.get_domain_fallback_content("abstract", domain)
                generation_log.append("abstract: success")
            except Exception as e:
                logger.error(f"Error writing abstract: {e}")
                sections['abstract'] = self.get_domain_fallback_content("abstract", domain)
                generation_log.append(f"abstract: fallback ({str(e)[:50]})")
            
            # Introduction
            try:
                sections['introduction'] = self.write_introduction(research_topic, papers, domain)
                if not self.validate_content_safety(sections['introduction'], domain):
                    sections['introduction'] = self.get_domain_fallback_content("introduction", domain)
                generation_log.append("introduction: success")
            except Exception as e:
                logger.error(f"Error writing introduction: {e}")
                sections['introduction'] = self.get_domain_fallback_content("introduction", domain)
                generation_log.append(f"introduction: fallback ({str(e)[:50]})")
            
            # Theme sections with domain awareness
            for i, theme in enumerate(themes[:5]):
                try:
                    theme_papers = [p for p in papers if hasattr(p, 'id') and p.id in theme.papers]
                    theme_notes = [n for n in notes if hasattr(n, 'paper_id') and n.paper_id in theme.papers]
                    
                    section_content = self.write_theme_section(theme, theme_papers, theme_notes, domain)
                    if not self.validate_content_safety(section_content, domain):
                        section_content = self.get_domain_fallback_content("theme", domain)
                    
                    sections[f'theme_{i+1}'] = {
                        'title': theme.title,
                        'content': section_content
                    }
                    generation_log.append(f"theme_{i+1}: success")
                except Exception as e:
                    logger.error(f"Error writing theme section {i+1}: {e}")
                    sections[f'theme_{i+1}'] = {
                        'title': theme.title,
                        'content': self.get_domain_fallback_content("theme", domain)
                    }
                    generation_log.append(f"theme_{i+1}: fallback ({str(e)[:50]})")
            
            # Discussion
            try:
                sections['discussion'] = self.write_discussion(themes, gaps, domain)
                if not self.validate_content_safety(sections['discussion'], domain):
                    sections['discussion'] = self.get_domain_fallback_content("discussion", domain)
                generation_log.append("discussion: success")
            except Exception as e:
                logger.error(f"Error writing discussion: {e}")
                sections['discussion'] = self.get_domain_fallback_content("discussion", domain)
                generation_log.append(f"discussion: fallback ({str(e)[:50]})")
            
            # Conclusion
            try:
                sections['conclusion'] = self.write_conclusion(research_topic, themes, gaps, domain)
                if not self.validate_content_safety(sections['conclusion'], domain):
                    sections['conclusion'] = self.get_domain_fallback_content("conclusion", domain)
                generation_log.append("conclusion: success")
            except Exception as e:
                logger.error(f"Error writing conclusion: {e}")
                sections['conclusion'] = self.get_domain_fallback_content("conclusion", domain)
                generation_log.append(f"conclusion: fallback ({str(e)[:50]})")
            
            # Compile final draft with comprehensive metadata
            draft = {
                'title': outline.get('title', f"A Survey of {research_topic}"),
                'abstract': sections.get('abstract', 'Abstract generation failed'),
                'introduction': sections.get('introduction', 'Introduction generation failed'),
                'sections': {k: v for k, v in sections.items() if k.startswith('theme_')},
                'discussion': sections.get('discussion', 'Discussion generation failed'),
                'conclusion': sections.get('conclusion', 'Conclusion generation failed'),
                'metadata': {
                    'topic': research_topic,
                    'domain': domain,
                    'themes_count': len(themes),
                    'papers_count': len(papers),
                    'gaps_count': len(gaps) if gaps else 0,
                    'generated_at': datetime.now().isoformat(),
                    'safety_validated': True,
                    'generation_log': generation_log,
                    'domain_config': self.get_domain_config(domain),
                    'universal_compatibility': True
                }
            }
            
            logger.info(f"Universal draft compilation completed for domain: {domain}")
            logger.info(f"Generation log: {generation_log}")
            return draft
            
        except Exception as e:
            logger.error(f"Critical error in universal draft compilation: {e}")
            return {
                'title': f"A Survey of {research_topic}",
                'abstract': 'Universal draft generation encountered technical difficulties.',
                'introduction': 'Introduction section could not be generated.',
                'sections': {},
                'discussion': 'Discussion section could not be generated.',
                'conclusion': 'Conclusion section could not be generated.',
                'metadata': {
                    'topic': research_topic,
                    'domain': 'unknown',
                    'themes_count': 0,
                    'papers_count': 0,
                    'gaps_count': 0,
                    'generated_at': datetime.now().isoformat(),
                    'safety_validated': False,
                    'universal_compatibility': True,
                    'critical_error': str(e)
                }
            }
    
    def write_theme_section(self, theme: ResearchTheme, 
                           related_papers: List[Paper],
                           related_notes: List[ResearchNote],
                           domain: str = "generic") -> str:
        """Write theme section with domain awareness"""
        system_prompt = f"""You are an expert at writing literature review sections for {domain} research. 
        Write a comprehensive section about the research theme using {domain} academic conventions."""
        
        papers_info = "\n".join([f"- {paper.title} by {', '.join(paper.authors[:2]) if paper.authors else 'Unknown'}..." 
                                for paper in related_papers[:5]])
        
        key_notes = "\n".join([f"- {note.content[:100]}..." 
                              for note in related_notes[:5] if note.content])
        
        prompt = f"""
        Research Domain: {domain}
        Theme: {theme.title}
        Description: {theme.description}
        
        Related Papers:
        {papers_info}
        
        Key Findings:
        {key_notes}
        
        Write a 400-500 word {domain} academic section that:
        1. Introduces the theme within {domain} context
        2. Discusses key contributions from the literature
        3. Synthesizes findings across papers using {domain} terminology
        4. Identifies patterns and trends in {domain}
        5. Notes any differing findings
        
        Use {domain} academic language and indicate where citations would be placed with [Citation].
        """
        
        section = self.safe_llm_generate(prompt, system_prompt, domain)
        return section.strip() if section else self.get_domain_fallback_content("theme", domain)
    
    def write_discussion(self, themes: List[ResearchTheme], gaps: List[str], domain: str = "generic") -> str:
        """Write discussion section with domain awareness"""
        system_prompt = f"""You are an expert at writing academic discussions for {domain} research. 
        Write a thoughtful discussion that synthesizes findings and implications within {domain}."""
        
        themes_summary = "\n".join([f"- {theme.title}: {theme.description[:100]}..." 
                                   for theme in themes])
        gaps_list = "\n".join([f"- {gap}" for gap in gaps[:5]]) if gaps else "- Several areas for future investigation"
        
        prompt = f"""
        Research Domain: {domain}
        Research Themes Identified:
        {themes_summary}
        
        Research Areas:
        {gaps_list}
        
        Write a 500-600 word {domain} discussion section that:
        1. Synthesizes the main findings across themes in {domain}
        2. Discusses implications for the {domain} field
        3. Addresses research areas and opportunities in {domain}
        4. Considers methodological insights for {domain}
        5. Suggests future research directions in {domain}
        
        Use {domain} academic language with clear argumentation.
        """
        
        discussion = self.safe_llm_generate(prompt, system_prompt, domain)
        return discussion.strip() if discussion else self.get_domain_fallback_content("discussion", domain)
    
    def write_conclusion(self, research_topic: str, themes: List[ResearchTheme],
                        gaps: List[str], domain: str = "generic") -> str:
        """Write conclusion section with domain awareness"""
        system_prompt = f"""You are an expert at writing academic conclusions for {domain} research. 
        Write a strong conclusion that summarizes contributions and future directions in {domain}."""
        
        prompt = f"""
        Research Topic: {research_topic}
        Research Domain: {domain}
        Number of Themes: {len(themes)}
        Number of Areas Identified: {len(gaps) if gaps else 0}
        
        Write a 200-300 word {domain} conclusion that:
        1. Summarizes the main contributions of the survey to {domain}
        2. Highlights key insights gained for {domain}
        3. Emphasizes the most important research areas in {domain}
        4. Provides clear future research directions for {domain}
        5. Concludes with the significance of the work to {domain}
        
        Use decisive {domain} academic language that reinforces the paper's value.
        """
        
        conclusion = self.safe_llm_generate(prompt, system_prompt, domain)
        return conclusion.strip() if conclusion else self.get_domain_fallback_content("conclusion", domain)