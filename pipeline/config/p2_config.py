"""
Configuration for Agent P2 - Universal Relevance Filter.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
import os

class P2Config:
    """Configuration for relevance filtering."""
    
    # Minimum score threshold for relevance
    MIN_RELEVANCE_SCORE = float(os.getenv('P2_MIN_SCORE', 0.6))
    
    # LLM settings
    LLM_MODEL = os.getenv('P2_LLM_MODEL', 'gemini-2.5-flash')
    LLM_TEMPERATURE = float(os.getenv('P2_LLM_TEMPERATURE', 0.1))
    LLM_MAX_OUTPUT_TOKENS = int(os.getenv('P2_LLM_MAX_TOKENS', 200))
    
    # Context truncation (chars)
    MAX_CONTEXT_LENGTH = int(os.getenv('P2_MAX_CONTEXT', 800))
    
    # Concurrency (respect 15 RPM rate limit)
    MAX_WORKERS = int(os.getenv('P2_MAX_WORKERS', 3))
    
    # Caching
    ENABLE_CACHE = os.getenv('P2_ENABLE_CACHE', 'true').lower() == 'true'
    CACHE_TTL_SECONDS = int(os.getenv('P2_CACHE_TTL', 3600))  # 1 hour
    
    # Retry settings
    MAX_RETRIES = int(os.getenv('P2_MAX_RETRIES', 2))
    RETRY_DELAY = float(os.getenv('P2_RETRY_DELAY', 1.0))
    
    # Heuristic fallback settings
    ENABLE_FALLBACK = os.getenv('P2_ENABLE_FALLBACK', 'true').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.getenv('P2_LOG_LEVEL', 'INFO')

