import arxiv
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..storage.models import Paper
from ..utils.config import config
from ..utils.app_logging import logger

class ArxivTool:
    def __init__(self):
        # Configure the client with reasonable defaults
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=3,
            num_retries=3
        )
        
        self.max_results = config.get('apis.arxiv.max_results', 100)
        self.delay = config.get('apis.arxiv.delay', 3)
        self.timeout = 60  # Total timeout for search operations
        
        # Error tracking
        self.error_counts = {
            'timeouts': 0,
            'connection_errors': 0,
            'parsing_errors': 0,
            'empty_results': 0
        }
    
    def search_papers(self, query: str, max_results: Optional[int] = None, 
                     date_from: Optional[datetime] = None) -> List[Paper]:
        """Search papers on arXiv with enhanced error handling and timeout management"""
        if max_results is None:
            max_results = self.max_results
        
        if not query or not isinstance(query, str) or not query.strip():
            logger.warning("Empty or invalid query provided to ArXiv search")
            return []
        
        # Limit max_results to reasonable bounds
        max_results = min(max_results, 200)  # ArXiv can be slow with large results
        
        try:
            logger.info(f"Starting ArXiv search for: {query} (max: {max_results})")
            
            # Create search with enhanced parameters
            search = arxiv.Search(
                query=query.strip(),
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            papers = []
            results_processed = 0
            start_time = time.time()
            
            # Process results with timeout and error handling
            try:
                for result in self.client.results(search):
                    # Check timeout
                    if time.time() - start_time > self.timeout:
                        logger.warning(f"ArXiv search timeout after {self.timeout}s, processed {results_processed} papers")
                        break
                    
                    # Filter by date if specified
                    if date_from and result.published:
                        try:
                            # Handle timezone-aware vs naive datetime comparison
                            pub_date = result.published
                            if pub_date.tzinfo is not None and date_from.tzinfo is None:
                                # Convert naive date_from to UTC for comparison
                                from datetime import timezone
                                date_from = date_from.replace(tzinfo=timezone.utc)
                            elif pub_date.tzinfo is None and date_from.tzinfo is not None:
                                # Convert timezone-aware date_from to naive for comparison
                                date_from = date_from.replace(tzinfo=None)
                            
                            if pub_date < date_from:
                                continue
                        except Exception as e:
                            logger.debug(f"Date comparison error, skipping date filter: {e}")
                            # Continue without date filtering for this paper
                    
                    # Enhanced metadata extraction with error handling
                    try:
                        paper = self._extract_paper_metadata(result)
                        if paper:
                            papers.append(paper)
                            results_processed += 1
                            
                            # Log progress for long searches
                            if results_processed % 10 == 0:
                                logger.debug(f"ArXiv: processed {results_processed} papers...")
                            
                    except Exception as e:
                        self.error_counts['parsing_errors'] += 1
                        logger.debug(f"Error parsing ArXiv result: {e}")
                        continue
                    
                    # Respect rate limiting with adaptive delay
                    if results_processed % 5 == 0:  # Every 5 results
                        time.sleep(self.delay * 0.5)  # Reduce delay for efficiency
                
            except arxiv.UnexpectedEmptyPageError as e:
                logger.warning(f"ArXiv returned empty page: {e}")
                self.error_counts['empty_results'] += 1
                
            except arxiv.HTTPError as e:
                logger.error(f"ArXiv HTTP error: {e}")
                self.error_counts['connection_errors'] += 1
                
            except Exception as e:
                logger.error(f"Unexpected ArXiv error: {e}")
                self.error_counts['connection_errors'] += 1
            
            elapsed_time = time.time() - start_time
            logger.info(f"ArXiv search completed: {len(papers)} papers found in {elapsed_time:.2f}s")
            return papers
            
        except Exception as e:
            logger.error(f"Error in ArXiv search setup: {e}")
            self.error_counts['connection_errors'] += 1
            return []
    
    def _extract_paper_metadata(self, result) -> Optional[Paper]:
        """Extract comprehensive metadata from arXiv result with enhanced validation"""
        try:
            # Validate input
            if not result:
                return None
            
            # Extract arXiv ID with validation
            arxiv_id = None
            try:
                if hasattr(result, 'entry_id') and result.entry_id:
                    arxiv_id = result.entry_id.split('/')[-1]
                    arxiv_id = arxiv_id.replace('abs/', '').replace('pdf/', '')
                    arxiv_id = arxiv_id.replace('.pdf', '')
                    
                    # Validate arXiv ID format
                    if not arxiv_id or len(arxiv_id) < 5:
                        logger.debug("Invalid arXiv ID extracted")
                        return None
                        
            except Exception as e:
                logger.debug(f"Error extracting arXiv ID: {e}")
                return None
            
            # Clean and validate title
            title = ""
            try:
                if hasattr(result, 'title') and result.title:
                    title = result.title.strip()
                    # Clean common artifacts
                    title = ' '.join(title.split())  # Normalize whitespace
                    
                    if not title or len(title) < 5:
                        logger.debug(f"Invalid title for arXiv paper {arxiv_id}: '{title}'")
                        return None
                        
            except Exception as e:
                logger.debug(f"Error extracting title for {arxiv_id}: {e}")
                return None
            
            # Extract authors with proper formatting and validation
            authors = []
            try:
                if hasattr(result, 'authors') and result.authors:
                    for author in result.authors:
                        try:
                            author_name = str(author).strip()
                            if (author_name and 
                                author_name not in authors and 
                                len(author_name) >= 2 and
                                not author_name.isdigit()):
                                authors.append(author_name)
                        except Exception:
                            continue
                    
                # Limit authors to reasonable number
                authors = authors[:50]
                
            except Exception as e:
                logger.debug(f"Error extracting authors for {arxiv_id}: {e}")
            
            # Clean abstract with validation
            abstract = ""
            try:
                if hasattr(result, 'summary') and result.summary:
                    abstract = result.summary.strip()
                    abstract = ' '.join(abstract.split())  # Normalize whitespace
                    
                    # Validate abstract length and content
                    if len(abstract) > 5000:  # Truncate very long abstracts
                        abstract = abstract[:5000] + "..."
                    elif len(abstract) < 20:
                        abstract = "Abstract not available"
                else:
                    abstract = "Abstract not available"
                    
            except Exception as e:
                logger.debug(f"Error extracting abstract for {arxiv_id}: {e}")
                abstract = "Abstract not available"
            
            # Extract and validate publication date
            pub_date = None
            try:
                if hasattr(result, 'published') and result.published:
                    pub_date = result.published
                    
                    # Validate date range
                    current_year = datetime.now().year
                    if (pub_date.year < 1990 or pub_date.year > current_year + 1):
                        logger.debug(f"Invalid publication date for {arxiv_id}: {pub_date}")
                        pub_date = None
                        
            except Exception as e:
                logger.debug(f"Error extracting publication date for {arxiv_id}: {e}")
            
            # Extract subject categories with validation
            categories = []
            venue = "arXiv"
            try:
                if hasattr(result, 'categories') and result.categories:
                    categories = [cat.strip() for cat in result.categories if cat.strip()]
                    venue = self._determine_venue_from_categories(categories)
                    
            except Exception as e:
                logger.debug(f"Error extracting categories for {arxiv_id}: {e}")
            
            # Extract DOI with validation
            doi = None
            try:
                if hasattr(result, 'doi') and result.doi:
                    doi_str = result.doi.strip()
                    if doi_str and '/' in doi_str and len(doi_str) >= 7:
                        doi = doi_str
                        
            except Exception as e:
                logger.debug(f"Error extracting DOI for {arxiv_id}: {e}")
            
            # Generate URLs with validation
            entry_url = None
            pdf_url = None
            try:
                if hasattr(result, 'entry_id') and result.entry_id:
                    entry_url = result.entry_id
                    
                if hasattr(result, 'pdf_url') and result.pdf_url:
                    pdf_url = result.pdf_url
                elif entry_url:
                    pdf_url = entry_url.replace('/abs/', '/pdf/') + '.pdf'
                    
            except Exception as e:
                logger.debug(f"Error generating URLs for {arxiv_id}: {e}")
            
            # Create paper object with comprehensive validation
            try:
                paper = Paper(
                    id=f"arxiv_{arxiv_id}",
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=entry_url or f"https://arxiv.org/abs/{arxiv_id}",
                    published_date=pub_date,
                    venue=venue,
                    citations=0,  # ArXiv doesn't provide citation counts
                    doi=doi,
                    created_at=datetime.now()
                )
                
                # Add arXiv-specific metadata
                paper.source = 'arxiv'
                paper.arxiv_id = arxiv_id
                paper.categories = categories
                paper.pdf_url = pdf_url
                
                # Final validation
                if not paper.title or len(paper.title.strip()) < 5:
                    logger.debug(f"Paper created but has invalid title: {arxiv_id}")
                    return None
                
                logger.debug(f"Successfully created ArXiv paper: {title[:50]}... (ID: {arxiv_id})")
                return paper
                
            except Exception as e:
                logger.error(f"Error creating Paper object for ArXiv ID {arxiv_id}: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Unexpected error extracting ArXiv metadata: {e}")
            return None
    
    def _determine_venue_from_categories(self, categories: List[str]) -> str:
        """Determine appropriate venue name from arXiv categories with enhanced mapping"""
        if not categories:
            return "arXiv"
        
        # Enhanced category mapping with more comprehensive coverage
        category_map = {
            # Computer Science
            'cs.AI': 'arXiv:cs.AI (Artificial Intelligence)',
            'cs.CL': 'arXiv:cs.CL (Computation and Language)',
            'cs.CV': 'arXiv:cs.CV (Computer Vision and Pattern Recognition)',
            'cs.LG': 'arXiv:cs.LG (Machine Learning)',
            'cs.RO': 'arXiv:cs.RO (Robotics)',
            'cs.SE': 'arXiv:cs.SE (Software Engineering)',
            'cs.NE': 'arXiv:cs.NE (Neural and Evolutionary Computing)',
            'cs.IR': 'arXiv:cs.IR (Information Retrieval)',
            'cs.HC': 'arXiv:cs.HC (Human-Computer Interaction)',
            'cs.CR': 'arXiv:cs.CR (Cryptography and Security)',
            'cs.DC': 'arXiv:cs.DC (Distributed, Parallel, and Cluster Computing)',
            'cs.DS': 'arXiv:cs.DS (Data Structures and Algorithms)',
            
            # Statistics and Machine Learning
            'stat.ML': 'arXiv:stat.ML (Machine Learning)',
            'stat.AP': 'arXiv:stat.AP (Applications)',
            'stat.CO': 'arXiv:stat.CO (Computation)',
            'stat.ME': 'arXiv:stat.ME (Methodology)',
            
            # Mathematics
            'math.OC': 'arXiv:math.OC (Optimization and Control)',
            'math.ST': 'arXiv:math.ST (Statistics Theory)',
            'math.PR': 'arXiv:math.PR (Probability)',
            'math.NA': 'arXiv:math.NA (Numerical Analysis)',
            
            # Engineering
            'eess.AS': 'arXiv:eess.AS (Audio and Speech Processing)',
            'eess.IV': 'arXiv:eess.IV (Image and Video Processing)',
            'eess.SP': 'arXiv:eess.SP (Signal Processing)',
            'eess.SY': 'arXiv:eess.SY (Systems and Control)',
            
            # Physics
            'physics.data-an': 'arXiv:physics.data-an (Data Analysis)',
            'physics.comp-ph': 'arXiv:physics.comp-ph (Computational Physics)',
            'cond-mat.dis-nn': 'arXiv:cond-mat.dis-nn (Disordered Systems and Neural Networks)',
            
            # Biology
            'q-bio.QM': 'arXiv:q-bio.QM (Quantitative Methods)',
            'q-bio.NC': 'arXiv:q-bio.NC (Neurons and Cognition)',
            'q-bio.GN': 'arXiv:q-bio.GN (Genomics)',
        }
        
        primary_category = categories[0] if categories else ""
        
        # Try exact match first
        if primary_category in category_map:
            return category_map[primary_category]
        
        # Try partial matches for subcategories
        for cat, venue in category_map.items():
            if primary_category.startswith(cat.split('.')[0]):
                return venue
        
        # Handle general categories
        if primary_category.startswith('cs.'):
            return f"arXiv:cs (Computer Science) - {primary_category}"
        elif primary_category.startswith('stat.'):
            return f"arXiv:stat (Statistics) - {primary_category}"
        elif primary_category.startswith('math.'):
            return f"arXiv:math (Mathematics) - {primary_category}"
        elif primary_category.startswith('eess.'):
            return f"arXiv:eess (Electrical Engineering) - {primary_category}"
        elif primary_category.startswith('physics.'):
            return f"arXiv:physics (Physics) - {primary_category}"
        elif primary_category.startswith('q-bio.'):
            return f"arXiv:q-bio (Quantitative Biology) - {primary_category}"
        
        # Default fallback
        return f"arXiv:{primary_category}" if primary_category else "arXiv"
    
    def get_paper_by_id(self, arxiv_id: str) -> Optional[Paper]:
        """Get a specific paper by arXiv ID with enhanced error handling"""
        if not arxiv_id or not isinstance(arxiv_id, str):
            logger.warning("Invalid arXiv ID provided to get_paper_by_id")
            return None
        
        try:
            # Clean arXiv ID
            clean_id = arxiv_id.replace('arxiv_', '').strip()
            
            if not clean_id or len(clean_id) < 5:
                logger.warning(f"Invalid arXiv ID format: {arxiv_id}")
                return None
            
            logger.info(f"Fetching ArXiv paper by ID: {clean_id}")
            
            search = arxiv.Search(id_list=[clean_id])
            
            try:
                results = list(self.client.results(search))
                
                if not results:
                    logger.warning(f"No paper found for arXiv ID: {clean_id}")
                    return None
                
                result = results[0]
                return self._extract_paper_metadata(result)
                
            except arxiv.UnexpectedEmptyPageError:
                logger.warning(f"ArXiv returned empty page for ID: {clean_id}")
                return None
                
            except Exception as e:
                logger.error(f"Error fetching ArXiv paper {clean_id}: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Error in get_paper_by_id for {arxiv_id}: {e}")
            return None
    
    def search_by_author(self, author_name: str, max_results: int = 50) -> List[Paper]:
        """Search papers by author name with enhanced query construction"""
        if not author_name or not isinstance(author_name, str) or not author_name.strip():
            logger.warning("Invalid author name provided to search_by_author")
            return []
        
        try:
            # Create author-specific query with better formatting
            author_clean = author_name.strip()
            
            # Try multiple query formats for better recall
            queries = [
                f'au:"{author_clean}"',  # Exact author name
                f'au:{author_clean}',    # Author name without quotes
            ]
            
            # If name has multiple parts, try variations
            name_parts = author_clean.split()
            if len(name_parts) >= 2:
                last_name = name_parts[-1]
                first_names = ' '.join(name_parts[:-1])
                queries.append(f'au:"{last_name}, {first_names}"')  # Last, First format
            
            all_papers = []
            
            for query in queries[:2]:  # Limit to first 2 queries to avoid duplicates
                try:
                    logger.info(f"Searching ArXiv by author with query: {query}")
                    
                    search = arxiv.Search(
                        query=query,
                        max_results=max_results,
                        sort_by=arxiv.SortCriterion.SubmittedDate,
                        sort_order=arxiv.SortOrder.Descending
                    )
                    
                    papers = []
                    for result in self.client.results(search):
                        paper = self._extract_paper_metadata(result)
                        if paper:
                            papers.append(paper)
                        
                        # Rate limiting
                        time.sleep(self.delay * 0.5)
                    
                    all_papers.extend(papers)
                    
                    # If we got good results from first query, don't need others
                    if len(papers) >= max_results // 2:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error with author query '{query}': {e}")
                    continue
            
            # Remove duplicates based on arXiv ID
            unique_papers = []
            seen_ids = set()
            
            for paper in all_papers:
                if hasattr(paper, 'arxiv_id') and paper.arxiv_id:
                    if paper.arxiv_id not in seen_ids:
                        seen_ids.add(paper.arxiv_id)
                        unique_papers.append(paper)
                else:
                    unique_papers.append(paper)
            
            # Limit results
            unique_papers = unique_papers[:max_results]
            
            logger.info(f"Found {len(unique_papers)} unique papers by author: {author_name}")
            return unique_papers
            
        except Exception as e:
            logger.error(f"Error searching by author on arXiv: {e}")
            return []
    
    def get_recent_papers(self, category: str = None, days: int = 30, 
                         max_results: int = 100) -> List[Paper]:
        """Get recent papers from arXiv with enhanced category handling"""
        try:
            date_from = datetime.now() - timedelta(days=days)
            
            # Construct query based on category
            if category:
                # Validate and clean category
                category_clean = category.strip().lower()
                
                # Handle common category formats
                if not category_clean.startswith('cat:'):
                    if '.' in category_clean:
                        query = f"cat:{category_clean}"
                    else:
                        # Assume it's a major category like 'cs', 'stat', etc.
                        query = f"cat:{category_clean}.*"
                else:
                    query = category_clean
            else:
                # Search multiple relevant categories for general AI/ML
                categories = ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV', 'stat.ML']
                query = ' OR '.join([f'cat:{cat}' for cat in categories])
            
            logger.info(f"Getting recent ArXiv papers with query: {query}")
            return self.search_papers(query, max_results, date_from)
            
        except Exception as e:
            logger.error(f"Error getting recent papers: {e}")
            return []
    
    def validate_metadata(self, paper: Paper) -> Dict[str, Any]:
        """Validate and report metadata quality with enhanced checks"""
        try:
            validation = {
                'title': bool(paper.title and paper.title.strip() and len(paper.title.strip()) >= 5),
                'authors': bool(paper.authors and len(paper.authors) > 0),
                'abstract': bool(paper.abstract and len(paper.abstract.strip()) > 50),
                'date': bool(paper.published_date),
                'venue': bool(paper.venue and paper.venue != 'arXiv'),
                'arxiv_id': bool(hasattr(paper, 'arxiv_id') and paper.arxiv_id),
                'url': bool(paper.url and paper.url.startswith('http')),
                'categories': bool(hasattr(paper, 'categories') and paper.categories)
            }
            
            # Calculate completeness score
            validation['completeness_score'] = sum(validation.values()) / len(validation)
            
            # Add quality indicators
            validation['title_length'] = len(paper.title) if paper.title else 0
            validation['author_count'] = len(paper.authors) if paper.authors else 0
            validation['abstract_length'] = len(paper.abstract) if paper.abstract else 0
            
            # Check for common quality issues
            validation['issues'] = []
            
            if validation['title_length'] < 10:
                validation['issues'].append('Very short title')
            if validation['author_count'] == 0:
                validation['issues'].append('No authors listed')
            if validation['abstract_length'] < 100:
                validation['issues'].append('Very short abstract')
            if not validation['date']:
                validation['issues'].append('Missing publication date')
            
            return validation
            
        except Exception as e:
            logger.error(f"Error validating metadata: {e}")
            return {'completeness_score': 0.0, 'issues': ['Validation failed']}
    
    def get_error_statistics(self) -> Dict[str, int]:
        """Get error statistics for monitoring"""
        return self.error_counts.copy()
    
    def reset_error_statistics(self):
        """Reset error statistics"""
        self.error_counts = {
            'timeouts': 0,
            'connection_errors': 0,
            'parsing_errors': 0,
            'empty_results': 0
        }