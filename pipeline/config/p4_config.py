"""
Configuration for Agent P4 - Entity Resolution.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
import os

class P4Config:
    """Configuration for entity resolution."""
    
    # Similarity thresholds
    HARD_MATCH_THRESHOLD = float(os.getenv('P4_HARD_MATCH', 0.88))  # Definite match
    SOFT_MATCH_THRESHOLD = float(os.getenv('P4_SOFT_MATCH', 0.70))  # Possible match (needs corroboration)
    
    # Similarity weights (must sum to 1.0)
    WEIGHT_TOKEN_JACCARD = float(os.getenv('P4_WEIGHT_TOKEN', 0.35))
    WEIGHT_EDIT_DISTANCE = float(os.getenv('P4_WEIGHT_EDIT', 0.25))
    WEIGHT_JARO_WINKLER = float(os.getenv('P4_WEIGHT_JARO', 0.15))
    WEIGHT_ACRONYM = float(os.getenv('P4_WEIGHT_ACRONYM', 0.25))  # Increased for acronym importance
    
    # Feature toggles
    USE_PHONETIC = os.getenv('P4_USE_PHONETIC', 'false').lower() == 'true'
    USE_ACRONYM_EXPANSION = os.getenv('P4_USE_ACRONYM', 'true').lower() == 'true'
    
    # Blocking parameters
    MIN_BLOCK_SIZE = int(os.getenv('P4_MIN_BLOCK_SIZE', 2))
    MAX_BLOCK_SIZE = int(os.getenv('P4_MAX_BLOCK_SIZE', 1000))
    
    # Clustering guardrails
    MAX_CLUSTER_SIZE = int(os.getenv('P4_MAX_CLUSTER_SIZE', 20))
    
    # Canonical selection strategy
    CANONICAL_STRATEGY = os.getenv('P4_CANONICAL_STRATEGY', 'longest')  # longest, most_frequent, highest_score
    
    # Legal suffixes to remove (international)
    LEGAL_SUFFIXES = [
        'inc', 'incorporated', 'corp', 'corporation', 'ltd', 'limited',
        'llc', 'l.l.c.', 'co', 'company', 'plc', 'p.l.c.',
        's.a.', 'sa', 'ag', 'gmbh', 'bv', 'b.v.', 'n.v.', 'nv',
        'pte', 'pty', 'oy', 'kk', 'k.k.', 'kft', 'srl', 's.r.l.',
        'ab', 'as', 'a/s', 'spa', 's.p.a.', 'kg', 'gmbh & co. kg'
    ]
    
    # Corporate stopwords (remove if not sole token)
    CORPORATE_STOPWORDS = [
        'technologies', 'technology', 'systems', 'solutions',
        'holdings', 'group', 'international', 'global',
        'services', 'software', 'labs', 'laboratory'
    ]
    
    # Common acronym expansions (seed dictionary)
    ACRONYM_EXPANSIONS = {
        'pan': 'palo alto networks',
        'vmw': 'vmware',
        'csco': 'cisco',
        'crwd': 'crowdstrike',
        'ftnt': 'fortinet',
        'panw': 'palo alto networks',
        'zs': 'zscaler',
        'okta': 'okta',
    }
    
    # Performance
    ENABLE_CACHE = os.getenv('P4_ENABLE_CACHE', 'true').lower() == 'true'
    MAX_CACHE_SIZE = int(os.getenv('P4_MAX_CACHE_SIZE', 10000))
    
    # Logging
    LOG_LEVEL = os.getenv('P4_LOG_LEVEL', 'INFO')
    LOG_DETAILED_SCORES = os.getenv('P4_LOG_SCORES', 'false').lower() == 'true'

