"""
NewsArticle data model for newsletter ingestion (Agent P1b).

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class NewsArticle:
    """
    Represents a news article extracted from an RSS feed.
    
    Attributes:
        id: Stable hash of source + link for deduplication
        source: Feed/source name (e.g., "TheCyberWire")
        title: Article title
        link: Article URL
        published_at: Publication datetime (UTC)
        summary: Short description from feed (may contain HTML)
        content_text: Full article text (optional, extracted from HTML)
        categories: Tags/categories from feed
        is_funding_announcement: Flag for funding announcement
        funding_hint_reason: Why it was flagged as funding (for debugging)
        raw: Raw feed entry for troubleshooting
    """
    
    source: str
    title: str
    link: str
    published_at: datetime
    summary: str = ""
    content_text: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    is_funding_announcement: bool = False
    funding_hint_reason: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate stable ID from source + link."""
        if not hasattr(self, '_id'):
            hash_input = f"{self.source}:{self.link}"
            self._id = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    @property
    def id(self) -> str:
        """Stable identifier for deduplication."""
        if not hasattr(self, '_id'):
            self.__post_init__()
        return self._id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        data = asdict(self)
        data['id'] = self.id
        data['published_at'] = self.published_at.isoformat()
        # Don't include raw in export (too verbose)
        data.pop('raw', None)
        return data
    
    @classmethod
    def from_feed_entry(
        cls, 
        entry: Dict[str, Any], 
        source_name: str
    ) -> "NewsArticle":
        """
        Create NewsArticle from feedparser entry.
        
        Args:
            entry: feedparser entry dict
            source_name: Name of the feed source
            
        Returns:
            NewsArticle instance
        """
        # Extract published date (fallback to updated, then now)
        published = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            published = datetime(*entry.updated_parsed[:6])
        else:
            published = datetime.utcnow()
        
        # Extract categories/tags
        categories = []
        if hasattr(entry, 'tags'):
            categories = [tag.get('term', '') for tag in entry.tags if tag.get('term')]
        
        # Get summary (may contain HTML)
        summary = ""
        if hasattr(entry, 'summary'):
            summary = entry.summary
        elif hasattr(entry, 'description'):
            summary = entry.description
        
        return cls(
            source=source_name,
            title=entry.get('title', '').strip(),
            link=entry.get('link', '').strip(),
            published_at=published,
            summary=summary,
            categories=categories,
            raw=dict(entry)
        )
    
    def get_text_for_analysis(self) -> str:
        """
        Get combined text for funding detection.
        
        Returns title + summary + content_text (if available).
        """
        parts = [self.title, self.summary]
        if self.content_text:
            parts.append(self.content_text)
        return " ".join(p for p in parts if p)

