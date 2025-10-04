"""
RelevanceResult data model for Agent P2 - Universal Relevance Filter.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Literal, List, Dict, Any, Optional


@dataclass
class RelevanceResult:
    """
    Result of relevance classification for a patent or news article.
    
    Attributes:
        item_id: Unique identifier of the source item
        source_type: Type of source ("patent" or "news")
        is_relevant: Whether item is cybersecurity-relevant
        score: Confidence score (0.0-1.0)
        category: Cybersecurity category
        reasons: List of reasoning/justifications
        model: Model/method used ("gemini-2.5-flash" or "heuristic-v1")
        model_version: Version of the model
        timestamp: When classification was performed
        hash: Content hash for deduplication/caching
    """
    
    item_id: str
    source_type: Literal["patent", "news"]
    is_relevant: bool
    score: float
    category: str
    reasons: List[str]
    model: str
    model_version: str
    timestamp: datetime
    hash: str = ""
    
    def __post_init__(self):
        """Validate and normalize fields."""
        # Clamp score to [0.0, 1.0]
        self.score = max(0.0, min(1.0, self.score))
        
        # Normalize category to lowercase
        self.category = self.category.lower().strip()
        
        # Ensure reasons is a list
        if not isinstance(self.reasons, list):
            self.reasons = [str(self.reasons)]
        
        # Generate hash if not provided
        if not self.hash:
            hash_input = f"{self.item_id}:{self.source_type}:{self.model}"
            self.hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RelevanceResult":
        """Create from dictionary."""
        data = dict(data)  # Copy to avoid mutation
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    @classmethod
    def create_from_llm_response(
        cls,
        item_id: str,
        source_type: Literal["patent", "news"],
        llm_response: Dict[str, Any],
        content_hash: str
    ) -> "RelevanceResult":
        """
        Create RelevanceResult from LLM JSON response.
        
        Args:
            item_id: Source item ID
            source_type: "patent" or "news"
            llm_response: Parsed JSON from LLM
            content_hash: Hash of input content for caching
            
        Returns:
            RelevanceResult instance
        """
        return cls(
            item_id=item_id,
            source_type=source_type,
            is_relevant=llm_response.get('is_relevant', False),
            score=float(llm_response.get('score', 0.0)),
            category=llm_response.get('category', 'unknown'),
            reasons=llm_response.get('reasons', []),
            model=llm_response.get('model', 'gemini-2.5-flash'),
            model_version=llm_response.get('model_version', 'v1'),
            timestamp=datetime.utcnow(),
            hash=content_hash
        )
    
    @classmethod
    def create_heuristic(
        cls,
        item_id: str,
        source_type: Literal["patent", "news"],
        is_relevant: bool,
        score: float,
        category: str,
        reasons: List[str],
        content_hash: str
    ) -> "RelevanceResult":
        """
        Create RelevanceResult from heuristic analysis.
        
        Args:
            item_id: Source item ID
            source_type: "patent" or "news"
            is_relevant: Relevance flag
            score: Confidence score
            category: Detected category
            reasons: Reasoning
            content_hash: Hash of input content
            
        Returns:
            RelevanceResult instance
        """
        return cls(
            item_id=item_id,
            source_type=source_type,
            is_relevant=is_relevant,
            score=score,
            category=category,
            reasons=reasons,
            model="heuristic-v1",
            model_version="1.0",
            timestamp=datetime.utcnow(),
            hash=content_hash
        )


# Valid cybersecurity categories
VALID_CATEGORIES = {
    "cloud",
    "network",
    "endpoint",
    "identity",
    "vulnerability",
    "malware",
    "data",
    "governance",
    "cryptography",
    "application",
    "iot",
    "unknown"
}


def normalize_category(category: str) -> str:
    """
    Normalize category to valid set.
    
    Args:
        category: Raw category string
        
    Returns:
        Normalized category from VALID_CATEGORIES
    """
    category = category.lower().strip()
    
    # Direct match
    if category in VALID_CATEGORIES:
        return category
    
    # Fuzzy matching
    mappings = {
        "vuln": "vulnerability",
        "cve": "vulnerability",
        "crypto": "cryptography",
        "encryption": "cryptography",
        "iam": "identity",
        "access": "identity",
        "auth": "identity",
        "sec": "network",
        "cloud security": "cloud",
        "endpoint protection": "endpoint",
        "threat": "malware",
        "ransomware": "malware",
        "compliance": "governance",
        "policy": "governance",
    }
    
    for key, value in mappings.items():
        if key in category:
            return value
    
    return "unknown"

