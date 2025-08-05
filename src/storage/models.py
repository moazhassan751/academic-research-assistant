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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'authors': json.dumps(self.authors),
            'abstract': self.abstract,
            'url': self.url,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'venue': self.venue,
            'citations': self.citations,
            'pdf_path': self.pdf_path,
            'full_text': self.full_text,
            'keywords': json.dumps(self.keywords),
            'doi': self.doi,
            'arxiv_id': self.arxiv_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Paper':
        if data.get('published_date'):
            data['published_date'] = datetime.fromisoformat(data['published_date'])
        if data.get('authors'):
            data['authors'] = json.loads(data['authors'])
        if data.get('keywords'):
            data['keywords'] = json.loads(data['keywords'])
        return cls(**data)

@dataclass
class ResearchNote:
    """Research note extracted from papers"""
    id: str
    paper_id: str
    content: str
    note_type: str  # 'key_finding', 'methodology', 'limitation', 'future_work'
    confidence: float = 0.0
    page_number: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'paper_id': self.paper_id,
            'content': self.content,
            'note_type': self.note_type,
            'confidence': self.confidence,
            'page_number': self.page_number,
            'created_at': self.created_at.isoformat()
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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'papers': json.dumps(self.papers),
            'frequency': self.frequency,
            'confidence': self.confidence,
            'related_themes': json.dumps(self.related_themes)
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