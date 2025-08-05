import PyPDF2
import pdfplumber
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from ..utils.config import config
from ..utils.logging import logger

class PDFProcessor:
    def __init__(self):
        self.papers_dir = Path(config.get('storage.papers_dir', 'data/papers'))
        self.papers_dir.mkdir(parents=True, exist_ok=True)
    
    def download_pdf(self, url: str, filename: str) -> Optional[str]:
        """Download PDF from URL"""
        try:
            filepath = self.papers_dir / filename
            
            if filepath.exists():
                logger.info(f"PDF already exists: {filename}")
                return str(filepath)
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded PDF: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error downloading PDF {url}: {e}")
            return None
    
    def extract_text_pypdf2(self, pdf_path: str) -> Optional[str]:
        """Extract text using PyPDF2"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                return text.strip()
                
        except Exception as e:
            logger.error(f"Error extracting text with PyPDF2: {e}")
            return None
    
    def extract_text_pdfplumber(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Extract text and metadata using pdfplumber"""
        try:
            result = {
                'text': '',
                'pages': [],
                'tables': [],
                'metadata': {}
            }
            
            with pdfplumber.open(pdf_path) as pdf:
                result['metadata'] = pdf.metadata or {}
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        result['text'] += page_text + "\n"
                        result['pages'].append({
                            'page_number': i + 1,
                            'text': page_text
                        })
                    
                    # Extract tables if any
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            result['tables'].append({
                                'page_number': i + 1,
                                'table': table
                            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting text with pdfplumber: {e}")
            return None
    
    def process_pdf(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Process PDF and extract comprehensive information"""
        try:
            # Try pdfplumber first (more comprehensive)
            result = self.extract_text_pdfplumber(pdf_path)
            
            if not result or not result.get('text'):
                # Fallback to PyPDF2
                text = self.extract_text_pypdf2(pdf_path)
                if text:
                    result = {
                        'text': text,
                        'pages': [],
                        'tables': [],
                        'metadata': {}
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return None