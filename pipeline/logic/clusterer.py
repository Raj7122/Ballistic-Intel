"""
Clustering and canonical selection for entity resolution.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set, Tuple

from logic.name_normalizer import NameNormalizer
from config.p4_config import P4Config


class UnionFind:
    """Union-Find data structure for clustering."""
    
    def __init__(self):
        """Initialize Union-Find."""
        self.parent: Dict[str, str] = {}
        self.rank: Dict[str, int] = {}
    
    def find(self, x: str) -> str:
        """Find root with path compression."""
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
            return x
        
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        
        return self.parent[x]
    
    def union(self, x: str, y: str) -> bool:
        """
        Union two elements.
        
        Returns:
            True if union was performed, False if already in same set
        """
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False
        
        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        return True
    
    def get_clusters(self) -> Dict[str, List[str]]:
        """
        Get all clusters.
        
        Returns:
            Dict mapping root to list of members
        """
        clusters = defaultdict(list)
        
        for element in list(self.parent.keys()):
            root = self.find(element)
            clusters[root].append(element)
        
        return dict(clusters)


class Clusterer:
    """Cluster names and select canonical forms."""
    
    def __init__(self):
        """Initialize clusterer."""
        self.normalizer = NameNormalizer()
    
    def cluster_names(
        self,
        matches: List[Tuple[str, str, float, List[str]]]
    ) -> Dict[str, List[str]]:
        """
        Cluster names based on pairwise matches.
        
        Args:
            matches: List of (name1, name2, score, rules) tuples
            
        Returns:
            Dict mapping canonical_name to list of aliases
        """
        uf = UnionFind()
        
        # Build clusters via union-find
        for name1, name2, score, rules in matches:
            uf.union(name1, name2)
        
        # Get raw clusters
        raw_clusters = uf.get_clusters()
        
        # Filter and validate clusters
        filtered_clusters = {}
        
        for root, members in raw_clusters.items():
            # Enforce max cluster size
            if len(members) > P4Config.MAX_CLUSTER_SIZE:
                # Split large cluster (keep as singleton clusters)
                for member in members:
                    filtered_clusters[member] = [member]
            else:
                # Select canonical name
                canonical = self.select_canonical(members)
                filtered_clusters[canonical] = members
        
        return filtered_clusters
    
    def select_canonical(self, names: List[str]) -> str:
        """
        Select canonical name from a cluster.
        
        Args:
            names: List of names in cluster
            
        Returns:
            Canonical name
        """
        if not names:
            return ""
        
        if len(names) == 1:
            return names[0]
        
        strategy = P4Config.CANONICAL_STRATEGY
        
        if strategy == 'longest':
            # Choose longest after normalization
            normalized_lengths = [(name, len(self.normalizer.normalize(name))) for name in names]
            return max(normalized_lengths, key=lambda x: x[1])[0]
        
        elif strategy == 'most_frequent':
            # Choose most frequent (requires external frequency data)
            # For now, fall back to longest
            return self.select_canonical_longest(names)
        
        elif strategy == 'highest_score':
            # Choose one with highest avg similarity to others (expensive)
            # For now, fall back to longest
            return self.select_canonical_longest(names)
        
        else:
            return self.select_canonical_longest(names)
    
    def select_canonical_longest(self, names: List[str]) -> str:
        """Select longest normalized name."""
        normalized_lengths = [(name, len(self.normalizer.normalize(name))) for name in names]
        # Sort by length desc, then alphabetically for determinism
        sorted_names = sorted(normalized_lengths, key=lambda x: (-x[1], x[0]))
        return sorted_names[0][0]

