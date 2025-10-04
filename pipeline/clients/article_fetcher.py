"""
Article content fetcher and HTML text extraction.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import time
from typing import Optional, Dict
import requests
from bs4 import BeautifulSoup


class ArticleFetcher:
    """
    Fetch article HTML and extract main text content.
    
    Features:
    - Custom User-Agent
    - Content-length cap to avoid huge pages
    - Basic readability extraction using BeautifulSoup
    - In-memory cache to avoid re-fetching
    """
    
    USER_AGENT = "BallisticIntelBot/0.1 (Cybersecurity Research)"
    MAX_CONTENT_LENGTH = 500 * 1024  # 500KB
    
    def __init__(
        self,
        timeout: int = 10,
        rate_limit_delay: float = 0.5
    ):
        """
        Initialize article fetcher.
        
        Args:
            timeout: Request timeout in seconds
            rate_limit_delay: Delay between requests
        """
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self._cache: Dict[str, str] = {}
        self._last_request_time: float = 0
    
    def fetch_content(self, url: str) -> Optional[str]:
        """
        Fetch article HTML and extract main text.
        
        Args:
            url: Article URL
            
        Returns:
            Extracted text or None if failed
        """
        # Check cache
        if url in self._cache:
            return self._cache[url]
        
        # Rate limiting
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        
        try:
            # Fetch HTML
            response = requests.get(
                url,
                headers={'User-Agent': self.USER_AGENT},
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()
            
            # Check content length
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
                return None
            
            self._last_request_time = time.time()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract text from common content containers
            # Priority: article, main, content div, body
            content = None
            for selector in ['article', 'main', 'div[class*="content"]', 'body']:
                content = soup.select_one(selector)
                if content:
                    break
            
            if not content:
                return None
            
            # Remove script, style, nav, footer
            for tag in content.find_all(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            
            # Extract text
            text = content.get_text(separator=' ', strip=True)
            
            # Basic cleaning
            text = ' '.join(text.split())  # Normalize whitespace
            
            # Cache result
            self._cache[url] = text
            
            return text
            
        except Exception as exc:
            print(f"Warning: Failed to fetch content from {url}: {exc}")
            return None
    
    def clear_cache(self):
        """Clear the fetch cache."""
        self._cache.clear()

