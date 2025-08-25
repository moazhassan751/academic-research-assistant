import PyPDF2
import pdfplumber
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import hashlib
import mimetypes
from ..utils.config import config
from ..utils.app_logging import logger

class PDFProcessor:
    def __init__(self):
        self.papers_dir = Path(config.get('storage.papers_dir', 'data/papers'))
        self.papers_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.max_file_size = config.get('pdf.max_file_size_mb', 50) * 1024 * 1024  # 50MB default
        self.chunk_size = config.get('pdf.download_chunk_size', 8192)
        self.timeout = config.get('pdf.download_timeout', 30)
        self.min_content_length = config.get('pdf.min_content_length', 100)
    
    def _validate_pdf_file(self, filepath: Path) -> Tuple[bool, str]:
        """Validate PDF file integrity and security"""
        try:
            # Check file size
            if filepath.stat().st_size > self.max_file_size:
                return False, f"File too large: {filepath.stat().st_size / (1024*1024):.1f}MB > {self.max_file_size / (1024*1024)}MB"
            
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(str(filepath))
            if mime_type != 'application/pdf':
                return False, f"Invalid MIME type: {mime_type}"
            
            # Basic PDF header check
            with open(filepath, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    return False, "Invalid PDF header"
            
            return True, "Valid PDF file"
            
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def _calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA-256 hash of file for integrity checking"""
        hash_sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _assess_content_quality(self, text: str) -> Dict[str, Any]:
        """Assess the quality of extracted text content"""
        if not text:
            return {"score": 0, "issues": ["No text extracted"], "readable": False}
        
        issues = []
        score = 100
        
        # Check content length
        if len(text) < self.min_content_length:
            issues.append("Very short content")
            score -= 30
        
        # Check for garbled text (high ratio of special characters)
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if len(text) > 0 and (special_chars / len(text)) > 0.3:
            issues.append("High ratio of special characters - possible OCR issues")
            score -= 25
        
        # Check for repeated characters (scanning artifacts)
        repeated_patterns = len([c for c in text if text.count(c * 3) > 5])
        if repeated_patterns > 10:
            issues.append("Repeated character patterns detected")
            score -= 20
        
        # Check word ratio
        words = text.split()
        if len(words) > 0:
            avg_word_length = sum(len(word) for word in words) / len(words)
            if avg_word_length > 15:  # Very long "words" suggest extraction issues
                issues.append("Unusually long words - possible extraction issues")
                score -= 15
        
        return {
            "score": max(0, score),
            "issues": issues,
            "readable": score > 50,
            "word_count": len(words) if len(text) > 0 else 0,
            "char_count": len(text)
        }

    def download_pdf(self, url: str, filename: str) -> Optional[str]:
        """Download PDF from URL with enhanced validation and progress tracking"""
        try:
            filepath = self.papers_dir / filename
            
            # Check if file already exists and validate it
            if filepath.exists():
                is_valid, message = self._validate_pdf_file(filepath)
                if is_valid:
                    logger.info(f"Valid PDF already exists: {filename}")
                    return str(filepath)
                else:
                    logger.warning(f"Existing PDF invalid ({message}), re-downloading: {filename}")
                    filepath.unlink()  # Remove invalid file
            
            # Download with progress tracking
            logger.info(f"Downloading PDF from: {url}")
            response = requests.get(url, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            # Check content length
            content_length = response.headers.get('content-length')
            if content_length:
                content_length = int(content_length)
                if content_length > self.max_file_size:
                    raise ValueError(f"File too large: {content_length / (1024*1024):.1f}MB")
            
            # Download with progress tracking
            downloaded = 0
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Log progress for large files
                        if content_length and downloaded % (1024*1024) == 0:  # Every MB
                            progress = (downloaded / content_length) * 100
                            logger.info(f"Download progress: {progress:.1f}%")
            
            # Validate downloaded file
            is_valid, message = self._validate_pdf_file(filepath)
            if not is_valid:
                filepath.unlink()  # Remove invalid file
                raise ValueError(f"Downloaded file invalid: {message}")
            
            # Calculate and log file hash for integrity
            file_hash = self._calculate_file_hash(filepath)
            logger.info(f"Downloaded PDF: {filename} (SHA256: {file_hash[:16]}...)")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error downloading PDF {url}: {e}")
            # Clean up partial download
            if 'filepath' in locals() and filepath.exists():
                try:
                    filepath.unlink()
                except:
                    pass
            return None
    
    def extract_text_pypdf2(self, pdf_path: str) -> Optional[str]:
        """Extract text using PyPDF2 with enhanced error handling"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                
                # Check if PDF is encrypted
                if reader.is_encrypted:
                    logger.warning(f"PDF is encrypted, attempting to decrypt: {pdf_path}")
                    try:
                        reader.decrypt("")  # Try with empty password
                    except:
                        logger.error(f"Could not decrypt PDF: {pdf_path}")
                        return None
                
                total_pages = len(reader.pages)
                logger.info(f"Extracting text from {total_pages} pages using PyPDF2")
                
                for i, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                        
                        # Log progress for large documents
                        if i > 0 and i % 10 == 0:
                            logger.info(f"Processed {i}/{total_pages} pages")
                            
                    except Exception as page_error:
                        logger.warning(f"Error extracting page {i+1}: {page_error}")
                        continue
                
                final_text = text.strip()
                logger.info(f"PyPDF2 extraction complete: {len(final_text)} characters")
                return final_text if final_text else None
                
        except Exception as e:
            logger.error(f"Error extracting text with PyPDF2: {e}")
            return None
    
    def extract_text_pdfplumber(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Extract text and metadata using pdfplumber with enhanced features"""
        try:
            result = {
                'text': '',
                'pages': [],
                'tables': [],
                'metadata': {},
                'images': [],
                'quality_assessment': {}
            }
            
            with pdfplumber.open(pdf_path) as pdf:
                result['metadata'] = pdf.metadata or {}
                total_pages = len(pdf.pages)
                logger.info(f"Extracting content from {total_pages} pages using pdfplumber")
                
                total_text = ""
                
                for i, page in enumerate(pdf.pages):
                    try:
                        # Extract text with better error handling
                        page_text = page.extract_text()
                        
                        # Try alternative extraction if primary fails
                        if not page_text or len(page_text.strip()) < 10:
                            try:
                                # Try with different layout parameters
                                page_text = page.extract_text(layout=True)
                            except:
                                pass
                        
                        if page_text:
                            total_text += page_text + "\n"
                            result['pages'].append({
                                'page_number': i + 1,
                                'text': page_text,
                                'char_count': len(page_text),
                                'bbox': page.bbox if hasattr(page, 'bbox') else None
                            })
                        
                        # Extract tables with better error handling
                        try:
                            tables = page.extract_tables()
                            if tables:
                                for j, table in enumerate(tables):
                                    if table and len(table) > 0:
                                        result['tables'].append({
                                            'page_number': i + 1,
                                            'table_number': j + 1,
                                            'table': table,
                                            'rows': len(table),
                                            'columns': len(table[0]) if table[0] else 0
                                        })
                        except Exception as table_error:
                            logger.warning(f"Error extracting tables from page {i+1}: {table_error}")
                        
                        # Extract image information
                        try:
                            if hasattr(page, 'images') and page.images:
                                for img in page.images:
                                    result['images'].append({
                                        'page_number': i + 1,
                                        'bbox': img.get('bbox'),
                                        'width': img.get('width'),
                                        'height': img.get('height')
                                    })
                        except Exception as img_error:
                            logger.warning(f"Error extracting images from page {i+1}: {img_error}")
                        
                        # Log progress for large documents
                        if i > 0 and i % 10 == 0:
                            logger.info(f"Processed {i}/{total_pages} pages")
                            
                    except Exception as page_error:
                        logger.warning(f"Error processing page {i+1}: {page_error}")
                        continue
                
                result['text'] = total_text.strip()
                
                # Assess content quality
                result['quality_assessment'] = self._assess_content_quality(result['text'])
                
                logger.info(f"pdfplumber extraction complete: {len(result['text'])} characters, "
                          f"{len(result['tables'])} tables, {len(result['images'])} images")
                
                return result if result['text'] else None
            
        except Exception as e:
            logger.error(f"Error extracting text with pdfplumber: {e}")
            return None
    
    def process_pdf(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Process PDF and extract comprehensive information with enhanced validation"""
        try:
            pdf_file = Path(pdf_path)
            
            # Validate file exists and is readable
            if not pdf_file.exists():
                logger.error(f"PDF file not found: {pdf_path}")
                return None
            
            # Validate PDF file
            is_valid, validation_message = self._validate_pdf_file(pdf_file)
            if not is_valid:
                logger.error(f"PDF validation failed: {validation_message}")
                return None
            
            logger.info(f"Processing PDF: {pdf_file.name} ({pdf_file.stat().st_size / (1024*1024):.2f}MB)")
            
            # Try pdfplumber first (more comprehensive)
            result = self.extract_text_pdfplumber(pdf_path)
            
            if not result or not result.get('text') or len(result['text'].strip()) < self.min_content_length:
                logger.warning("pdfplumber extraction insufficient, trying PyPDF2 fallback")
                # Fallback to PyPDF2
                text = self.extract_text_pypdf2(pdf_path)
                if text and len(text.strip()) >= self.min_content_length:
                    result = {
                        'text': text,
                        'pages': [],
                        'tables': [],
                        'metadata': {},
                        'images': [],
                        'quality_assessment': self._assess_content_quality(text),
                        'extraction_method': 'PyPDF2'
                    }
                    logger.info("PyPDF2 fallback successful")
                else:
                    logger.error("Both extraction methods failed to produce sufficient content")
                    return None
            else:
                result['extraction_method'] = 'pdfplumber'
            
            # Add processing metadata
            result['processing_info'] = {
                'file_path': str(pdf_path),
                'file_size_mb': pdf_file.stat().st_size / (1024*1024),
                'file_hash': self._calculate_file_hash(pdf_file),
                'processing_timestamp': logger.info.__globals__.get('datetime', type('datetime', (), {'now': lambda: 'unknown'})).now() if 'datetime' in logger.info.__globals__ else 'unknown'
            }
            
            # Final quality check
            quality = result.get('quality_assessment', {})
            if not quality.get('readable', False):
                logger.warning(f"Content quality concerns: {quality.get('issues', [])}")
            
            logger.info(f"PDF processing complete: {len(result['text'])} characters extracted "
                       f"(Quality score: {quality.get('score', 0)}/100)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return None
    
    def get_pdf_info(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Get basic PDF information without full text extraction"""
        try:
            pdf_file = Path(pdf_path)
            
            if not pdf_file.exists():
                return None
            
            # Basic file info
            info = {
                'file_path': str(pdf_path),
                'file_name': pdf_file.name,
                'file_size_mb': pdf_file.stat().st_size / (1024*1024),
                'file_hash': self._calculate_file_hash(pdf_file)
            }
            
            # Try to get PDF metadata
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    info.update({
                        'page_count': len(pdf.pages),
                        'metadata': pdf.metadata or {}
                    })
            except:
                try:
                    with open(pdf_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        info.update({
                            'page_count': len(reader.pages),
                            'metadata': reader.metadata or {},
                            'encrypted': reader.is_encrypted
                        })
                except:
                    pass
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting PDF info for {pdf_path}: {e}")
            return None