"""
RSS Feed Client with retry logic and politeness.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import time
from typing import Dict, Any
import feedparser
import requests


class RSSClient:
    """
    Fetch and parse RSS feeds with retry logic and rate limiting.
    
    Features:
    - Custom User-Agent for identification
    - Timeout enforcement
    - Exponential backoff retry
    - Rate limiting between requests
    """
    
    USER_AGENT = "BallisticIntelBot/0.1 (Cybersecurity Research; +contact@ballisticintel.com)"
    
    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 3,
        rate_limit_delay: float = 0.5
    ):
        """
        Initialize RSS client.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            rate_limit_delay: Delay between requests (politeness)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time: float = 0
    
    def fetch_feed(self, url: str) -> Dict[str, Any]:
        """
        Fetch and parse RSS feed with retry logic.
        
        Args:
            url: RSS feed URL
            
        Returns:
            feedparser.FeedParserDict (dict-like object)
            
        Raises:
            Exception: If all retries fail
        """
        # Rate limiting: ensure minimum delay between requests
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Fetch with custom headers
                response = requests.get(
                    url,
                    headers={'User-Agent': self.USER_AGENT},
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                self._last_request_time = time.time()
                
                # Parse feed
                feed = feedparser.parse(response.content)
                
                # Check for feed errors
                if hasattr(feed, 'bozo') and feed.bozo and feed.bozo_exception:
                    # Some feeds have minor parsing issues but are still usable
                    # Only fail if no entries
                    if not feed.entries:
                        raise Exception(f"Feed parsing failed: {feed.bozo_exception}")
                
                return feed
                
            except Exception as exc:
                last_exception = exc
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
        
        # All retries exhausted
        raise Exception(
            f"Failed to fetch feed {url} after {self.max_retries} attempts: "
            f"{last_exception}"
        )

