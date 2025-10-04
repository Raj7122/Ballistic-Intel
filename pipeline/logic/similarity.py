"""
String similarity functions for entity resolution.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import Levenshtein
import jellyfish
from typing import Set, Tuple

from config.p4_config import P4Config
from logic.name_normalizer import NameNormalizer


class SimilarityCalculator:
    """
    Calculate similarity scores between company names.
    
    Uses multiple similarity metrics with configurable weights.
    """
    
    def __init__(self):
        """Initialize calculator."""
        self.normalizer = NameNormalizer()
    
    def token_jaccard(self, tokens1: Set[str], tokens2: Set[str]) -> float:
        """
        Calculate Jaccard similarity between token sets.
        
        Args:
            tokens1: First token set
            tokens2: Second token set
            
        Returns:
            Jaccard similarity (0.0-1.0)
        """
        if not tokens1 and not tokens2:
            return 1.0
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        
        return len(intersection) / len(union) if union else 0.0
    
    def edit_distance_ratio(self, str1: str, str2: str) -> float:
        """
        Calculate normalized edit distance ratio.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity ratio (0.0-1.0)
        """
        if not str1 and not str2:
            return 1.0
        if not str1 or not str2:
            return 0.0
        
        return Levenshtein.ratio(str1, str2)
    
    def jaro_winkler(self, str1: str, str2: str) -> float:
        """
        Calculate Jaro-Winkler similarity.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Jaro-Winkler score (0.0-1.0)
        """
        if not str1 and not str2:
            return 1.0
        if not str1 or not str2:
            return 0.0
        
        return jellyfish.jaro_winkler_similarity(str1, str2)
    
    def acronym_score(self, name1: str, name2: str) -> float:
        """
        Calculate acronym matching score.
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            Acronym score (0.0 or 1.0)
        """
        # Check if one is acronym and matches the other
        if P4Config.USE_ACRONYM_EXPANSION:
            # Check direct acronym match
            if self.normalizer.matches_acronym(name1, name2):
                return 1.0
            if self.normalizer.matches_acronym(name2, name1):
                return 1.0
            
            # Check expansion match
            expanded1 = self.normalizer.expand_acronym(name1)
            expanded2 = self.normalizer.expand_acronym(name2)
            
            if expanded1 != name1 or expanded2 != name2:
                # One was expanded, check if they match now
                if expanded1 == expanded2:
                    return 1.0
                # Check if expansion matches the other
                if self.normalizer.normalize(expanded1) == self.normalizer.normalize(name2):
                    return 1.0
                if self.normalizer.normalize(expanded2) == self.normalizer.normalize(name1):
                    return 1.0
        
        return 0.0
    
    def composite_score(
        self,
        name1: str,
        name2: str
    ) -> Tuple[float, dict]:
        """
        Calculate weighted composite similarity score.
        
        Args:
            name1: First company name
            name2: Second company name
            
        Returns:
            Tuple of (composite_score, component_scores_dict)
        """
        # Normalize
        norm1 = self.normalizer.normalize(name1)
        norm2 = self.normalizer.normalize(name2)
        
        # Extract tokens
        tokens1 = self.normalizer.extract_tokens(name1)
        tokens2 = self.normalizer.extract_tokens(name2)
        
        # Calculate component scores
        jaccard = self.token_jaccard(tokens1, tokens2)
        edit = self.edit_distance_ratio(norm1, norm2)
        jaro = self.jaro_winkler(norm1, norm2)
        acronym = self.acronym_score(name1, name2)
        
        # Weighted composite
        composite = (
            P4Config.WEIGHT_TOKEN_JACCARD * jaccard +
            P4Config.WEIGHT_EDIT_DISTANCE * edit +
            P4Config.WEIGHT_JARO_WINKLER * jaro +
            P4Config.WEIGHT_ACRONYM * acronym
        )
        
        components = {
            'jaccard': jaccard,
            'edit': edit,
            'jaro': jaro,
            'acronym': acronym,
            'composite': composite
        }
        
        return composite, components
    
    def is_match(
        self,
        name1: str,
        name2: str
    ) -> Tuple[bool, float, list]:
        """
        Determine if two names match.
        
        Args:
            name1: First company name
            name2: Second company name
            
        Returns:
            Tuple of (is_match, score, rules_applied)
        """
        score, components = self.composite_score(name1, name2)
        rules = []
        
        # Hard match
        if score >= P4Config.HARD_MATCH_THRESHOLD:
            rules.append('hard_match')
            return (True, score, rules)
        
        # Soft match with corroboration
        if score >= P4Config.SOFT_MATCH_THRESHOLD:
            # Check for corroborating signals
            if components['acronym'] == 1.0:
                rules.append('soft_match_with_acronym')
                return (True, score, rules)
            
            if components['jaccard'] >= 0.8:
                rules.append('soft_match_with_high_token_overlap')
                return (True, score, rules)
            
            # High edit distance suggests close strings
            if components['edit'] >= 0.9:
                rules.append('soft_match_with_high_edit_similarity')
                return (True, score, rules)
            
            rules.append('soft_match_no_corroboration')
            return (False, score, rules)
        
        rules.append('no_match')
        return (False, score, rules)

