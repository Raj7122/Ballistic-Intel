"""
Heuristic fallback for extraction and classification when LLM is unavailable.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import hashlib
import re
from typing import Tuple, List

from models import Patent, NewsArticle, ExtractionResult
from logic.relevance_heuristics import RelevanceHeuristics


class ExtractionHeuristics:
    """
    Heuristic-based extraction and classification for patents and news.
    
    Strategy:
    - Reuse P2 RelevanceHeuristics for sector detection
    - Company extraction via patterns and known entities
    - Novelty scoring based on keywords and CPC codes
    - Tech keyword extraction from P2 keyword lists
    """
    
    # Novelty indicators for patents
    PATENT_NOVELTY_HIGH = {
        'novel', 'innovative', 'breakthrough', 'new method', 'new system',
        'first', 'unprecedented', 'revolutionary', 'advanced'
    }
    
    PATENT_NOVELTY_MED = {
        'improved', 'enhanced', 'optimized', 'efficient', 'method for',
        'system for', 'apparatus for'
    }
    
    # Novelty indicators for news
    NEWS_NOVELTY_HIGH = {
        'launches', 'unveils', 'introduces', 'announces new', 'revolutionary',
        'first-of-its-kind', 'breakthrough', 'innovative platform'
    }
    
    NEWS_NOVELTY_MED = {
        'new product', 'new platform', 'new feature', 'enhanced'
    }
    
    # Company name patterns for news
    COMPANY_PATTERNS = [
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:announced|raised|secured|launched|unveiled|closed)',
        r'(?:led by|co-led by|from|by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})',
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:has|will)',
    ]
    
    # Common non-company words to exclude
    EXCLUDE_WORDS = {
        'the', 'a', 'an', 'this', 'that', 'these', 'those',
        'cisa', 'fbi', 'nsa', 'cve', 'owasp',  # Orgs/standards
        'series', 'round', 'funding', 'million', 'billion'
    }
    
    def __init__(self):
        """Initialize extraction heuristics."""
        self.relevance_heuristics = RelevanceHeuristics()
    
    def extract_patent(self, patent: Patent) -> ExtractionResult:
        """
        Extract structured data from patent.
        
        Args:
            patent: Patent object
            
        Returns:
            ExtractionResult
        """
        # Combine text for analysis
        text = f"{patent.title} {patent.abstract}".lower()
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        
        # Extract companies from assignees
        company_names = self._normalize_company_names(patent.assignees)
        
        # Detect sector using relevance heuristics
        relevance = self.relevance_heuristics.classify_patent(patent)
        sector = relevance.category
        
        # Calculate novelty score
        novelty_score = self._calculate_patent_novelty(patent, text)
        
        # Extract tech keywords
        tech_keywords = self._extract_tech_keywords(text)
        
        # Generate rationale
        rationale = []
        if company_names:
            rationale.append(f"Assigned to {', '.join(company_names[:2])}")
        if patent.cpc_codes:
            rationale.append(f"CPC codes: {', '.join(patent.cpc_codes[:3])}")
        rationale.append(f"Sector: {sector}")
        
        return ExtractionResult.create_heuristic(
            item_id=patent.publication_number,
            source_type='patent',
            company_names=company_names,
            sector=sector,
            novelty_score=novelty_score,
            tech_keywords=tech_keywords,
            rationale=rationale[:4],
            content_hash=content_hash
        )
    
    def extract_news(self, article: NewsArticle) -> ExtractionResult:
        """
        Extract structured data from news article.
        
        Args:
            article: NewsArticle object
            
        Returns:
            ExtractionResult
        """
        # Combine text for analysis
        text = article.get_text_for_analysis().lower()
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        
        # Extract company names
        company_names = self._extract_companies_from_news(article)
        
        # Detect sector using relevance heuristics
        relevance = self.relevance_heuristics.classify_news(article)
        sector = relevance.category
        
        # Calculate novelty score
        novelty_score = self._calculate_news_novelty(text)
        
        # Extract tech keywords
        tech_keywords = self._extract_tech_keywords(text)
        
        # Generate rationale
        rationale = []
        if company_names:
            rationale.append(f"Mentions {', '.join(company_names[:2])}")
        if 'funding' in text or 'raised' in text:
            rationale.append("Funding announcement")
        rationale.append(f"Sector: {sector}")
        
        return ExtractionResult.create_heuristic(
            item_id=article.id,
            source_type='news',
            company_names=company_names,
            sector=sector,
            novelty_score=novelty_score,
            tech_keywords=tech_keywords,
            rationale=rationale[:4],
            content_hash=content_hash
        )
    
    def _normalize_company_names(self, names: List[str]) -> List[str]:
        """
        Normalize company names (remove legal suffixes, dedupe).
        
        Args:
            names: Raw company names
            
        Returns:
            Normalized company names
        """
        normalized = []
        seen = set()
        
        for name in names:
            # Remove common legal suffixes
            clean = re.sub(
                r'\s+(Inc\.?|Corp\.?|Ltd\.?|LLC|Co\.?|LP|LLP)$',
                '',
                name.strip(),
                flags=re.IGNORECASE
            )
            clean = clean.strip()
            
            if clean and clean.lower() not in seen:
                seen.add(clean.lower())
                normalized.append(clean)
        
        return normalized[:5]  # Limit to 5
    
    def _extract_companies_from_news(self, article: NewsArticle) -> List[str]:
        """
        Extract company names from news article text.
        
        Args:
            article: NewsArticle object
            
        Returns:
            List of company names
        """
        text = f"{article.title} {article.summary}"
        companies = []
        seen = set()
        
        # Apply regex patterns
        for pattern in self.COMPANY_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                clean = match.strip()
                if clean.lower() not in self.EXCLUDE_WORDS and clean.lower() not in seen:
                    seen.add(clean.lower())
                    companies.append(clean)
        
        return companies[:5]  # Limit to 5
    
    def _calculate_patent_novelty(self, patent: Patent, text: str) -> float:
        """
        Calculate novelty score for patent.
        
        Args:
            patent: Patent object
            text: Lowercased combined text
            
        Returns:
            Novelty score 0.0-1.0
        """
        score = 0.5  # Base score
        
        # Check novelty keywords
        high_count = sum(1 for kw in self.PATENT_NOVELTY_HIGH if kw in text)
        med_count = sum(1 for kw in self.PATENT_NOVELTY_MED if kw in text)
        
        score += min(0.3, high_count * 0.15)
        score += min(0.15, med_count * 0.05)
        
        # Boost for certain CPC codes (new methods)
        if any(cpc.startswith('H04L9') for cpc in patent.cpc_codes):  # Crypto
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_news_novelty(self, text: str) -> float:
        """
        Calculate novelty score for news article.
        
        Args:
            text: Lowercased article text
            
        Returns:
            Novelty score 0.0-1.0
        """
        score = 0.3  # Base score (lower for news)
        
        # Check novelty keywords
        high_count = sum(1 for kw in self.NEWS_NOVELTY_HIGH if kw in text)
        med_count = sum(1 for kw in self.NEWS_NOVELTY_MED if kw in text)
        
        score += min(0.4, high_count * 0.2)
        score += min(0.2, med_count * 0.1)
        
        # Reduce for pure funding announcements
        if 'raised' in text and 'million' in text and 'series' in text:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _extract_tech_keywords(self, text: str) -> List[str]:
        """
        Extract technical keywords from text.
        
        Args:
            text: Lowercased text
            
        Returns:
            List of tech keywords
        """
        keywords = []
        seen = set()
        
        # Reuse keyword lists from RelevanceHeuristics
        all_keywords = (
            self.relevance_heuristics.HIGH_CONFIDENCE_KEYWORDS |
            self.relevance_heuristics.MEDIUM_CONFIDENCE_KEYWORDS
        )
        
        for keyword in all_keywords:
            if keyword in text and keyword not in seen:
                seen.add(keyword)
                keywords.append(keyword)
                if len(keywords) >= 10:
                    break
        
        return keywords

