"""
Configuration for Agent P3 - Extraction & Classification.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
import os

class P3Config:
    """Configuration for extraction and classification."""
    
    # LLM settings
    LLM_MODEL = os.getenv('P3_LLM_MODEL', 'gemini-2.5-flash')
    LLM_TEMPERATURE = float(os.getenv('P3_LLM_TEMPERATURE', 0.1))
    LLM_MAX_OUTPUT_TOKENS = int(os.getenv('P3_LLM_MAX_TOKENS', 350))
    
    # Context truncation (chars)
    MAX_CONTEXT_LENGTH = int(os.getenv('P3_MAX_CONTEXT', 1200))
    
    # Concurrency (respect 15 RPM rate limit)
    MAX_WORKERS = int(os.getenv('P3_MAX_WORKERS', 3))
    
    # Caching
    ENABLE_CACHE = os.getenv('P3_ENABLE_CACHE', 'true').lower() == 'true'
    CACHE_TTL_SECONDS = int(os.getenv('P3_CACHE_TTL', 3600))  # 1 hour
    
    # Heuristic fallback
    ENABLE_FALLBACK = os.getenv('P3_ENABLE_FALLBACK', 'true').lower() == 'true'
    
    # Company name extraction limits
    MAX_COMPANIES = int(os.getenv('P3_MAX_COMPANIES', 5))
    MAX_KEYWORDS = int(os.getenv('P3_MAX_KEYWORDS', 10))
    
    # Novelty score defaults
    DEFAULT_NOVELTY_SCORE = float(os.getenv('P3_DEFAULT_NOVELTY', 0.5))
    
    # Logging
    LOG_LEVEL = os.getenv('P3_LOG_LEVEL', 'INFO')

