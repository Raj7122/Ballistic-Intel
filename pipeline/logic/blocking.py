"""
Blocking strategy for efficient candidate generation.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

from collections import defaultdict
from typing import List, Set, Tuple

from logic.name_normalizer import NameNormalizer
from config.p4_config import P4Config


class BlockingStrategy:
    """Generate candidate pairs using blocking keys to reduce O(n^2) comparisons."""
    
    def __init__(self):
        """Initialize blocking strategy."""
        self.normalizer = NameNormalizer()
    
    def generate_blocking_keys(self, name: str) -> List[str]:
        """
        Generate multiple blocking keys for a name.
        
        Args:
            name: Company name
            
        Returns:
            List of blocking keys
        """
        keys = []
        normalized = self.normalizer.normalize(name)
        
        if not normalized:
            return keys
        
        tokens = normalized.split()
        
        # Key 1: First token
        if tokens:
            keys.append(f"first:{tokens[0]}")
        
        # Key 2: First 3 characters
        if normalized:
            keys.append(f"prefix:{normalized[:3]}")
        
        # Key 3: Sorted token signature
        if tokens:
            sorted_sig = ''.join(sorted(tokens))[:10]
            keys.append(f"sig:{sorted_sig}")
        
        # Key 4: Length bucket
        length_bucket = len(normalized) // 10
        keys.append(f"len:{length_bucket}")
        
        return keys
    
    def generate_candidates(
        self,
        names: List[str]
    ) -> List[Tuple[str, str]]:
        """
        Generate candidate pairs using blocking.
        
        Args:
            names: List of company names
            
        Returns:
            List of (name1, name2) candidate pairs
        """
        # Build inverted index: block_key -> [names]
        blocks = defaultdict(list)
        
        for name in names:
            keys = self.generate_blocking_keys(name)
            for key in keys:
                blocks[key].append(name)
        
        # Generate candidate pairs within blocks
        candidates: Set[Tuple[str, str]] = set()
        
        for block_key, block_names in blocks.items():
            # Skip if block too small or too large
            if len(block_names) < P4Config.MIN_BLOCK_SIZE:
                continue
            if len(block_names) > P4Config.MAX_BLOCK_SIZE:
                continue
            
            # Generate pairs within block
            for i in range(len(block_names)):
                for j in range(i + 1, len(block_names)):
                    name1, name2 = block_names[i], block_names[j]
                    # Ensure consistent ordering
                    pair = tuple(sorted([name1, name2]))
                    candidates.add(pair)
        
        return list(candidates)

