"""
Export utilities for Academic Research Assistant
Supports multiple output formats: PDF, Word, LaTeX, CSV, HTML
"""

import os
import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

try:
    # PDF generation
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    # Word document generation
    from docx import Document
    from docx.shared import Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    # HTML to PDF conversion (alternative)
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False

logger = logging.getLogger(__name__)

class ExportManager:
    """Manages export functionality for research outputs"""
    
    def __init__(self):
        self.supported_formats = {
            'markdown': True,
            'txt': True,
            'json': True,
            'csv': True,
            'html': True,
            'latex': True,
            'pdf': PDF_AVAILABLE or PDFKIT_AVAILABLE,
            'docx': DOCX_AVAILABLE
        }
        
    def get_supported_formats(self) -> Dict[str, bool]:
        """Return dict of supported formats and their availability"""
        return self.supported_formats.copy()
    
    def export_draft(self, draft: Dict[str, Any], output_path: str, 
                    format_type: str = 'markdown') -> bool:
        """
        Export research draft to specified format
        
        Args:
            draft: Draft content dictionary
            output_path: Output file path (without extension)
            format_type: Export format ('markdown', 'pdf', 'docx', 'latex', 'html')
        
        Returns:
            bool: Success status
        """
        try:
            format_type = format_type.lower()
            
            if format_type not in self.supported_formats:
                raise ValueError(f"Unsupported format: {format_type}")
            
            if not self.supported_formats[format_type]:
                raise ValueError(f"Format {format_type} is not available (missing dependencies)")
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == 'markdown':
                return self._export_draft_markdown(draft, f"{output_path}.md")
            elif format_type == 'pdf':
                return self._export_draft_pdf(draft, f"{output_path}.pdf")
            elif format_type == 'docx':
                return self._export_draft_docx(draft, f"{output_path}.docx")
            elif format_type == 'latex':
                return self._export_draft_latex(draft, f"{output_path}.tex")
            elif format_type == 'html':
                return self._export_draft_html(draft, f"{output_path}.html")
            elif format_type == 'json':
                return self._export_draft_json(draft, f"{output_path}.json")
            else:
                raise ValueError(f"Format {format_type} handler not implemented")
                
        except Exception as e:
            logger.error(f"Error exporting draft to {format_type}: {e}")
            return False
    
    def export_bibliography(self, bibliography: str, papers: List[Any], 
                          output_path: str, format_type: str = 'txt') -> bool:
        """
        Export bibliography to specified format
        
        Args:
            bibliography: Bibliography text content
            papers: List of paper objects
            output_path: Output file path (without extension)
            format_type: Export format ('txt', 'csv', 'bibtex', 'json', 'pdf', 'docx')
        
        Returns:
            bool: Success status
        """
        try:
            format_type = format_type.lower()
            
            # Map bibtex to latex for consistency
            if format_type == 'bibtex':
                format_type = 'latex'
            
            if format_type not in self.supported_formats:
                raise ValueError(f"Unsupported format: {format_type}")
            
            if not self.supported_formats[format_type]:
                raise ValueError(f"Format {format_type} is not available (missing dependencies)")
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == 'txt':
                return self._export_bibliography_txt(bibliography, f"{output_path}.txt")
            elif format_type == 'csv':
                return self._export_bibliography_csv(papers, f"{output_path}.csv")
            elif format_type == 'json':
                return self._export_bibliography_json(papers, f"{output_path}.json")
            elif format_type == 'latex':
                return self._export_bibliography_bibtex(papers, f"{output_path}.bib")
            elif format_type == 'pdf':
                return self._export_bibliography_pdf(bibliography, f"{output_path}.pdf")
            elif format_type == 'docx':
                return self._export_bibliography_docx(bibliography, f"{output_path}.docx")
            else:
                raise ValueError(f"Format {format_type} handler not implemented")
                
        except Exception as e:
            logger.error(f"Error exporting bibliography to {format_type}: {e}")
            return False
    
    # Draft export methods
    def _export_draft_markdown(self, draft: Dict[str, Any], filepath: str) -> bool:
        """Export draft as Markdown"""
        try:
            md_content = self._format_draft_as_markdown(draft)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
            logger.info(f"Draft exported to Markdown: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting draft to Markdown: {e}")
            return False
    
    def _export_draft_pdf(self, draft: Dict[str, Any], filepath: str) -> bool:
        """Export draft as PDF"""
        try:
            if PDF_AVAILABLE:
                return self._export_draft_pdf_reportlab(draft, filepath)
            elif PDFKIT_AVAILABLE:
                return self._export_draft_pdf_pdfkit(draft, filepath)
            else:
                raise ValueError("No PDF library available")
        except Exception as e:
            logger.error(f"Error exporting draft to PDF: {e}")
            return False
    
    def _export_draft_pdf_reportlab(self, draft: Dict[str, Any], filepath: str) -> bool:
        """Export draft as PDF using ReportLab"""
        try:
            doc = SimpleDocTemplate(filepath, pagesize=A4,
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                alignment=TA_CENTER,
                spaceAfter=30
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=20,
                spaceAfter=12
            )
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                alignment=TA_JUSTIFY,
                spaceBefore=6,
                spaceAfter=6
            )
            
            story = []
            
            # Title
            title = draft.get('title', 'Research Paper Draft')
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))
            
            # Abstract
            if 'abstract' in draft and draft['abstract']:
                story.append(Paragraph("Abstract", heading_style))
                story.append(Paragraph(str(draft['abstract']), normal_style))
                story.append(Spacer(1, 12))
            
            # Introduction
            if 'introduction' in draft and draft['introduction']:
                story.append(Paragraph("1. Introduction", heading_style))
                story.append(Paragraph(str(draft['introduction']), normal_style))
                story.append(Spacer(1, 12))
            
            # Sections
            section_num = 2
            if 'sections' in draft and draft['sections']:
                for key, section in draft['sections'].items():
                    if key.startswith('theme_') and isinstance(section, dict):
                        title = section.get('title', f'Section {section_num}')
                        content = section.get('content', 'Content unavailable')
                        story.append(Paragraph(f"{section_num}. {title}", heading_style))
                        story.append(Paragraph(str(content), normal_style))
                        story.append(Spacer(1, 12))
                        section_num += 1
            
            # Discussion
            if 'discussion' in draft and draft['discussion']:
                story.append(Paragraph(f"{section_num}. Discussion", heading_style))
                story.append(Paragraph(str(draft['discussion']), normal_style))
                story.append(Spacer(1, 12))
                section_num += 1
            
            # Conclusion
            if 'conclusion' in draft and draft['conclusion']:
                story.append(Paragraph(f"{section_num}. Conclusion", heading_style))
                story.append(Paragraph(str(draft['conclusion']), normal_style))
                story.append(Spacer(1, 12))
            
            # References
            if 'bibliography' in draft and draft['bibliography']:
                story.append(PageBreak())
                story.append(Paragraph("References", heading_style))
                story.append(Paragraph(str(draft['bibliography']), normal_style))
            
            doc.build(story)
            logger.info(f"Draft exported to PDF: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating PDF with ReportLab: {e}")
            return False
    
    def _export_draft_pdf_pdfkit(self, draft: Dict[str, Any], filepath: str) -> bool:
        """Export draft as PDF using pdfkit (HTML to PDF)"""
        try:
            # First create HTML
            html_content = self._format_draft_as_html(draft)
            
            # Convert to PDF
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None
            }
            
            pdfkit.from_string(html_content, filepath, options=options)
            logger.info(f"Draft exported to PDF: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating PDF with pdfkit: {e}")
            return False
    
    def _export_draft_docx(self, draft: Dict[str, Any], filepath: str) -> bool:
        """Export draft as Word document"""
        try:
            doc = Document()
            
            # Title
            title = draft.get('title', 'Research Paper Draft')
            title_para = doc.add_heading(title, level=0)
            title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Abstract
            if 'abstract' in draft and draft['abstract']:
                doc.add_heading('Abstract', level=1)
                doc.add_paragraph(str(draft['abstract']))
            
            # Introduction
            if 'introduction' in draft and draft['introduction']:
                doc.add_heading('1. Introduction', level=1)
                doc.add_paragraph(str(draft['introduction']))
            
            # Sections
            section_num = 2
            if 'sections' in draft and draft['sections']:
                for key, section in draft['sections'].items():
                    if key.startswith('theme_') and isinstance(section, dict):
                        title = section.get('title', f'Section {section_num}')
                        content = section.get('content', 'Content unavailable')
                        doc.add_heading(f'{section_num}. {title}', level=1)
                        doc.add_paragraph(str(content))
                        section_num += 1
            
            # Discussion
            if 'discussion' in draft and draft['discussion']:
                doc.add_heading(f'{section_num}. Discussion', level=1)
                doc.add_paragraph(str(draft['discussion']))
                section_num += 1
            
            # Conclusion
            if 'conclusion' in draft and draft['conclusion']:
                doc.add_heading(f'{section_num}. Conclusion', level=1)
                doc.add_paragraph(str(draft['conclusion']))
            
            # References
            if 'bibliography' in draft and draft['bibliography']:
                doc.add_page_break()
                doc.add_heading('References', level=1)
                doc.add_paragraph(str(draft['bibliography']))
            
            doc.save(filepath)
            logger.info(f"Draft exported to Word: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating Word document: {e}")
            return False
    
    def _export_draft_latex(self, draft: Dict[str, Any], filepath: str) -> bool:
        """Export draft as LaTeX document"""
        try:
            latex_content = self._format_draft_as_latex(draft)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            logger.info(f"Draft exported to LaTeX: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting draft to LaTeX: {e}")
            return False
    
    def _export_draft_html(self, draft: Dict[str, Any], filepath: str) -> bool:
        """Export draft as HTML document"""
        try:
            html_content = self._format_draft_as_html(draft)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Draft exported to HTML: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting draft to HTML: {e}")
            return False
    
    def _export_draft_json(self, draft: Dict[str, Any], filepath: str) -> bool:
        """Export draft as JSON document"""
        try:
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(draft, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Draft exported to JSON: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting draft to JSON: {e}")
            return False
    
    # Bibliography export methods
    def _export_bibliography_txt(self, bibliography: str, filepath: str) -> bool:
        """Export bibliography as plain text"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(bibliography)
            logger.info(f"Bibliography exported to text: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting bibliography to text: {e}")
            return False
    
    def _export_bibliography_csv(self, papers: List[Any], filepath: str) -> bool:
        """Export bibliography as CSV"""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['title', 'authors', 'year', 'journal', 'doi', 'url', 'abstract']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for paper in papers:
                    writer.writerow({
                        'title': getattr(paper, 'title', ''),
                        'authors': '; '.join(getattr(paper, 'authors', [])),
                        'year': getattr(paper.published_date, 'year', '') if hasattr(paper, 'published_date') and paper.published_date else '',
                        'journal': getattr(paper, 'journal', ''),
                        'doi': getattr(paper, 'doi', ''),
                        'url': getattr(paper, 'url', ''),
                        'abstract': getattr(paper, 'abstract', '')[:500] + '...' if len(getattr(paper, 'abstract', '')) > 500 else getattr(paper, 'abstract', '')
                    })
            
            logger.info(f"Bibliography exported to CSV: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting bibliography to CSV: {e}")
            return False
    
    def _export_bibliography_json(self, papers: List[Any], filepath: str) -> bool:
        """Export bibliography as JSON"""
        try:
            papers_data = []
            for paper in papers:
                paper_dict = {
                    'title': getattr(paper, 'title', ''),
                    'authors': getattr(paper, 'authors', []),
                    'year': getattr(paper.published_date, 'year', None) if hasattr(paper, 'published_date') and paper.published_date else None,
                    'journal': getattr(paper, 'journal', ''),
                    'doi': getattr(paper, 'doi', ''),
                    'url': getattr(paper, 'url', ''),
                    'abstract': getattr(paper, 'abstract', ''),
                    'keywords': getattr(paper, 'keywords', [])
                }
                papers_data.append(paper_dict)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(papers_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Bibliography exported to JSON: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting bibliography to JSON: {e}")
            return False
    
    def _export_bibliography_bibtex(self, papers: List[Any], filepath: str) -> bool:
        """Export bibliography as BibTeX"""
        try:
            bibtex_content = self._format_papers_as_bibtex(papers)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(bibtex_content)
            logger.info(f"Bibliography exported to BibTeX: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting bibliography to BibTeX: {e}")
            return False
    
    def _export_bibliography_pdf(self, bibliography: str, filepath: str) -> bool:
        """Export bibliography as PDF"""
        try:
            if PDF_AVAILABLE:
                doc = SimpleDocTemplate(filepath, pagesize=A4,
                                      rightMargin=72, leftMargin=72,
                                      topMargin=72, bottomMargin=18)
                
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'BibTitle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    alignment=TA_CENTER,
                    spaceAfter=30
                )
                normal_style = ParagraphStyle(
                    'BibNormal',
                    parent=styles['Normal'],
                    fontSize=10,
                    spaceBefore=6,
                    spaceAfter=6
                )
                
                story = []
                story.append(Paragraph("Bibliography", title_style))
                story.append(Spacer(1, 12))
                
                # Split bibliography into entries and format each
                entries = bibliography.split('\n\n')
                for entry in entries:
                    if entry.strip():
                        story.append(Paragraph(entry.strip(), normal_style))
                        story.append(Spacer(1, 6))
                
                doc.build(story)
                logger.info(f"Bibliography exported to PDF: {filepath}")
                return True
            else:
                raise ValueError("PDF library not available")
                
        except Exception as e:
            logger.error(f"Error exporting bibliography to PDF: {e}")
            return False
    
    def _export_bibliography_docx(self, bibliography: str, filepath: str) -> bool:
        """Export bibliography as Word document"""
        try:
            doc = Document()
            
            # Title
            title_para = doc.add_heading('Bibliography', level=0)
            title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Bibliography entries
            entries = bibliography.split('\n\n')
            for entry in entries:
                if entry.strip():
                    doc.add_paragraph(entry.strip())
            
            doc.save(filepath)
            logger.info(f"Bibliography exported to Word: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting bibliography to Word: {e}")
            return False
    
    # Formatting helper methods
    def _format_draft_as_markdown(self, draft: Dict[str, Any]) -> str:
        """Format draft as markdown document"""
        md_content = f"# {draft.get('title', 'Research Paper Draft')}\n\n"
        
        # Abstract
        if 'abstract' in draft and draft['abstract']:
            md_content += "## Abstract\n\n"
            md_content += str(draft['abstract']) + "\n\n"
        
        # Introduction
        if 'introduction' in draft and draft['introduction']:
            md_content += "## 1. Introduction\n\n"
            md_content += str(draft['introduction']) + "\n\n"
        
        # Sections
        section_num = 2
        if 'sections' in draft and draft['sections']:
            for key, section in draft['sections'].items():
                if key.startswith('theme_') and isinstance(section, dict):
                    title = section.get('title', f'Section {section_num}')
                    content = section.get('content', 'Content unavailable')
                    md_content += f"## {section_num}. {title}\n\n"
                    md_content += str(content) + "\n\n"
                    section_num += 1
        
        # Discussion
        if 'discussion' in draft and draft['discussion']:
            md_content += f"## {section_num}. Discussion\n\n"
            md_content += str(draft['discussion']) + "\n\n"
            section_num += 1
        
        # Conclusion
        if 'conclusion' in draft and draft['conclusion']:
            md_content += f"## {section_num}. Conclusion\n\n"
            md_content += str(draft['conclusion']) + "\n\n"
        
        # References
        if 'bibliography' in draft and draft['bibliography']:
            md_content += "## References\n\n"
            md_content += str(draft['bibliography']) + "\n\n"
        
        return md_content
    
    def _format_draft_as_latex(self, draft: Dict[str, Any]) -> str:
        """Format draft as LaTeX document"""
        latex_content = """\\documentclass[12pt,a4paper]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[english]{babel}
\\usepackage{amsmath}
\\usepackage{amsfonts}
\\usepackage{amssymb}
\\usepackage{graphicx}
\\usepackage[left=2cm,right=2cm,top=2cm,bottom=2cm]{geometry}
\\usepackage{cite}
\\usepackage{url}

\\title{""" + draft.get('title', 'Research Paper Draft').replace('&', '\\&').replace('_', '\\_') + """}
\\author{Academic Research Assistant}
\\date{\\today}

\\begin{document}

\\maketitle

"""
        
        # Abstract
        if 'abstract' in draft and draft['abstract']:
            latex_content += "\\begin{abstract}\n"
            latex_content += self._escape_latex(str(draft['abstract'])) + "\n"
            latex_content += "\\end{abstract}\n\n"
        
        # Introduction
        if 'introduction' in draft and draft['introduction']:
            latex_content += "\\section{Introduction}\n"
            latex_content += self._escape_latex(str(draft['introduction'])) + "\n\n"
        
        # Sections
        if 'sections' in draft and draft['sections']:
            for key, section in draft['sections'].items():
                if key.startswith('theme_') and isinstance(section, dict):
                    title = section.get('title', 'Section')
                    content = section.get('content', 'Content unavailable')
                    latex_content += f"\\section{{{self._escape_latex(title)}}}\n"
                    latex_content += self._escape_latex(str(content)) + "\n\n"
        
        # Discussion
        if 'discussion' in draft and draft['discussion']:
            latex_content += "\\section{Discussion}\n"
            latex_content += self._escape_latex(str(draft['discussion'])) + "\n\n"
        
        # Conclusion
        if 'conclusion' in draft and draft['conclusion']:
            latex_content += "\\section{Conclusion}\n"
            latex_content += self._escape_latex(str(draft['conclusion'])) + "\n\n"
        
        # References
        if 'bibliography' in draft and draft['bibliography']:
            latex_content += "\\section*{References}\n"
            # Simple bibliography formatting
            bib_entries = str(draft['bibliography']).split('\n\n')
            for entry in bib_entries:
                if entry.strip():
                    latex_content += self._escape_latex(entry.strip()) + "\n\n"
        
        latex_content += "\\end{document}"
        return latex_content
    
    def _format_draft_as_html(self, draft: Dict[str, Any]) -> str:
        """Format draft as HTML document"""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{draft.get('title', 'Research Paper Draft')}</title>
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
        }}
        h1 {{
            text-align: center;
            color: #333;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #444;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        p {{
            text-align: justify;
            margin-bottom: 15px;
        }}
        .abstract {{
            background-color: #f9f9f9;
            padding: 20px;
            border-left: 4px solid #333;
            margin: 20px 0;
        }}
        .references {{
            font-size: 0.9em;
            line-height: 1.4;
        }}
    </style>
</head>
<body>
    <h1>{draft.get('title', 'Research Paper Draft')}</h1>
"""
        
        # Abstract
        if 'abstract' in draft and draft['abstract']:
            html_content += '    <div class="abstract">\n'
            html_content += '        <h2>Abstract</h2>\n'
            html_content += f'        <p>{self._escape_html(str(draft["abstract"]))}</p>\n'
            html_content += '    </div>\n'
        
        # Introduction
        if 'introduction' in draft and draft['introduction']:
            html_content += '    <h2>1. Introduction</h2>\n'
            html_content += f'    <p>{self._escape_html(str(draft["introduction"]))}</p>\n'
        
        # Sections
        section_num = 2
        if 'sections' in draft and draft['sections']:
            for key, section in draft['sections'].items():
                if key.startswith('theme_') and isinstance(section, dict):
                    title = section.get('title', f'Section {section_num}')
                    content = section.get('content', 'Content unavailable')
                    html_content += f'    <h2>{section_num}. {self._escape_html(title)}</h2>\n'
                    html_content += f'    <p>{self._escape_html(str(content))}</p>\n'
                    section_num += 1
        
        # Discussion
        if 'discussion' in draft and draft['discussion']:
            html_content += f'    <h2>{section_num}. Discussion</h2>\n'
            html_content += f'    <p>{self._escape_html(str(draft["discussion"]))}</p>\n'
            section_num += 1
        
        # Conclusion
        if 'conclusion' in draft and draft['conclusion']:
            html_content += f'    <h2>{section_num}. Conclusion</h2>\n'
            html_content += f'    <p>{self._escape_html(str(draft["conclusion"]))}</p>\n'
        
        # References
        if 'bibliography' in draft and draft['bibliography']:
            html_content += '    <h2>References</h2>\n'
            html_content += '    <div class="references">\n'
            bib_entries = str(draft['bibliography']).split('\n\n')
            for entry in bib_entries:
                if entry.strip():
                    html_content += f'        <p>{self._escape_html(entry.strip())}</p>\n'
            html_content += '    </div>\n'
        
        html_content += """</body>
</html>"""
        return html_content
    
    def _format_papers_as_bibtex(self, papers: List[Any]) -> str:
        """Format papers as BibTeX entries"""
        bibtex_entries = []
        header = f"""% Bibliography generated by Academic Research Assistant
% Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
% Total entries: {len(papers)}

"""
        
        for i, paper in enumerate(papers):
            try:
                # Generate citation key
                first_author = ""
                if hasattr(paper, 'authors') and paper.authors:
                    first_author = paper.authors[0].split()[-1] if paper.authors[0] else f"author{i}"
                else:
                    first_author = f"author{i}"
                
                year = ""
                if hasattr(paper, 'published_date') and paper.published_date:
                    year = str(paper.published_date.year)
                else:
                    year = "unknown"
                
                citation_key = f"{first_author.lower()}{year}_{i}"
                
                # Create BibTeX entry
                entry_type = "article"
                if hasattr(paper, 'journal') and not paper.journal:
                    entry_type = "misc"
                
                bibtex_entry = f"@{entry_type}{{{citation_key},\n"
                
                # Title
                if hasattr(paper, 'title') and paper.title:
                    bibtex_entry += f"  title={{{self._escape_bibtex(paper.title)}}},\n"
                
                # Authors
                if hasattr(paper, 'authors') and paper.authors:
                    authors = " and ".join(paper.authors)
                    bibtex_entry += f"  author={{{self._escape_bibtex(authors)}}},\n"
                
                # Journal
                if hasattr(paper, 'journal') and paper.journal:
                    bibtex_entry += f"  journal={{{self._escape_bibtex(paper.journal)}}},\n"
                
                # Year
                if year != "unknown":
                    bibtex_entry += f"  year={{{year}}},\n"
                
                # DOI
                if hasattr(paper, 'doi') and paper.doi:
                    bibtex_entry += f"  doi={{{paper.doi}}},\n"
                
                # URL
                if hasattr(paper, 'url') and paper.url:
                    bibtex_entry += f"  url={{{paper.url}}},\n"
                
                # Abstract
                if hasattr(paper, 'abstract') and paper.abstract:
                    abstract = paper.abstract[:500] + "..." if len(paper.abstract) > 500 else paper.abstract
                    bibtex_entry += f"  abstract={{{self._escape_bibtex(abstract)}}},\n"
                
                # Remove trailing comma and close entry
                bibtex_entry = bibtex_entry.rstrip(',\n') + "\n}\n"
                bibtex_entries.append(bibtex_entry)
                
            except Exception as e:
                logger.warning(f"Error creating BibTeX entry for paper {i}: {e}")
                continue
        
        return header + "\n".join(bibtex_entries)
    
    # Utility methods for escaping special characters
    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters"""
        latex_escapes = {
            '&': '\\&',
            '%': '\\%',
            '$': '\\$',
            '#': '\\#',
            '^': '\\textasciicircum{}',
            '_': '\\_',
            '{': '\\{',
            '}': '\\}',
            '~': '\\textasciitilde{}',
            '\\': '\\textbackslash{}'
        }
        
        result = text
        for char, escape in latex_escapes.items():
            result = result.replace(char, escape)
        return result
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        html_escapes = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;'
        }
        
        result = text
        for char, escape in html_escapes.items():
            result = result.replace(char, escape)
        return result
    
    def _escape_bibtex(self, text: str) -> str:
        """Escape special BibTeX characters"""
        # For BibTeX, we mainly need to handle braces and special characters
        result = text.replace('{', '\\{').replace('}', '\\}')
        return result


# Create global export manager instance
export_manager = ExportManager()
