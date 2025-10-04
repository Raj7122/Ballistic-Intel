"""
ExtractionResult data model for Agent P3 - Extraction & Classification.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Literal, List, Dict, Any

from models.relevance import normalize_category


@dataclass
class ExtractionResult:
    """
    Result of entity extraction and sector classification.
    
    Attributes:
        item_id: Unique identifier of the source item
        source_type: Type of source ("patent" or "news")
        company_names: Extracted company names (unique, ≤5)
        sector: Cybersecurity sector (normalized to P2 categories)
        novelty_score: Innovation/novelty score (0.0-1.0)
        tech_keywords: Technical keywords (≤10)
        rationale: Reasoning for classification (1-4 items)
        model: Model/method used
        model_version: Version of the model
        timestamp: When extraction was performed
        hash: Content hash for caching
    """
    
    item_id: str
    source_type: Literal["patent", "news"]
    company_names: List[str]
    sector: str
    novelty_score: float
    tech_keywords: List[str]
    rationale: List[str]
    model: str
    model_version: str
    timestamp: datetime
    hash: str = ""
    
    def __post_init__(self):
        """Validate and normalize fields."""
        # Clamp novelty score to [0.0, 1.0]
        self.novelty_score = max(0.0, min(1.0, self.novelty_score))
        
        # Normalize sector to P2 categories
        self.sector = normalize_category(self.sector)
        
        # Deduplicate and limit company names
        seen = set()
        unique_companies = []
        for company in self.company_names:
            company_clean = company.strip()
            if company_clean and company_clean.lower() not in seen:
                seen.add(company_clean.lower())
                unique_companies.append(company_clean)
        self.company_names = unique_companies[:5]  # Limit to 5
        
        # Deduplicate and limit tech keywords
        seen = set()
        unique_keywords = []
        for keyword in self.tech_keywords:
            keyword_clean = keyword.strip().lower()
            if keyword_clean and keyword_clean not in seen:
                seen.add(keyword_clean)
                unique_keywords.append(keyword_clean)
        self.tech_keywords = unique_keywords[:10]  # Limit to 10
        
        # Ensure rationale is a list and limit to 4
        if not isinstance(self.rationale, list):
            self.rationale = [str(self.rationale)]
        self.rationale = self.rationale[:4]
        
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
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractionResult":
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
    ) -> "ExtractionResult":
        """
        Create ExtractionResult from LLM JSON response.
        
        Args:
            item_id: Source item ID
            source_type: "patent" or "news"
            llm_response: Parsed JSON from LLM
            content_hash: Hash of input content for caching
            
        Returns:
            ExtractionResult instance
        """
        return cls(
            item_id=item_id,
            source_type=source_type,
            company_names=llm_response.get('company_names', []),
            sector=llm_response.get('sector', 'unknown'),
            novelty_score=float(llm_response.get('novelty_score', 0.5)),
            tech_keywords=llm_response.get('tech_keywords', []),
            rationale=llm_response.get('rationale', []),
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
        company_names: List[str],
        sector: str,
        novelty_score: float,
        tech_keywords: List[str],
        rationale: List[str],
        content_hash: str
    ) -> "ExtractionResult":
        """
        Create ExtractionResult from heuristic analysis.
        
        Args:
            item_id: Source item ID
            source_type: "patent" or "news"
            company_names: Extracted companies
            sector: Detected sector
            novelty_score: Novelty estimation
            tech_keywords: Extracted keywords
            rationale: Reasoning
            content_hash: Hash of input content
            
        Returns:
            ExtractionResult instance
        """
        return cls(
            item_id=item_id,
            source_type=source_type,
            company_names=company_names,
            sector=sector,
            novelty_score=novelty_score,
            tech_keywords=tech_keywords,
            rationale=rationale,
            model="heuristic-v1",
            model_version="1.0",
            timestamp=datetime.utcnow(),
            hash=content_hash
        )

