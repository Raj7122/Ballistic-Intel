"""
Entity resolution data models for Agent P4.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any


@dataclass
class ResolvedEntity:
    """
    Represents a canonical company entity with its aliases.
    
    Attributes:
        entity_id: Stable hash-based identifier
        canonical_name: Normalized canonical name
        aliases: List of all raw names mapped to this entity
        sources: List of sources where entity was mentioned
        confidence: Average confidence score for cluster
        created_at: Timestamp of resolution
    """
    
    entity_id: str
    canonical_name: str
    aliases: List[str]
    sources: List[str]
    confidence: float
    created_at: datetime
    
    def __post_init__(self):
        """Validate and ensure uniqueness."""
        # Deduplicate aliases and sources
        self.aliases = list(dict.fromkeys(self.aliases))  # Preserve order
        self.sources = list(dict.fromkeys(self.sources))
        
        # Clamp confidence
        self.confidence = max(0.0, min(1.0, self.confidence))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            'entity_id': self.entity_id,
            'canonical_name': self.canonical_name,
            'aliases': self.aliases,
            'sources': self.sources,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResolvedEntity":
        """Create from dictionary."""
        data = dict(data)  # Copy
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)
    
    @classmethod
    def create_entity_id(cls, canonical_name: str) -> str:
        """
        Generate stable entity ID from canonical name.
        
        Args:
            canonical_name: Normalized canonical name
            
        Returns:
            SHA-256 hash (first 16 chars)
        """
        return hashlib.sha256(canonical_name.lower().encode()).hexdigest()[:16]


@dataclass
class AliasLink:
    """
    Represents a mapping from raw name to canonical entity.
    
    Attributes:
        raw_name: Original company name as extracted
        canonical_name: Resolved canonical name
        entity_id: ID of the canonical entity
        score: Similarity/confidence score
        rules_applied: List of normalization/matching rules used
    """
    
    raw_name: str
    canonical_name: str
    entity_id: str
    score: float
    rules_applied: List[str]
    
    def __post_init__(self):
        """Validate."""
        self.score = max(0.0, min(1.0, self.score))
        self.rules_applied = list(dict.fromkeys(self.rules_applied))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AliasLink":
        """Create from dictionary."""
        return cls(**data)


def create_resolved_entities(
    clusters: Dict[str, List[str]],
    canonical_map: Dict[str, str],
    scores: Dict[str, float],
    sources: Dict[str, List[str]]
) -> List[ResolvedEntity]:
    """
    Create ResolvedEntity objects from clustering results.
    
    Args:
        clusters: {canonical_name: [alias1, alias2, ...]}
        canonical_map: {raw_name: canonical_name}
        scores: {raw_name: confidence_score}
        sources: {raw_name: [source1, source2, ...]}
        
    Returns:
        List of ResolvedEntity objects
    """
    entities = []
    
    for canonical_name, aliases in clusters.items():
        # Calculate average confidence
        alias_scores = [scores.get(alias, 1.0) for alias in aliases]
        avg_confidence = sum(alias_scores) / len(alias_scores) if alias_scores else 1.0
        
        # Collect sources
        entity_sources = []
        for alias in aliases:
            entity_sources.extend(sources.get(alias, []))
        entity_sources = list(dict.fromkeys(entity_sources))
        
        # Create entity
        entity_id = ResolvedEntity.create_entity_id(canonical_name)
        entity = ResolvedEntity(
            entity_id=entity_id,
            canonical_name=canonical_name,
            aliases=aliases,
            sources=entity_sources,
            confidence=avg_confidence,
            created_at=datetime.utcnow()
        )
        entities.append(entity)
    
    return entities


def create_alias_links(
    canonical_map: Dict[str, str],
    scores: Dict[str, float],
    rules: Dict[str, List[str]]
) -> List[AliasLink]:
    """
    Create AliasLink objects from resolution mappings.
    
    Args:
        canonical_map: {raw_name: canonical_name}
        scores: {raw_name: confidence_score}
        rules: {raw_name: [rule1, rule2, ...]}
        
    Returns:
        List of AliasLink objects
    """
    links = []
    
    for raw_name, canonical_name in canonical_map.items():
        entity_id = ResolvedEntity.create_entity_id(canonical_name)
        link = AliasLink(
            raw_name=raw_name,
            canonical_name=canonical_name,
            entity_id=entity_id,
            score=scores.get(raw_name, 1.0),
            rules_applied=rules.get(raw_name, [])
        )
        links.append(link)
    
    return links

