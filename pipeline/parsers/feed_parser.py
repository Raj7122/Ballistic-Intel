"""
Feed parser to convert RSS entries to NewsArticle objects.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict, Any

from models import NewsArticle


class FeedParser:
    """
    Parse RSS feed entries into NewsArticle objects with date filtering.
    """
    
    def __init__(self, lookback_days: int = 7, max_per_feed: int = 200):
        """
        Initialize feed parser.
        
        Args:
            lookback_days: Only include articles from last N days
            max_per_feed: Maximum articles per feed
        """
        self.lookback_days = lookback_days
        self.max_per_feed = max_per_feed
        self.cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
    
    def parse_feed(
        self, 
        feed: Dict[str, Any], 
        source_name: str
    ) -> List[NewsArticle]:
        """
        Parse feed entries into NewsArticle objects.
        
        Args:
            feed: feedparser.FeedParserDict
            source_name: Name of the feed source
            
        Returns:
            List of NewsArticle objects
        """
        articles: List[NewsArticle] = []
        seen_links: set[str] = set()
        
        entries = feed.get('entries', [])[:self.max_per_feed]
        
        for entry in entries:
            try:
                article = NewsArticle.from_feed_entry(entry, source_name)
                
                # Filter by date
                if article.published_at < self.cutoff_date:
                    continue
                
                # Deduplicate by link
                if article.link in seen_links:
                    continue
                seen_links.add(article.link)
                
                # Basic validation
                if not article.title or not article.link:
                    continue
                
                articles.append(article)
                
            except Exception as exc:
                # Log parse error but continue with other entries
                print(f"Warning: Failed to parse entry: {exc}")
                continue
        
        return articles

