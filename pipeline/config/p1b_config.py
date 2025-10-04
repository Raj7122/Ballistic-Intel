"""
Configuration for Agent P1b - Newsletter Ingestion.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
import os

class P1BConfig:
    """Configuration for newsletter ingestion."""
    
    # RSS Feeds to monitor
    FEEDS = [
        {
            "url": "https://thecyberwire.com/feeds/rss.xml",
            "source_name": "TheCyberWire"
        },
        {
            "url": "https://www.darkreading.com/rss.xml",
            "source_name": "DarkReading"
        },
        {
            "url": "https://www.securityweek.com/feed/",
            "source_name": "SecurityWeek"
        },
        {
            "url": "https://techcrunch.com/category/security/feed/",
            "source_name": "TechCrunch Security"
        },
    ]
    
    # Lookback window
    LOOKBACK_DAYS = int(os.getenv('NEWSLETTER_LOOKBACK_DAYS', 7))
    
    # Request settings
    REQUEST_TIMEOUT = int(os.getenv('NEWSLETTER_TIMEOUT', 10))
    MAX_PER_FEED = int(os.getenv('NEWSLETTER_MAX_PER_FEED', 200))
    
    # Content fetching
    FETCH_HTML_CONTENT = os.getenv('NEWSLETTER_FETCH_HTML', 'true').lower() == 'true'
    
    # Rate limiting (requests per second)
    RATE_LIMIT_DELAY = float(os.getenv('NEWSLETTER_RATE_LIMIT_DELAY', 0.5))
    
    # Funding detection
    MIN_FUNDING_SIGNALS = int(os.getenv('FUNDING_MIN_SIGNALS', 2))

