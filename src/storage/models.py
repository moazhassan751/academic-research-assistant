from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

@dataclass
class Paper:
    """Research paper data model"""
    id: str
    title: str
    authors: List[str]
    abstract: str
    url: str
    published_date: Optional[datetime] = None
    venue: Optional[str] = None
    citations: int = 0
    pdf_path: Optional[str] = None
    full_text: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    created_at: Optional[datetime] = None  # Add this field to match database schema
    _source: Optional[str] = field(default=None, init=False)  # Private field to store explicit source
    
    @property
    def source(self) -> str:
        """Return the source of the paper based on available identifiers"""
        # If source was explicitly set, return it
        if self._source:
            return self._source
            
        # Otherwise, infer from available data
        if self.arxiv_id:
            return "ArXiv"
        elif self.doi and "crossref" in str(self.doi).lower():
            return "CrossRef"
        elif self.venue:
            if "arxiv" in self.venue.lower():
                return "ArXiv"
            elif any(word in self.venue.lower() for word in ["conference", "proceedings"]):
                return "Conference"
            elif any(word in self.venue.lower() for word in ["journal", "trans"]):
                return "Journal"
            else:
                return self.venue
        else:
            return "Unknown"
    
    @source.setter
    def source(self, value: str):
        """Set the source explicitly"""
        self._source = value
    
    @property
    def year(self) -> str:
        """Return the publication year as string"""
        if self.published_date:
            return str(self.published_date.year)
        return "Unknown"
    
    @property
    def topic(self) -> str:
        """Return the inferred topic from keywords or venue"""
        if self.keywords:
            return ", ".join(self.keywords[:3])  # Return first 3 keywords
        elif self.venue:
            return self.venue
        else:
            return "General"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'authors': json.dumps(self.authors) if self.authors else json.dumps([]),
            'abstract': self.abstract or '',
            'url': self.url or '',
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'venue': self.venue or '',
            'citations': self.citations or 0,
            'pdf_path': self.pdf_path,
            'full_text': self.full_text,
            'keywords': json.dumps(self.keywords) if self.keywords else json.dumps([]),
            'doi': self.doi,
            'arxiv_id': self.arxiv_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Paper':
        # Create a copy to avoid mutating original data
        data_copy = data.copy()
        
        # Handle published_date
        if data_copy.get('published_date'):
            try:
                data_copy['published_date'] = datetime.fromisoformat(data_copy['published_date'])
            except (ValueError, TypeError):
                data_copy['published_date'] = None
        
        # Handle created_at field from database
        if data_copy.get('created_at'):
            try:
                if isinstance(data_copy['created_at'], str):
                    data_copy['created_at'] = datetime.fromisoformat(data_copy['created_at'])
            except (ValueError, TypeError):
                data_copy['created_at'] = None
        
        # Handle authors JSON
        if data_copy.get('authors'):
            try:
                if isinstance(data_copy['authors'], str):
                    data_copy['authors'] = json.loads(data_copy['authors'])
                elif not isinstance(data_copy['authors'], list):
                    data_copy['authors'] = []
            except (json.JSONDecodeError, TypeError):
                data_copy['authors'] = []
        else:
            data_copy['authors'] = []
        
        # Handle keywords JSON
        if data_copy.get('keywords'):
            try:
                if isinstance(data_copy['keywords'], str):
                    data_copy['keywords'] = json.loads(data_copy['keywords'])
                elif not isinstance(data_copy['keywords'], list):
                    data_copy['keywords'] = []
            except (json.JSONDecodeError, TypeError):
                data_copy['keywords'] = []
        else:
            data_copy['keywords'] = []
        
        # Ensure required fields have default values
        data_copy.setdefault('title', '')
        data_copy.setdefault('abstract', '')
        data_copy.setdefault('url', '')
        data_copy.setdefault('citations', 0)
        
        # Remove any unexpected fields that might cause issues
        expected_fields = {
            'id', 'title', 'authors', 'abstract', 'url', 'published_date', 
            'venue', 'citations', 'pdf_path', 'full_text', 'keywords', 
            'doi', 'arxiv_id', 'created_at'
        }
        filtered_data = {k: v for k, v in data_copy.items() if k in expected_fields}
        
        return cls(**filtered_data)

@dataclass
class ResearchNote:
    """Research note extracted from papers"""
    id: str
    paper_id: str
    content: str
    note_type: str  # 'key_finding', 'methodology', 'limitation', 'future_work'
    confidence: float = 0.0
    page_number: Optional[int] = None
    created_at: Optional[datetime] = None  # Make this Optional to handle database values
    
    def __post_init__(self):
        """Handle datetime conversion from database strings"""
        if isinstance(self.created_at, str):
            try:
                self.created_at = datetime.fromisoformat(self.created_at)
            except (ValueError, TypeError):
                self.created_at = datetime.now()
        elif self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'paper_id': self.paper_id,
            'content': self.content,
            'note_type': self.note_type,
            'confidence': self.confidence,
            'page_number': self.page_number,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.now().isoformat()
        }

@dataclass
class ResearchTheme:
    """Synthesized research theme"""
    id: str
    title: str
    description: str
    papers: List[str]  # Paper IDs
    frequency: int
    confidence: float
    related_themes: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Handle JSON deserialization for themes from database"""
        # Handle papers field
        if isinstance(self.papers, str):
            try:
                self.papers = json.loads(self.papers)
            except (json.JSONDecodeError, TypeError):
                self.papers = []
        elif not isinstance(self.papers, list):
            self.papers = []
        
        # Handle related_themes field
        if isinstance(self.related_themes, str):
            try:
                self.related_themes = json.loads(self.related_themes)
            except (json.JSONDecodeError, TypeError):
                self.related_themes = []
        elif not isinstance(self.related_themes, list):
            self.related_themes = []
        
        # Handle created_at
        if isinstance(self.created_at, str):
            try:
                self.created_at = datetime.fromisoformat(self.created_at)
            except (ValueError, TypeError):
                self.created_at = datetime.now()
        elif self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'papers': json.dumps(self.papers) if self.papers else json.dumps([]),
            'frequency': self.frequency,
            'confidence': self.confidence,
            'related_themes': json.dumps(self.related_themes) if self.related_themes else json.dumps([]),
            'created_at': self.created_at.isoformat() if self.created_at else datetime.now().isoformat()
        }

@dataclass
class Citation:
    """Citation information"""
    id: str
    paper_id: str
    citation_key: str
    apa_format: str
    mla_format: str
    bibtex: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'paper_id': self.paper_id,
            'citation_key': self.citation_key,
            'apa_format': self.apa_format,
            'mla_format': self.mla_format,
            'bibtex': self.bibtex
        }