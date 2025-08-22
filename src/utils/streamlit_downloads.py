"""
Streamlit Download Extensions for Export Manager
Safe additions that work alongside existing export functionality
"""

import streamlit as st
import io
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class StreamlitDownloadHelper:
    """
    Helper class for Streamlit download functionality
    Works with existing ExportManager without modifying it
    """
    
    def __init__(self, export_manager):
        """Initialize with existing export manager instance"""
        self.export_manager = export_manager
        
    def create_download_button_pdf(self, draft: Dict[str, Any], filename: str = None) -> bool:
        """
        Create a download button for PDF export
        Returns True if download button was clicked
        """
        try:
            if filename is None:
                timestamp = st.session_state.get('timestamp', 'export')
                filename = f"research_draft_{timestamp}.pdf"
            
            # Generate PDF using existing export manager
            import tempfile
            import os
            
            # Create temporary file with proper Windows path
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                temp_path = tmp.name
            
            # Use existing export function (doesn't modify it)
            success = self.export_manager.export_draft(draft, temp_path.replace('.pdf', ''), format="pdf")
            
            # Check both with and without extension
            final_path = temp_path if os.path.exists(temp_path) else temp_path.replace('.pdf', '') + '.pdf'
            
            if success and os.path.exists(final_path):
                # Read the generated file
                with open(final_path, 'rb') as f:
                    pdf_data = f.read()
                
                # Cleanup temp file
                try:
                    os.unlink(final_path)
                except:
                    pass
                
                # Create download button
                return st.download_button(
                    label="📄 Download PDF Report",
                    data=pdf_data,
                    file_name=filename,
                    mime="application/pdf",
                    help="Click to download your research report as PDF"
                )
            else:
                st.error("❌ Failed to generate PDF")
                return False
                
        except Exception as e:
            logger.error(f"PDF download error: {e}")
            st.error(f"❌ PDF generation failed: {str(e)}")
            return False
    
    def create_download_button_docx(self, draft: Dict[str, Any], filename: str = None) -> bool:
        """
        Create a download button for Word document export
        Returns True if download button was clicked
        """
        try:
            if filename is None:
                timestamp = st.session_state.get('timestamp', 'export')
                filename = f"research_draft_{timestamp}.docx"
            
            # Create temporary file with proper Windows path
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
                temp_path = tmp.name
            
            # Use existing export function (doesn't modify it)
            success = self.export_manager.export_draft(draft, temp_path.replace('.docx', ''), format="docx")
            
            # Check both with and without extension
            final_path = temp_path if os.path.exists(temp_path) else temp_path.replace('.docx', '') + '.docx'
            
            if success and os.path.exists(final_path):
                # Read the generated file
                with open(final_path, 'rb') as f:
                    docx_data = f.read()
                
                # Cleanup temp file
                try:
                    os.unlink(final_path)
                except:
                    pass
                
                # Create download button
                return st.download_button(
                    label="📝 Download Word Document",
                    data=docx_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    help="Click to download your research report as Word document"
                )
            else:
                st.error("❌ Failed to generate Word document")
                return False
                
        except Exception as e:
            logger.error(f"DOCX download error: {e}")
            st.error(f"❌ Word document generation failed: {str(e)}")
            return False
    
    def create_download_button_bibliography(self, bibliography: str, papers: List[Any], 
                                          format: str = "bibtex", filename: str = None) -> bool:
        """
        Create a download button for bibliography export
        Returns True if download button was clicked
        """
        try:
            if filename is None:
                timestamp = st.session_state.get('timestamp', 'export')
                filename = f"bibliography_{timestamp}.{format}"
            
            # Create temporary file with proper Windows path
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix=f'.{format}', delete=False) as tmp:
                temp_path = tmp.name
            
            # Use existing export function (doesn't modify it)
            success = self.export_manager.export_bibliography(bibliography, papers, temp_path.replace(f'.{format}', ''), format)
            
            # Check both with and without extension
            final_path = temp_path if os.path.exists(temp_path) else temp_path.replace(f'.{format}', '') + f'.{format}'
            
            if success and os.path.exists(final_path):
                # Read the generated file
                with open(final_path, 'r', encoding='utf-8') as f:
                    bib_data = f.read()
                
                # Cleanup temp file
                try:
                    os.unlink(final_path)
                except:
                    pass
                
                # Determine MIME type
                mime_types = {
                    'bibtex': 'text/plain',
                    'ris': 'application/x-research-info-systems',
                    'csv': 'text/csv',
                    'json': 'application/json'
                }
                mime_type = mime_types.get(format, 'text/plain')
                
                # Create download button
                return st.download_button(
                    label=f"📚 Download Bibliography ({format.upper()})",
                    data=bib_data,
                    file_name=filename,
                    mime=mime_type,
                    help=f"Click to download your bibliography as {format.upper()}"
                )
            else:
                st.error("❌ Failed to generate bibliography")
                return False
                
        except Exception as e:
            logger.error(f"Bibliography download error: {e}")
            st.error(f"❌ Bibliography generation failed: {str(e)}")
            return False
    
    def create_text_preview(self, content: str, max_lines: int = 20):
        """
        Create a text preview with copy button
        Safe preview functionality
        """
        try:
            lines = content.split('\n')
            preview_lines = lines[:max_lines]
            preview_text = '\n'.join(preview_lines)
            
            if len(lines) > max_lines:
                preview_text += f"\n\n... ({len(lines) - max_lines} more lines)"
            
            st.text_area(
                "📄 Preview",
                value=preview_text,
                height=300,
                help="Preview of your exported content"
            )
            
            # Copy button (text content)
            st.download_button(
                label="📋 Download as Text",
                data=content,
                file_name="research_content.txt",
                mime="text/plain",
                help="Download the full content as text file"
            )
            
        except Exception as e:
            logger.error(f"Preview error: {e}")
            st.error("❌ Failed to create preview")

# Convenience function for easy integration
def add_download_buttons(export_manager, draft: Dict[str, Any] = None, 
                        bibliography: str = None, papers: List[Any] = None):
    """
    Convenience function to add download buttons to any Streamlit page
    Safe integration with existing export manager
    """
    if not export_manager:
        st.warning("⚠️ Export manager not available")
        return
    
    helper = StreamlitDownloadHelper(export_manager)
    
    if draft:
        st.subheader("📄 Export Research Draft")
        col1, col2 = st.columns(2)
        
        with col1:
            if helper.create_download_button_pdf(draft):
                st.success("✅ PDF download initiated!")
        
        with col2:
            if helper.create_download_button_docx(draft):
                st.success("✅ Word document download initiated!")
    
    if bibliography and papers:
        st.subheader("📚 Export Bibliography")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if helper.create_download_button_bibliography(bibliography, papers, "bibtex"):
                st.success("✅ BibTeX download initiated!")
        
        with col2:
            if helper.create_download_button_bibliography(bibliography, papers, "ris"):
                st.success("✅ RIS download initiated!")
        
        with col3:
            if helper.create_download_button_bibliography(bibliography, papers, "csv"):
                st.success("✅ CSV download initiated!")
