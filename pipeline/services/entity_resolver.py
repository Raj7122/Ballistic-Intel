"""
Entity Resolution Service.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

from typing import List, Dict, Any, Tuple
from collections import defaultdict

from logic.name_normalizer import NameNormalizer
from logic.similarity import SimilarityCalculator
from logic.blocking import BlockingStrategy
from logic.clusterer import Clusterer
from models import ResolvedEntity, AliasLink, create_resolved_entities, create_alias_links


class EntityResolver:
    """
    Resolve and deduplicate company names.
    
    Orchestrates normalization, blocking, similarity, and clustering.
    """
    
    def __init__(self):
        """Initialize entity resolver."""
        self.normalizer = NameNormalizer()
        self.similarity = SimilarityCalculator()
        self.blocking = BlockingStrategy()
        self.clusterer = Clusterer()
        
        self.stats: Dict[str, Any] = {
            "total_names": 0,
            "unique_normalized": 0,
            "candidate_pairs": 0,
            "matches_found": 0,
            "clusters_formed": 0,
            "avg_cluster_size": 0.0,
            "processing_time": 0.0
        }
    
    def resolve(
        self,
        names: List[str],
        sources: Dict[str, List[str]] = None
    ) -> Tuple[List[ResolvedEntity], List[AliasLink], Dict[str, Any]]:
        """
        Resolve company names to canonical entities.
        
        Args:
            names: List of company names
            sources: Optional dict mapping name to list of sources
            
        Returns:
            Tuple of (resolved_entities, alias_links, statistics)
        """
        import time
        start_time = time.time()
        
        if sources is None:
            sources = {name: ["unknown"] for name in names}
        
        # Deduplicate input
        unique_names = list(set(names))
        self.stats["total_names"] = len(names)
        self.stats["unique_normalized"] = len(unique_names)
        
        # Generate candidate pairs via blocking
        candidates = self.blocking.generate_candidates(unique_names)
        self.stats["candidate_pairs"] = len(candidates)
        
        # Score pairs and find matches
        matches = []
        for name1, name2 in candidates:
            is_match, score, rules = self.similarity.is_match(name1, name2)
            if is_match:
                matches.append((name1, name2, score, rules))
        
        self.stats["matches_found"] = len(matches)
        
        # Cluster matched names
        clusters = self.clusterer.cluster_names(matches)
        self.stats["clusters_formed"] = len(clusters)
        
        # Calculate avg cluster size
        if clusters:
            total_members = sum(len(members) for members in clusters.values())
            self.stats["avg_cluster_size"] = total_members / len(clusters)
        
        # Build canonical map and scores
        canonical_map: Dict[str, str] = {}
        scores_map: Dict[str, float] = {}
        rules_map: Dict[str, List[str]] = {}
        
        for canonical, aliases in clusters.items():
            for alias in aliases:
                canonical_map[alias] = canonical
                scores_map[alias] = 1.0  # Default confidence
                rules_map[alias] = ["clustered"]
        
        # Add singleton clusters (names that didn't match anything)
        for name in unique_names:
            if name not in canonical_map:
                canonical_map[name] = name
                scores_map[name] = 1.0
                rules_map[name] = ["singleton"]
                clusters[name] = [name]
        
        # Create resolved entities
        entities = create_resolved_entities(clusters, canonical_map, scores_map, sources)
        
        # Create alias links
        links = create_alias_links(canonical_map, scores_map, rules_map)
        
        self.stats["processing_time"] = time.time() - start_time
        
        return entities, links, dict(self.stats)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get resolution statistics."""
        return dict(self.stats)

