"""
Company name normalization for entity resolution.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import re
import unicodedata
from typing import List, Set

from config.p4_config import P4Config


class NameNormalizer:
    """
    Normalize company names for matching and deduplication.
    
    Features:
    - Case folding and Unicode normalization
    - Legal suffix removal
    - Corporate stopword removal
    - Punctuation and whitespace cleaning
    - Token sorting and deduplication
    - Acronym detection
    """
    
    def __init__(self):
        """Initialize normalizer with configuration."""
        self.legal_suffixes = set(s.lower() for s in P4Config.LEGAL_SUFFIXES)
        self.stopwords = set(s.lower() for s in P4Config.CORPORATE_STOPWORDS)
    
    def normalize(self, name: str) -> str:
        """
        Normalize a company name to canonical form.
        
        Args:
            name: Raw company name
            
        Returns:
            Normalized name
        """
        if not name:
            return ""
        
        # Unicode NFC normalization
        name = unicodedata.normalize('NFC', name)
        
        # Lowercase
        name = name.lower()
        
        # Replace ampersands and slashes
        name = name.replace('&', ' and ')
        name = name.replace('/', ' ')
        
        # Remove punctuation except spaces
        name = re.sub(r'[^\w\s]', '', name)
        
        # Collapse multiple spaces
        name = ' '.join(name.split())
        
        # Tokenize
        tokens = name.split()
        
        # Remove legal suffixes
        tokens = self._remove_legal_suffixes(tokens)
        
        # Remove corporate stopwords (but keep if it's the only token or if it's part of the company name)
        # Be conservative: only remove if it's a trailing stopword and there are 2+ other tokens
        if len(tokens) > 2 and tokens[-1] in self.stopwords:
            tokens = tokens[:-1]
        
        # Deduplicate tokens while preserving order
        seen: Set[str] = set()
        unique_tokens = []
        for token in tokens:
            if token not in seen:
                seen.add(token)
                unique_tokens.append(token)
        
        # Join back
        normalized = ' '.join(unique_tokens)
        
        return normalized.strip()
    
    def _remove_legal_suffixes(self, tokens: List[str]) -> List[str]:
        """
        Remove legal suffixes from token list.
        
        Args:
            tokens: List of lowercase tokens
            
        Returns:
            Tokens with suffixes removed
        """
        if not tokens:
            return tokens
        
        # Check last token
        if tokens[-1] in self.legal_suffixes:
            tokens = tokens[:-1]
        
        # Check second-to-last if it's a multi-part suffix (e.g., "co kg")
        if len(tokens) >= 2:
            last_two = f"{tokens[-2]} {tokens[-1]}"
            if last_two in self.legal_suffixes:
                tokens = tokens[:-2]
        
        return tokens
    
    def extract_tokens(self, name: str) -> Set[str]:
        """
        Extract normalized token set from name.
        
        Args:
            name: Company name
            
        Returns:
            Set of normalized tokens
        """
        normalized = self.normalize(name)
        return set(normalized.split()) if normalized else set()
    
    def is_acronym(self, name: str) -> bool:
        """
        Check if name appears to be an acronym.
        
        Args:
            name: Company name
            
        Returns:
            True if likely an acronym
        """
        normalized = self.normalize(name)
        tokens = normalized.split()
        
        # Single token, all uppercase in original, ≤5 chars
        if len(tokens) == 1:
            # Check original for uppercase
            original_tokens = name.strip().split()
            if original_tokens:
                first = original_tokens[0]
                if first.isupper() and len(first) <= 5:
                    return True
        
        return False
    
    def expand_acronym(self, acronym: str) -> str:
        """
        Attempt to expand acronym using known mappings.
        
        Args:
            acronym: Potential acronym
            
        Returns:
            Expanded form or original if not found
        """
        normalized = self.normalize(acronym)
        return P4Config.ACRONYM_EXPANSIONS.get(normalized, normalized)
    
    def matches_acronym(self, full_name: str, acronym: str) -> bool:
        """
        Check if acronym matches the initials of full name.
        
        Args:
            full_name: Full company name
            acronym: Potential acronym
            
        Returns:
            True if acronym matches initials
        """
        full_tokens = self.extract_tokens(full_name)
        acronym_normalized = self.normalize(acronym)
        
        if not full_tokens or not acronym_normalized:
            return False
        
        # Get initials from full name (preserve order, don't sort)
        initials = ''.join(token[0] for token in full_tokens if token)
        
        # Also try with 'w' for 'works/ware/ways' common variants
        return initials == acronym_normalized or initials.replace('w', '') == acronym_normalized

