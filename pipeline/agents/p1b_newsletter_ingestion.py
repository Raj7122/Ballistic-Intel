"""
Agent P1b: Newsletter Ingestion from RSS feeds.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import time
from typing import List, Dict, Any

from clients.rss_client import RSSClient
from clients.article_fetcher import ArticleFetcher
from parsers.feed_parser import FeedParser
from logic.funding_detector import FundingDetector
from models import NewsArticle
from config.p1b_config import P1BConfig


class NewsletterIngestionError(Exception):
    """Custom exception for newsletter ingestion failures."""


class NewsletterIngestionAgent:
    """
    Agent P1b: Newsletter Ingestion from RSS feeds.
    
    Responsibilities:
      1. Fetch RSS feeds from configured sources
      2. Parse entries into NewsArticle objects
      3. Optionally fetch full article content
      4. Detect funding announcements using heuristics
      5. Track statistics
    """
    
    def __init__(
        self,
        *,
        lookback_days: int = P1BConfig.LOOKBACK_DAYS,
        fetch_content: bool = P1BConfig.FETCH_HTML_CONTENT,
        min_articles: int = 100
    ):
        """
        Initialize newsletter ingestion agent.
        
        Args:
            lookback_days: Days to look back for articles
            fetch_content: Whether to fetch full article HTML
            min_articles: Minimum articles required
        """
        self.rss_client = RSSClient(
            timeout=P1BConfig.REQUEST_TIMEOUT,
            rate_limit_delay=P1BConfig.RATE_LIMIT_DELAY
        )
        self.feed_parser = FeedParser(
            lookback_days=lookback_days,
            max_per_feed=P1BConfig.MAX_PER_FEED
        )
        self.article_fetcher = ArticleFetcher(
            timeout=P1BConfig.REQUEST_TIMEOUT,
            rate_limit_delay=P1BConfig.RATE_LIMIT_DELAY
        ) if fetch_content else None
        self.funding_detector = FundingDetector(
            min_signals=P1BConfig.MIN_FUNDING_SIGNALS
        )
        
        self.fetch_content = fetch_content
        self.min_articles = min_articles
        
        self.stats: Dict[str, Any] = {
            "feeds_processed": 0,
            "feeds_failed": 0,
            "articles_total": 0,
            "articles_after_filter": 0,
            "funding_flagged": 0,
            "content_fetched": 0,
            "errors": [],
            "processing_time": 0.0,
        }
    
    def fetch_articles(self) -> List[NewsArticle]:
        """
        Fetch articles from all configured feeds.
        
        Returns:
            List of NewsArticle objects
            
        Raises:
            NewsletterIngestionError: If insufficient articles retrieved
        """
        start_time = time.time()
        all_articles: List[NewsArticle] = []
        seen_ids: set[str] = set()
        
        for feed_config in P1BConfig.FEEDS:
            source_name = feed_config["source_name"]
            feed_url = feed_config["url"]
            
            try:
                # Fetch and parse feed
                feed = self.rss_client.fetch_feed(feed_url)
                articles = self.feed_parser.parse_feed(feed, source_name)
                
                # Deduplicate across feeds
                for article in articles:
                    if article.id not in seen_ids:
                        all_articles.append(article)
                        seen_ids.add(article.id)
                
                self.stats["feeds_processed"] += 1
                print(f"✓ {source_name}: {len(articles)} articles")
                
            except Exception as exc:
                self.stats["feeds_failed"] += 1
                self.stats["errors"].append(f"{source_name}: {exc}")
                print(f"✗ {source_name}: {exc}")
                continue
        
        self.stats["articles_total"] = len(all_articles)
        
        # Fetch full content if enabled
        if self.fetch_content and self.article_fetcher:
            for article in all_articles:
                content = self.article_fetcher.fetch_content(article.link)
                if content:
                    article.content_text = content
                    self.stats["content_fetched"] += 1
        
        # Run funding detection
        for article in all_articles:
            text = article.get_text_for_analysis()
            is_funding, reason = self.funding_detector.detect(text)
            article.is_funding_announcement = is_funding
            article.funding_hint_reason = reason
            
            if is_funding:
                self.stats["funding_flagged"] += 1
        
        self.stats["articles_after_filter"] = len(all_articles)
        self.stats["processing_time"] = time.time() - start_time
        
        # Check minimum threshold
        if len(all_articles) < self.min_articles:
            raise NewsletterIngestionError(
                f"Only {len(all_articles)} articles retrieved "
                f"(minimum: {self.min_articles})"
            )
        
        return all_articles
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return ingestion statistics."""
        return dict(self.stats)

