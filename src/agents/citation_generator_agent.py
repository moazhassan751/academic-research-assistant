from crewai import Agent
from typing import List, Dict, Any, Optional
from ..storage.models import Paper, Citation
from ..storage.database import db
from ..tools.citation_formatter import CitationFormatter
from ..tools.Cross_Ref_tool import CrossRefTool
from ..llm.llm_factory import LLMFactory
from ..utils.logging import logger

class CitationGeneratorAgent:
    def __init__(self):
        self.llm = LLMFactory.create_llm()
        self.citation_formatter = CitationFormatter()
        self.crossref_tool = CrossRefTool()
        
        self.agent = Agent(
            role='Citation and Bibliography Specialist',
            goal='Generate properly formatted citations and bibliographies in multiple styles',
            backstory="""You are a meticulous librarian and citation expert who 
            ensures all academic work is properly cited. You understand the 
            nuances of different citation styles and maintain consistency 
            throughout academic documents.""",
            verbose=True,
            llm=self.llm.generate
        )
    
    def generate_citations_for_papers(self, papers: List[Paper]) -> List[Citation]:
        """Generate citations for a list of papers with enhanced quality validation"""
        citations = []
        quality_warnings = []
        
        # Pre-validate paper collection quality
        collection_analysis = self.citation_formatter.suggest_citation_improvements(papers)
        avg_quality = collection_analysis.get('average_quality_score', 0)
        
        if avg_quality < 70:
            logger.warning(f"Paper collection has low average quality: {avg_quality}/100")
            for recommendation in collection_analysis.get('recommendations', []):
                logger.info(f"Quality recommendation: {recommendation}")
        
        for paper in papers:
            try:
                # Assess individual paper quality before processing
                quality_assessment = self.citation_formatter.validate_citation_quality(paper)
                paper_quality = quality_assessment.get('quality_score', 0)
                
                if paper_quality < 50:
                    logger.warning(f"Poor quality paper detected: {paper.title[:50]}... (Score: {paper_quality}/100)")
                    for issue in quality_assessment.get('issues', [])[:3]:  # Show top 3 issues
                        logger.warning(f"  Issue: {issue}")
                    quality_warnings.append({
                        'paper_id': paper.id,
                        'title': paper.title[:50],
                        'score': paper_quality,
                        'issues': quality_assessment.get('issues', [])
                    })
                
                # Check if citation already exists
                existing_citation = db.get_citation(paper.id)
                if existing_citation:
                    citations.append(existing_citation)
                    continue
                
                # Try to get enhanced citation data from CrossRef if we have a DOI
                enhanced_paper = paper
                if hasattr(paper, 'doi') and paper.doi:
                    # Validate DOI format before making API call
                    if self.citation_formatter._validate_doi(paper.doi):
                        try:
                            crossref_paper = self.crossref_tool.get_paper_by_doi(paper.doi)
                            if crossref_paper:
                                # Merge data, preferring more complete information
                                enhanced_paper = self.merge_paper_data(paper, crossref_paper)
                                logger.info(f"Enhanced citation data from CrossRef for: {paper.title[:50]}")
                        except Exception as e:
                            logger.warning(f"Could not enhance citation data from CrossRef: {e}")
                    else:
                        logger.warning(f"Invalid DOI format, skipping CrossRef enhancement: {paper.doi}")
                
                # Generate new citation with enhanced validation
                if self.citation_formatter._validate_paper(enhanced_paper):
                    citation = self.citation_formatter.create_citation(enhanced_paper)
                    
                    # Save to database
                    if db.save_citation(citation):
                        citations.append(citation)
                        logger.info(f"Generated citation for: {paper.title} (Quality: {paper_quality}/100)")
                else:
                    logger.error(f"Paper validation failed, skipping citation generation: {paper.title}")
                    continue
                
            except Exception as e:
                logger.error(f"Error generating citation for paper {paper.id}: {e}")
                continue
        
        # Log collection summary
        logger.info(f"Citation generation complete: {len(citations)} citations generated")
        if quality_warnings:
            logger.warning(f"{len(quality_warnings)} papers had quality issues")
        
        return citations
    
    def merge_paper_data(self, original: Paper, crossref: Paper) -> Paper:
        """Merge paper data, preferring more complete information"""
        # Start with original paper
        merged_data = {
            'id': original.id,
            'title': crossref.title if len(crossref.title) > len(original.title) else original.title,
            'authors': crossref.authors if len(crossref.authors) > len(original.authors) else original.authors,
            'abstract': original.abstract if len(original.abstract) > len(crossref.abstract) else crossref.abstract,
            'url': original.url,  # Keep original URL
            'published_date': crossref.published_date if crossref.published_date else original.published_date,
            'venue': crossref.venue if crossref.venue and not original.venue else original.venue,
            'citations': original.citations,  # Keep original citation count
            'pdf_path': original.pdf_path,
            'full_text': original.full_text,
            'keywords': original.keywords,
            'doi': crossref.doi if crossref.doi else original.doi,
            'arxiv_id': original.arxiv_id,
            'created_at': original.created_at
        }
        
        return Paper(**merged_data)
    
    def create_bibliography(self, citations: List[Citation], 
                           style: str = "apa") -> str:
        """Create formatted bibliography"""
        if not citations:
            return ""
        
        bibliography_entries = []
        
        for citation in citations:
            if style.lower() == "apa":
                entry = citation.apa_format
            elif style.lower() == "mla":
                entry = citation.mla_format
            elif style.lower() == "bibtex":
                entry = citation.bibtex
            else:
                entry = citation.apa_format  # Default to APA
            
            bibliography_entries.append(entry)
        
        # Sort entries alphabetically for APA/MLA
        if style.lower() in ["apa", "mla"]:
            bibliography_entries.sort()
        
        return "\n\n".join(bibliography_entries)
    
    def insert_inline_citations(self, text: str, citations: List[Citation]) -> str:
        """Insert inline citations into text where [Citation] placeholders exist"""
        system_prompt = """You are an expert at inserting inline citations into academic text. 
        Replace [Citation] placeholders with appropriate citations in APA format."""
        
        citations_list = "\n".join([f"- {cite.citation_key}: {cite.apa_format}" 
                                   for cite in citations])
        
        prompt = f"""
        Text with [Citation] placeholders:
        {text}
        
        Available Citations:
        {citations_list}
        
        Replace each [Citation] placeholder with the most appropriate citation key 
        in APA format (Author, Year). Consider the context to choose the best citation.
        
        Return the text with proper inline citations.
        """
        
        try:
            cited_text = self.llm.generate(prompt, system_prompt)
            return cited_text.strip()
        except Exception as e:
            logger.error(f"Error inserting inline citations: {e}")
            return text
    
    def validate_citations(self, citations: List[Citation]) -> Dict[str, List[str]]:
        """Validate citation formats and identify issues with enhanced quality assessment"""
        issues = {
            'missing_authors': [],
            'missing_dates': [],
            'missing_titles': [],
            'format_errors': [],
            'quality_issues': []
        }
        
        for citation in citations:
            citation_key = citation.citation_key
            
            # Get the original paper for quality assessment
            try:
                paper = db.get_paper(citation.paper_id)
                if paper:
                    # Use enhanced quality validation
                    quality_assessment = self.citation_formatter.validate_citation_quality(paper)
                    quality_score = quality_assessment.get('quality_score', 100)
                    
                    if quality_score < 70:
                        issues['quality_issues'].append(
                            f"{citation_key}: Low quality score ({quality_score}/100) - "
                            f"{', '.join(quality_assessment.get('issues', [])[:2])}"
                        )
            except Exception as e:
                logger.warning(f"Could not assess quality for citation {citation_key}: {e}")
            
            # Check APA format
            apa = citation.apa_format
            if not apa or len(apa) < 20:
                issues['format_errors'].append(f"{citation_key}: APA format too short")
            
            if "n.d." in apa:
                issues['missing_dates'].append(f"{citation_key}: Missing publication date")
            
            if "Unknown" in apa:
                issues['missing_authors'].append(f"{citation_key}: Missing author information")
            
            # Check for common formatting problems
            if "Error formatting" in apa:
                issues['format_errors'].append(f"{citation_key}: Citation formatting error")
        
        return issues
    
    def enhance_citation_with_crossref(self, citation: Citation, paper: Paper) -> Citation:
        """Enhance citation using CrossRef data"""
        if not paper.doi:
            return citation
        
        try:
            crossref_paper = self.crossref_tool.get_paper_by_doi(paper.doi)
            if not crossref_paper:
                return citation
            
            # Create enhanced citation
            enhanced_citation = Citation(
                id=citation.id,
                paper_id=citation.paper_id,
                citation_key=citation.citation_key,
                apa_format=self.citation_formatter.format_apa(crossref_paper),
                mla_format=self.citation_formatter.format_mla(crossref_paper),
                bibtex=self.citation_formatter.format_bibtex(crossref_paper, citation.citation_key)
            )
            
            return enhanced_citation
            
        except Exception as e:
            logger.error(f"Error enhancing citation with CrossRef: {e}")
            return citation
    
    def generate_citation_report(self, citations: List[Citation]) -> str:
        """Generate a comprehensive report about citation quality and completeness"""
        total_citations = len(citations)
        if total_citations == 0:
            return "No citations to analyze."
        
        # Get all papers for comprehensive quality analysis
        papers = []
        for citation in citations:
            try:
                paper = db.get_paper(citation.paper_id)
                if paper:
                    papers.append(paper)
            except Exception:
                continue
        
        # Use enhanced collection analysis
        collection_analysis = {}
        if papers:
            collection_analysis = self.citation_formatter.suggest_citation_improvements(papers)
        
        # Validate citations with enhanced features
        issues = self.validate_citations(citations)
        
        # Calculate statistics
        total_issues = sum(len(v) for v in issues.values())
        completeness_percentage = max(0, (total_citations - total_issues) / total_citations * 100)
        
        # Count citations by source
        source_counts = {'crossref': 0, 'openalex': 0, 'arxiv': 0, 'other': 0}
        for citation in citations:
            paper_id = citation.paper_id
            if 'crossref' in paper_id.lower():
                source_counts['crossref'] += 1
            elif 'openalex' in paper_id.lower():
                source_counts['openalex'] += 1
            elif 'arxiv' in paper_id.lower():
                source_counts['arxiv'] += 1
            else:
                source_counts['other'] += 1
        
        # Quality distribution from collection analysis
        quality_dist = collection_analysis.get('quality_distribution', {})
        avg_quality = collection_analysis.get('average_quality_score', 0)
        
        # Build comprehensive report
        report = f"""
Citation Quality Report
======================

Overall Statistics:
- Total Citations: {total_citations}
- Average Quality Score: {avg_quality:.1f}/100
- Citation Completeness: {completeness_percentage:.1f}%

Quality Distribution:
- Excellent (90-100): {quality_dist.get('excellent', 0)}
- Good (80-89): {quality_dist.get('good', 0)}
- Acceptable (70-79): {quality_dist.get('acceptable', 0)}
- Poor (60-69): {quality_dist.get('poor', 0)}
- Very Poor (<60): {quality_dist.get('very_poor', 0)}

Source Distribution:
- CrossRef: {source_counts['crossref']}
- OpenAlex: {source_counts['openalex']}
- ArXiv: {source_counts['arxiv']}
- Other: {source_counts['other']}

Issues Found:
- Missing Authors: {len(issues['missing_authors'])}
- Missing Dates: {len(issues['missing_dates'])}
- Missing Titles: {len(issues['missing_titles'])}
- Format Errors: {len(issues['format_errors'])}
- Quality Issues: {len(issues.get('quality_issues', []))}

Most Common Issues:"""
        
        # Add most common issues from collection analysis
        common_issues = collection_analysis.get('most_common_issues', [])
        for issue_info in common_issues[:5]:
            issue_name = issue_info.get('issue', '')
            count = issue_info.get('count', 0)
            percentage = issue_info.get('percentage', 0)
            report += f"\n- {issue_name}: {count} papers ({percentage}%)"
        
        report += f"""

Recommendations:"""
        
        # Add recommendations from collection analysis
        recommendations = collection_analysis.get('recommendations', [])
        for rec in recommendations:
            report += f"\n- {rec}"
        
        # Add standard recommendations
        if avg_quality < 70:
            report += "\n- Consider improving data quality before generating final citations"
        if len(issues['format_errors']) > 0:
            report += "\n- Review citations with formatting errors"
        if source_counts['other'] > total_citations * 0.5:
            report += "\n- Consider using more authoritative sources (CrossRef, OpenAlex)"
        
        return report.strip()
    
    def analyze_citation_quality_trends(self, citations: List[Citation]) -> Dict[str, Any]:
        """Analyze quality trends across citations for insights"""
        if not citations:
            return {"error": "No citations to analyze"}
        
        # Get papers for quality analysis
        papers = []
        for citation in citations:
            try:
                paper = db.get_paper(citation.paper_id)
                if paper:
                    papers.append(paper)
            except Exception:
                continue
        
        if not papers:
            return {"error": "No papers found for quality analysis"}
        
        # Quality analysis by source
        source_quality = {}
        venue_quality = {}
        year_quality = {}
        
        for paper in papers:
            try:
                quality = self.citation_formatter.validate_citation_quality(paper)
                score = quality.get('quality_score', 0)
                
                # By source
                source = "other"
                if hasattr(paper, 'id') and paper.id:
                    if "crossref" in paper.id.lower():
                        source = "crossref"
                    elif "openalex" in paper.id.lower():
                        source = "openalex"
                    elif "arxiv" in paper.id.lower():
                        source = "arxiv"
                
                if source not in source_quality:
                    source_quality[source] = []
                source_quality[source].append(score)
                
                # By venue
                venue = getattr(paper, 'venue', 'Unknown')[:30]  # Truncate long venue names
                if venue not in venue_quality:
                    venue_quality[venue] = []
                venue_quality[venue].append(score)
                
                # By year
                year = "Unknown"
                if hasattr(paper, 'published_date') and paper.published_date:
                    if hasattr(paper.published_date, 'year'):
                        year = str(paper.published_date.year)
                    else:
                        try:
                            year = str(paper.published_date)[:4]
                        except:
                            pass
                
                if year not in year_quality:
                    year_quality[year] = []
                year_quality[year].append(score)
                
            except Exception as e:
                logger.warning(f"Error analyzing paper quality: {e}")
                continue
        
        # Calculate averages
        source_avg = {k: round(sum(v)/len(v), 1) for k, v in source_quality.items() if v}
        venue_avg = {k: round(sum(v)/len(v), 1) for k, v in venue_quality.items() if v and len(v) >= 2}
        year_avg = {k: round(sum(v)/len(v), 1) for k, v in year_quality.items() if v and len(v) >= 2}
        
        return {
            "total_papers_analyzed": len(papers),
            "source_quality": source_avg,
            "top_venues_by_quality": dict(sorted(venue_avg.items(), key=lambda x: x[1], reverse=True)[:10]),
            "quality_by_year": dict(sorted(year_avg.items())),
            "insights": self._generate_quality_insights(source_avg, venue_avg, year_avg)
        }
    
    def _generate_quality_insights(self, source_avg: Dict, venue_avg: Dict, year_avg: Dict) -> List[str]:
        """Generate insights from quality analysis"""
        insights = []
        
        # Source insights
        if source_avg:
            best_source = max(source_avg.items(), key=lambda x: x[1])
            if best_source[1] > 80:
                insights.append(f"Highest quality citations come from {best_source[0]} (avg: {best_source[1]}/100)")
            
            worst_source = min(source_avg.items(), key=lambda x: x[1])
            if worst_source[1] < 70:
                insights.append(f"Consider improving {worst_source[0]} citations (avg: {worst_source[1]}/100)")
        
        # Venue insights
        if venue_avg:
            high_quality_venues = [k for k, v in venue_avg.items() if v > 85]
            if high_quality_venues:
                insights.append(f"High-quality venues include: {', '.join(high_quality_venues[:3])}")
        
        # Year insights
        if year_avg:
            recent_years = [k for k in year_avg.keys() if k.isdigit() and int(k) >= 2020]
            if recent_years:
                recent_avg = sum(year_avg[y] for y in recent_years) / len(recent_years)
                if recent_avg > 80:
                    insights.append(f"Recent papers (2020+) have good quality (avg: {recent_avg:.1f}/100)")
                elif recent_avg < 70:
                    insights.append(f"Recent papers need quality improvement (avg: {recent_avg:.1f}/100)")
        
        if not insights:
            insights.append("Citation quality appears consistent across sources and venues")
        
        return insights
    
    def suggest_citation_improvements_for_paper(self, paper: Paper) -> Dict[str, Any]:
        """Get specific improvement suggestions for a single paper"""
        try:
            quality_assessment = self.citation_formatter.validate_citation_quality(paper)
            
            # Generate specific recommendations
            recommendations = []
            score = quality_assessment.get('quality_score', 0)
            issues = quality_assessment.get('issues', [])
            
            if score < 50:
                recommendations.append("This paper requires significant data improvement before citation")
            elif score < 70:
                recommendations.append("Consider improving data completeness for better citation quality")
            
            # Specific issue recommendations
            for issue in issues:
                if "Missing publication date" in issue:
                    recommendations.append("Add publication date - essential for academic citations")
                elif "No authors specified" in issue:
                    recommendations.append("Author information is required for proper citation")
                elif "Missing venue" in issue:
                    recommendations.append("Add journal or conference venue information")
                elif "Invalid DOI" in issue:
                    recommendations.append("Verify DOI format (should be 10.xxxx/xxxxx)")
                elif "Missing DOI" in issue:
                    recommendations.append("Add DOI if available for better citation tracking")
            
            return {
                "paper_id": paper.id,
                "title": paper.title[:100],
                "current_quality": quality_assessment,
                "specific_recommendations": recommendations,
                "priority": "high" if score < 50 else "medium" if score < 70 else "low"
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations for paper {paper.id}: {e}")
            return {
                "error": f"Could not analyze paper: {str(e)}",
                "paper_id": getattr(paper, 'id', 'unknown')
            }