"""
Extract funding data from newsletter articles using Gemini.
Used by Agent P3 (Extraction & Classification).

This module provides high-level functions to extract structured funding
information from unstructured cybersecurity news articles.

Functions:
    extract_funding_data: Extract complete funding round information
    extract_company_sector: Classify cybersecurity sub-sector
    
Security:
    - Input sanitization for article text
    - Rate limiting handled by GeminiClient
    - Error handling with detailed logging

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
import json
import re
from typing import Optional, Dict, List
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from clients.gemini_client import GeminiClient


# Prompt templates
FUNDING_EXTRACTION_PROMPT = """
You are a venture capital analyst specializing in cybersecurity investments.
Extract funding information from this news article.

Article:
{article_text}

Return ONLY valid JSON with these fields (use null if information not found):
{{
  "company": "Full company name",
  "amount": "Funding amount with M/B suffix (e.g., $150M, $1.2B)",
  "stage": "Funding stage (Seed/Series A/Series B/Series C/Series D/Series E/Series F)",
  "lead_investor": "Name of lead investor",
  "other_investors": ["Investor 1", "Investor 2"],
  "valuation": "Post-money valuation if mentioned (e.g., $2.6B)",
  "sector": "Specific cybersecurity sub-sector (Cloud Security, Endpoint Security, etc.)",
  "use_of_funds": "Brief description of planned use of funds",
  "confidence": 0.95
}}

Important:
- Extract exact company names as written
- Normalize funding amounts to standard format ($150M not $150 million)
- Only include information explicitly stated in the article
- Confidence should be 0.0-1.0 based on clarity of information
- If this is NOT a funding announcement, return {{"is_funding_announcement": false}}

JSON:
"""

SECTOR_CLASSIFICATION_PROMPT = """
Classify this cybersecurity company into the most specific sub-sector.

Company: {company_name}
Description: {description}

Available sectors:
- Cloud Security
- Endpoint Security
- Network Security
- Identity & Access Management (IAM)
- Security Analytics / SIEM
- Vulnerability Management
- DevSecOps / Application Security
- Data Security / Encryption
- Zero Trust
- Threat Intelligence
- Email Security
- Web Application Firewall (WAF)
- Security Orchestration (SOAR)
- Managed Security Services (MSSP)
- Other

Return ONLY JSON:
{{
  "primary_sector": "Most specific sector",
  "secondary_sectors": ["Other relevant sectors"],
  "confidence": 0.95
}}

JSON:
"""


class FundingExtractor:
    """
    Extract structured funding data from unstructured articles.
    
    Attributes:
        client (GeminiClient): Gemini API client instance
        cache (dict): In-memory cache for repeated extractions
    """
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize funding extractor.
        
        Args:
            gemini_client: Optional pre-configured client (creates new if None)
        """
        self.client = gemini_client or GeminiClient()
        self.cache: Dict[str, dict] = {}
        
    def _sanitize_article_text(self, text: str) -> str:
        """
        Sanitize article text before sending to API.
        
        Args:
            text: Raw article text
            
        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove HTML tags if any
        text = re.sub(r'<[^>]+>', '', text)
        
        # Limit length to 5000 chars (reasonable article length)
        if len(text) > 5000:
            text = text[:5000] + "..."
            
        return text.strip()
        
    def extract_funding_data(
        self, 
        article_text: str,
        article_url: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Extract structured funding data from article text.
        
        Args:
            article_text: Full article content
            article_url: Optional URL for caching
            
        Returns:
            dict: Structured funding data or None if not a funding announcement
            
        Example:
            >>> extractor = FundingExtractor()
            >>> data = extractor.extract_funding_data(article_text)
            >>> if data:
            ...     print(f"{data['company']} raised {data['amount']}")
        """
        # Check cache first
        cache_key = article_url or article_text[:100]
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Sanitize input
        clean_text = self._sanitize_article_text(article_text)
        
        # Generate prompt
        prompt = FUNDING_EXTRACTION_PROMPT.format(
            article_text=clean_text
        )
        
        try:
            # Extract data
            result = self.client.generate_json(prompt)
            
            # Check if this is actually a funding announcement
            if result.get('is_funding_announcement') is False:
                return None
            
            # Validate required fields
            required_fields = ['company', 'amount', 'stage']
            if not all(result.get(field) for field in required_fields):
                print(f"⚠️  Missing required fields in extraction: {result}")
                return None
            
            # Check confidence threshold
            confidence = result.get('confidence', 0.0)
            if confidence < 0.5:
                print(f"⚠️  Low confidence extraction ({confidence}): {result}")
                return None
            
            # Cache result
            self.cache[cache_key] = result
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON from Gemini response: {e}")
            return None
        except Exception as e:
            print(f"❌ Error extracting funding data: {e}")
            return None
            
    def extract_company_sector(
        self,
        company_name: str,
        description: str
    ) -> Optional[Dict]:
        """
        Classify company into cybersecurity sub-sector.
        
        Args:
            company_name: Company name
            description: Company description or product info
            
        Returns:
            dict: Sector classification with confidence
            
        Example:
            >>> extractor = FundingExtractor()
            >>> sector = extractor.extract_company_sector(
            ...     "Wiz",
            ...     "Cloud security posture management (CSPM)"
            ... )
            >>> print(sector['primary_sector'])
            Cloud Security
        """
        # Sanitize description
        clean_desc = self._sanitize_article_text(description)
        
        # Generate prompt
        prompt = SECTOR_CLASSIFICATION_PROMPT.format(
            company_name=company_name,
            description=clean_desc
        )
        
        try:
            result = self.client.generate_json(prompt)
            return result
            
        except Exception as e:
            print(f"❌ Error classifying sector: {e}")
            return None
            
    def batch_extract(
        self,
        articles: List[Dict[str, str]]
    ) -> List[Optional[Dict]]:
        """
        Extract funding data from multiple articles.
        
        Args:
            articles: List of dicts with 'text' and optional 'url' keys
            
        Returns:
            List[Optional[Dict]]: Extracted data for each article
            
        Example:
            >>> articles = [
            ...     {'text': 'Company X raised $50M...', 'url': 'http://...'},
            ...     {'text': 'Company Y raised $100M...', 'url': 'http://...'}
            ... ]
            >>> results = extractor.batch_extract(articles)
        """
        results = []
        
        for i, article in enumerate(articles):
            print(f"Processing article {i+1}/{len(articles)}...")
            
            data = self.extract_funding_data(
                article_text=article.get('text', ''),
                article_url=article.get('url')
            )
            
            results.append(data)
            
        return results
        
    def clear_cache(self):
        """Clear the extraction cache."""
        self.cache.clear()


# Convenience function for one-off extractions
def extract_funding_data(article_text: str) -> Optional[Dict]:
    """
    Convenience function to extract funding data without creating extractor instance.
    
    Args:
        article_text: Article content
        
    Returns:
        dict: Funding data or None
    """
    extractor = FundingExtractor()
    return extractor.extract_funding_data(article_text)

