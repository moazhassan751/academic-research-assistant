import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from ..storage.models import Paper
from ..utils.logging import logger
from ..utils.config import config

class OpenAlexTool:
    def __init__(self, mailto: str = None):
        self.base_url = "https://api.openalex.org/works"
        self.rate_limit_delay = 0.1  # OpenAlex allows up to 10 requests per second
        self.last_request_time = 0
        self.session = requests.Session()
        
        # Use provided email or get from config
        self.mailto = mailto or config.get('apis.crossref.mailto', 'rmoazhassan555@gmail.com')
        
        # Set user agent for politeness - include email for better rate limits
        self.session.headers.update({
            'User-Agent': f'AcademicResearchAssistant/1.0 (mailto:{self.mailto})'
        })
        
        logger.info(f"OpenAlex tool initialized with email: {self.mailto}")
    
    def _rate_limit(self):
        """Implement rate limiting to be respectful to the API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def search_papers(self, query: str, max_results: int = 50, 
                     date_from: Optional[datetime] = None) -> List[Paper]:
        """Search papers using OpenAlex API"""
        papers = []
        
        try:
            # Prepare search parameters
            params = {
                'search': query,
                'per-page': min(max_results, 200),  # OpenAlex max is 200 per page
                'sort': 'cited_by_count:desc',
                'select': 'id,title,authorships,abstract_inverted_index,publication_date,primary_location,cited_by_count,doi,type,open_access',
                'mailto': self.mailto
            }
            
            # Add date filter if specified
            if date_from:
                date_str = date_from.strftime('%Y-%m-%d')
                params['filter'] = f'publication_date:>{date_str}'
            
            logger.info(f"Searching OpenAlex for: {query} (max: {max_results})")
            logger.info(f"Request URL: {self.base_url}")
            logger.debug(f"Request params: {params}")
            
            # Make request with rate limiting
            self._rate_limit()
            response = self.session.get(self.base_url, params=params, timeout=30)
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 429:
                logger.warning("Rate limit exceeded, waiting longer...")
                time.sleep(2)  # Wait 2 seconds and retry
                response = self.session.get(self.base_url, params=params, timeout=30)
            
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Response meta: {data.get('meta', {})}")
            results = data.get('results', [])
            logger.info(f"Results count: {len(results)}")
            
            if not results:
                logger.warning("No results field in OpenAlex response or empty results")
                logger.debug(f"Response data keys: {list(data.keys())}")
                return papers
            
            # Process results with detailed error tracking
            successful_parses = 0
            failed_parses = 0
            
            for i, item in enumerate(results[:max_results]):
                try:
                    logger.debug(f"Parsing paper {i+1}/{len(results)}")
                    paper = self.parse_paper(item)
                    if paper:
                        papers.append(paper)
                        successful_parses += 1
                        logger.debug(f"Successfully parsed: {paper.title[:50]}...")
                    else:
                        failed_parses += 1
                        logger.debug(f"Parse returned None for item {i+1}")
                except Exception as e:
                    failed_parses += 1
                    logger.error(f"Error parsing paper {i+1}: {e}")
                    logger.debug(f"Failed item keys: {list(item.keys()) if isinstance(item, dict) else 'Not a dict'}")
                    continue
            
            logger.info(f"Retrieved {len(papers)} papers from OpenAlex (successful: {successful_parses}, failed: {failed_parses})")
            
            # Log specific parsing issues if no papers retrieved
            if len(papers) == 0 and len(results) > 0:
                logger.warning("No papers successfully parsed despite having results!")
                logger.debug(f"First result sample: {results[0] if results else 'None'}")
            
        except requests.exceptions.Timeout:
            logger.error("OpenAlex API request timed out")
        except requests.exceptions.ConnectionError:
            logger.error("Connection error to OpenAlex API")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error from OpenAlex API: {e}")
            if hasattr(e, 'response') and e.response:
                logger.debug(f"Error response: {e.response.text[:500]}")
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAlex API request failed: {e}")
        except ValueError as e:
            logger.error(f"JSON decode error from OpenAlex response: {e}")
            if 'response' in locals():
                logger.debug(f"Response text: {response.text[:500]}")
        except Exception as e:
            logger.error(f"Unexpected error in OpenAlex search: {e}")
            logger.debug(f"Response text: {response.text[:500] if 'response' in locals() else 'No response'}")
        
        return papers
    
    def parse_paper(self, item: Dict[str, Any]) -> Optional[Paper]:
        """Parse OpenAlex paper data into Paper model with robust error handling"""
        try:
            # Validate input
            if not isinstance(item, dict):
                logger.debug(f"Item is not a dictionary: {type(item)}")
                return None
            
            if not item:
                logger.debug("Empty item received")
                return None
            
            # Extract and validate OpenAlex ID
            openalex_id = ''
            raw_id = item.get('id')
            
            if not raw_id:
                logger.debug("No ID found in item")
                return None
            
            if isinstance(raw_id, str):
                if '/' in raw_id:
                    openalex_id = raw_id.split('/')[-1]
                else:
                    openalex_id = raw_id
            else:
                openalex_id = str(raw_id)
            
            if not openalex_id or openalex_id == 'None':
                logger.debug(f"Invalid OpenAlex ID: '{openalex_id}'")
                return None
            
            # Extract and validate title
            title = item.get('title')
            if not title:
                logger.debug(f"No title found for paper {openalex_id}")
                return None
            
            if isinstance(title, str):
                title = title.strip()
            else:
                title = str(title).strip()
            
            if not title or title.lower() in ['none', 'null', '']:
                logger.debug(f"Invalid title for paper {openalex_id}: '{title}'")
                return None
            
            # Extract authors with improved error handling
            authors = []
            try:
                authorships = item.get('authorships', [])
                if isinstance(authorships, list):
                    for authorship in authorships:
                        if not isinstance(authorship, dict):
                            continue
                        
                        author = authorship.get('author', {})
                        if not isinstance(author, dict):
                            continue
                        
                        display_name = author.get('display_name')
                        if display_name and isinstance(display_name, str):
                            clean_name = display_name.strip()
                            if clean_name and clean_name.lower() not in ['none', 'null', '']:
                                authors.append(clean_name)
            except Exception as e:
                logger.debug(f"Error parsing authors for {openalex_id}: {e}")
            
            # Extract abstract with improved handling
            abstract = ""
            try:
                abstract_index = item.get('abstract_inverted_index')
                if abstract_index and isinstance(abstract_index, dict):
                    abstract = self._reconstruct_abstract(abstract_index)
                
                if not abstract:
                    # Try alternative abstract field
                    alt_abstract = item.get('abstract')
                    if alt_abstract and isinstance(alt_abstract, str):
                        abstract = alt_abstract.strip()
            except Exception as e:
                logger.debug(f"Error parsing abstract for {openalex_id}: {e}")
            
            if not abstract:
                abstract = "Abstract not available"
            
            # Extract publication date with multiple fallbacks
            pub_date = None
            try:
                pub_date_str = item.get('publication_date')
                if pub_date_str and isinstance(pub_date_str, str):
                    try:
                        pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d')
                    except ValueError:
                        try:
                            # Try year only
                            year_str = pub_date_str[:4]
                            if year_str.isdigit():
                                pub_date = datetime.strptime(year_str, '%Y')
                        except ValueError:
                            logger.debug(f"Could not parse date: {pub_date_str}")
            except Exception as e:
                logger.debug(f"Error parsing publication date for {openalex_id}: {e}")
            
            # Extract venue information with error handling
            venue = None
            try:
                primary_location = item.get('primary_location')
                if isinstance(primary_location, dict):
                    source = primary_location.get('source')
                    if isinstance(source, dict):
                        venue_name = source.get('display_name')
                        if venue_name and isinstance(venue_name, str):
                            venue = venue_name.strip()
                            if venue.lower() in ['none', 'null', '']:
                                venue = None
            except Exception as e:
                logger.debug(f"Error parsing venue for {openalex_id}: {e}")
            
            # Extract citations with validation
            citations = 0
            try:
                citation_count = item.get('cited_by_count', 0)
                if isinstance(citation_count, (int, float)):
                    citations = int(citation_count)
                elif isinstance(citation_count, str) and citation_count.isdigit():
                    citations = int(citation_count)
                else:
                    citations = 0
            except (ValueError, TypeError) as e:
                logger.debug(f"Error parsing citations for {openalex_id}: {e}")
                citations = 0
            
            # Handle DOI with validation
            doi = None
            try:
                raw_doi = item.get('doi')
                if raw_doi and isinstance(raw_doi, str):
                    clean_doi = raw_doi.replace('https://doi.org/', '').strip()
                    if clean_doi and clean_doi.lower() not in ['none', 'null', '']:
                        doi = clean_doi
            except Exception as e:
                logger.debug(f"Error parsing DOI for {openalex_id}: {e}")
            
            # Generate URL with fallback
            url = None
            try:
                if raw_id and isinstance(raw_id, str):
                    url = raw_id
                else:
                    url = f"https://openalex.org/W{openalex_id}"
            except Exception as e:
                logger.debug(f"Error generating URL for {openalex_id}: {e}")
                url = f"https://openalex.org/W{openalex_id}"
            
            # Create Paper object with validation
            try:
                paper = Paper(
                    id=f"openalex_{openalex_id}",
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=url,
                    published_date=pub_date,
                    venue=venue,
                    citations=citations,
                    doi=doi,
                    created_at=datetime.now()
                )
                
                # Add source tracking
                paper.source = 'openalex'
                
                # Validate the paper object
                if not paper.title or paper.title.strip() == '':
                    logger.debug(f"Paper created but has empty title: {openalex_id}")
                    return None
                
                logger.debug(f"Successfully created paper: {title[:50]}... (ID: {openalex_id})")
                return paper
                
            except Exception as e:
                logger.error(f"Error creating Paper object for {openalex_id}: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Unexpected error parsing OpenAlex paper: {e}")
            logger.debug(f"Problem item type: {type(item)}")
            if isinstance(item, dict):
                logger.debug(f"Problem item keys: {list(item.keys())}")
            return None
    
    def _reconstruct_abstract(self, inverted_index: Dict[str, List[int]]) -> str:
        """Reconstruct abstract text from OpenAlex inverted index with improved error handling"""
        if not inverted_index or not isinstance(inverted_index, dict):
            return ""
        
        try:
            # Create list of (position, word) tuples
            word_positions = []
            
            for word, positions in inverted_index.items():
                # Skip invalid entries
                if not word or not isinstance(word, str):
                    continue
                if not positions or not isinstance(positions, list):
                    continue
                
                # Clean the word
                clean_word = word.strip()
                if not clean_word:
                    continue
                
                # Process positions
                for pos in positions:
                    try:
                        if isinstance(pos, (int, float)):
                            word_positions.append((int(pos), clean_word))
                    except (ValueError, TypeError):
                        continue
            
            if not word_positions:
                return ""
            
            # Sort by position and reconstruct text
            word_positions.sort(key=lambda x: x[0])
            abstract_words = [word for _, word in word_positions]
            
            if not abstract_words:
                return ""
            
            # Reconstruct and clean text
            abstract = ' '.join(abstract_words)
            
            # Basic cleanup
            abstract = ' '.join(abstract.split())  # Normalize whitespace
            
            # Limit length to reasonable size
            if len(abstract) > 2000:
                abstract = abstract[:2000] + "..."
            
            return abstract
            
        except Exception as e:
            logger.debug(f"Error reconstructing abstract: {e}")
            return ""
    
    def get_paper_details(self, openalex_id: str) -> Optional[Paper]:
        """Get detailed information about a specific paper"""
        try:
            # Clean the ID
            if openalex_id.startswith('openalex_'):
                openalex_id = openalex_id.replace('openalex_', '')
            
            url = f"https://api.openalex.org/works/{openalex_id}"
            params = {'mailto': self.mailto}
            
            self._rate_limit()
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return self.parse_paper(data)
            
        except Exception as e:
            logger.error(f"Error fetching paper details from OpenAlex: {e}")
            return None
    
    def search_by_author(self, author_name: str, max_results: int = 50) -> List[Paper]:
        """Search papers by author using OpenAlex - First find author, then get their works"""
        try:
            # Step 1: Search for the author first using the authors endpoint
            authors_url = "https://api.openalex.org/authors"
            author_params = {
                'search': author_name,
                'per-page': 5,  # Get top 5 matching authors
                'mailto': self.mailto
            }
            
            logger.info(f"Searching OpenAlex for author: {author_name}")
            
            self._rate_limit()
            author_response = self.session.get(authors_url, params=author_params, timeout=30)
            author_response.raise_for_status()
            
            author_data = author_response.json()
            authors = author_data.get('results', [])
            
            if not authors:
                logger.info(f"No authors found matching: {author_name}")
                return []
            
            # Take the first (most relevant) author
            target_author = authors[0]
            author_id = target_author.get('id', '').split('/')[-1] if target_author.get('id') else ''
            
            if not author_id:
                logger.info(f"No valid author ID found for: {author_name}")
                return []
            
            logger.info(f"Found author: {target_author.get('display_name')} (ID: {author_id})")
            
            # Step 2: Get works by this author using their OpenAlex ID
            works_params = {
                'filter': f'author.id:A{author_id}',  # Use the correct filter format
                'per-page': min(max_results, 200),
                'sort': 'cited_by_count:desc',
                'select': 'id,title,authorships,abstract_inverted_index,publication_date,primary_location,cited_by_count,doi,type',
                'mailto': self.mailto
            }
            
            self._rate_limit()
            works_response = self.session.get(self.base_url, params=works_params, timeout=30)
            works_response.raise_for_status()
            
            works_data = works_response.json()
            papers = []
            
            for item in works_data.get('results', []):
                paper = self.parse_paper(item)
                if paper:
                    papers.append(paper)
            
            logger.info(f"Found {len(papers)} papers by author: {author_name}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching by author in OpenAlex: {e}")
            return []
    
    def search_by_doi(self, doi: str) -> Optional[Paper]:
        """Search for a paper by DOI using OpenAlex"""
        try:
            # Clean DOI
            clean_doi = doi.replace('https://doi.org/', '').strip()
            
            params = {
                'filter': f'doi:{clean_doi}',
                'select': 'id,title,authorships,abstract_inverted_index,publication_date,primary_location,cited_by_count,doi,type',
                'mailto': self.mailto
            }
            
            self._rate_limit()
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('results'):
                return self.parse_paper(data['results'][0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching by DOI in OpenAlex: {e}")
            return None
    
    def get_related_papers(self, paper_id: str, max_results: int = 10) -> List[Paper]:
        """Get papers related to a given paper (by shared concepts)"""
        try:
            # Clean paper ID
            if paper_id.startswith('openalex_'):
                paper_id = paper_id.replace('openalex_', '')
            
            # First get the paper's concepts
            paper_url = f"https://api.openalex.org/works/{paper_id}"
            params = {'mailto': self.mailto}
            
            self._rate_limit()
            response = self.session.get(paper_url, params=params, timeout=30)
            response.raise_for_status()
            
            paper_data = response.json()
            concepts = paper_data.get('concepts', [])
            
            if not concepts:
                logger.info(f"No concepts found for paper {paper_id}")
                return []
            
            # Get top concepts
            top_concepts = sorted(concepts, key=lambda x: x.get('score', 0), reverse=True)[:3]
            concept_ids = []
            
            for concept in top_concepts:
                concept_id = concept.get('id', '')
                if concept_id and '/' in concept_id:
                    concept_ids.append(concept_id.split('/')[-1])
            
            if not concept_ids:
                logger.info(f"No valid concept IDs found for paper {paper_id}")
                return []
            
            # Search for papers with similar concepts
            concept_filter = '|'.join([f'concepts.id:C{cid}' for cid in concept_ids])
            
            params = {
                'filter': concept_filter,
                'per-page': max_results + 1,  # Get one extra to account for original paper
                'sort': 'cited_by_count:desc',
                'select': 'id,title,authorships,abstract_inverted_index,publication_date,primary_location,cited_by_count,doi',
                'mailto': self.mailto
            }
            
            self._rate_limit()
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for item in data.get('results', []):
                # Exclude the original paper
                item_id = item.get('id', '').split('/')[-1] if item.get('id') else ''
                if item_id != paper_id:
                    paper = self.parse_paper(item)
                    if paper and len(papers) < max_results:
                        papers.append(paper)
            
            logger.info(f"Found {len(papers)} related papers for {paper_id}")
            return papers
            
        except Exception as e:
            logger.error(f"Error getting related papers from OpenAlex: {e}")
            return []

    # Backward compatibility - alias for the old method name
    def parsepaper(self, item: Dict[str, Any]) -> Optional[Paper]:
        """Backward compatibility alias for parse_paper"""
        return self.parse_paper(item)