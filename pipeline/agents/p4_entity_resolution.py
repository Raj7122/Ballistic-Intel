"""
Agent P4: Entity Resolution for company name deduplication.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

from typing import List, Dict, Any, Tuple

from services.entity_resolver import EntityResolver
from models import ResolvedEntity, AliasLink


class EntityResolutionError(Exception):
    """Custom exception for entity resolution failures."""


class EntityResolutionAgent:
    """
    Agent P4: Entity Resolution.
    
    Responsibilities:
      1. Normalize and deduplicate company names
      2. Create canonical entity mappings
      3. Track provenance and confidence
      4. Provide statistics and audit trail
    """
    
    def __init__(self):
        """Initialize entity resolution agent."""
        self.resolver = EntityResolver()
    
    def resolve_entities(
        self,
        names: List[str],
        sources: Dict[str, List[str]] = None
    ) -> Tuple[List[ResolvedEntity], List[AliasLink], Dict[str, Any]]:
        """
        Resolve company names to canonical entities.
        
        Args:
            names: List of company names to resolve
            sources: Optional mapping of name to list of sources
            
        Returns:
            Tuple of (entities, alias_links, statistics)
        """
        if not names:
            return [], [], {
                "total_names": 0,
                "clusters_formed": 0,
                "avg_cluster_size": 0.0
            }
        
        entities, links, stats = self.resolver.resolve(names, sources)
        
        return entities, links, stats
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get resolution statistics."""
        return self.resolver.get_statistics()

