"""
News Articles Repository
Maps NewsArticle domain models to database schema and handles upserts
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

from models.news_article import NewsArticle
from clients.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class NewsRepository:
    """Repository for news_articles table"""
    
    TABLE_NAME = 'news_articles'
    CONFLICT_KEY = 'link'  # Enforce uniqueness on URL
    
    def __init__(self):
        self.client = get_supabase_client()
    
    @staticmethod
    def _to_db_dict(article: NewsArticle) -> Dict[str, Any]:
        """
        Convert NewsArticle model to database dict
        
        Args:
            article: NewsArticle domain model
        
        Returns:
            Dict matching news_articles table schema
        """
        return {
            'id': article.id,
            'source': article.source,
            'title': article.title,
            'link': article.link,
            'published_at': article.published_at.isoformat() if isinstance(article.published_at, datetime) else article.published_at,
            'summary': article.summary,
            'categories': article.categories or [],
            'content_text': article.content_text,
        }
    
    def upsert_news(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """
        Upsert news articles in batches
        
        Args:
            articles: List of NewsArticle models
        
        Returns:
            Dict with 'count' (rows written) and 'success' (bool)
        
        Raises:
            RuntimeError: On persistent failures
        """
        if not articles:
            logger.warning("upsert_news called with empty list")
            return {'count': 0, 'success': True}
        
        logger.info(f"Upserting {len(articles)} news articles")
        
        try:
            # Convert to DB format
            rows = [self._to_db_dict(a) for a in articles]
            
            # Batch upsert
            result = self.client.upsert_batch(
                table=self.TABLE_NAME,
                rows=rows,
                on_conflict=self.CONFLICT_KEY,
                returning='minimal'
            )
            
            count = result.get('count', 0)
            logger.info(f"Successfully upserted {count} news articles")
            
            return {
                'count': count,
                'success': True,
                'table': self.TABLE_NAME
            }
        
        except Exception as e:
            logger.error(f"Failed to upsert news articles: {e}", exc_info=True)
            return {
                'count': 0,
                'success': False,
                'error': str(e),
                'table': self.TABLE_NAME
            }
    
    def get_by_link(self, link: str) -> Dict[str, Any]:
        """
        Get a single article by URL
        
        Args:
            link: Article URL
        
        Returns:
            Article dict or empty dict if not found
        """
        results = self.client.select(
            table=self.TABLE_NAME,
            filters={'link': link},
            limit=1
        )
        return results[0] if results else {}
    
    def get_recent_articles(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recently published articles
        
        Args:
            limit: Max number of articles
        
        Returns:
            List of article dicts
        """
        return self.client.select(
            table=self.TABLE_NAME,
            limit=limit
        )

