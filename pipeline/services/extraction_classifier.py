"""
Extraction Classifier Service using Gemini LLM with heuristic fallback.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path
from typing import Union, Optional, Dict, Any
from datetime import datetime, timedelta

from clients.gemini_client import GeminiClient
from logic.extraction_heuristics import ExtractionHeuristics
from models import Patent, NewsArticle, ExtractionResult, normalize_category
from config.p3_config import P3Config


class ExtractionClassifier:
    """
    Extract structured data and classify sector using LLM or heuristics.
    
    Features:
    - Gemini LLM with structured prompt
    - JSON response parsing and validation
    - In-memory cache for deduplication
    - Heuristic fallback on LLM failure
    - Rate limiting via GeminiClient
    """
    
    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        enable_cache: bool = P3Config.ENABLE_CACHE,
        enable_fallback: bool = P3Config.ENABLE_FALLBACK
    ):
        """
        Initialize extraction classifier.
        
        Args:
            gemini_client: Optional GeminiClient instance
            enable_cache: Enable result caching
            enable_fallback: Enable heuristic fallback
        """
        self.gemini_client = gemini_client or GeminiClient(model=P3Config.LLM_MODEL)
        self.heuristics = ExtractionHeuristics()
        self.enable_cache = enable_cache
        self.enable_fallback = enable_fallback
        
        # Cache: {content_hash: (result, timestamp)}
        self._cache: Dict[str, tuple[ExtractionResult, datetime]] = {}
        
        # Load prompt template
        prompt_path = Path(__file__).parent.parent / "prompts" / "extraction_prompt.md"
        with open(prompt_path) as f:
            self.prompt_template = f.read()
    
    def extract(
        self,
        item: Union[Patent, NewsArticle],
        use_llm: bool = True
    ) -> ExtractionResult:
        """
        Extract structured data from an item.
        
        Args:
            item: Patent or NewsArticle
            use_llm: Whether to use LLM (false forces heuristics)
            
        Returns:
            ExtractionResult
        """
        # Prepare context
        if isinstance(item, Patent):
            source_type = 'patent'
            item_id = item.publication_number
            context = self._prepare_patent_context(item)
        elif isinstance(item, NewsArticle):
            source_type = 'news'
            item_id = item.id
            context = self._prepare_news_context(item)
        else:
            raise ValueError(f"Unsupported item type: {type(item)}")
        
        # Generate content hash
        content_hash = hashlib.sha256(context.encode()).hexdigest()[:16]
        
        # Check cache
        if self.enable_cache and content_hash in self._cache:
            cached_result, cached_time = self._cache[content_hash]
            if datetime.utcnow() - cached_time < timedelta(seconds=P3Config.CACHE_TTL_SECONDS):
                return cached_result
        
        # Try LLM extraction
        if use_llm:
            try:
                result = self._extract_with_llm(
                    item_id=item_id,
                    source_type=source_type,
                    context=context,
                    content_hash=content_hash
                )
                
                # Cache result
                if self.enable_cache:
                    self._cache[content_hash] = (result, datetime.utcnow())
                
                return result
                
            except Exception as exc:
                print(f"Warning: LLM extraction failed: {exc}")
                if not self.enable_fallback:
                    raise
        
        # Fallback to heuristics
        if isinstance(item, Patent):
            result = self.heuristics.extract_patent(item)
        else:
            result = self.heuristics.extract_news(item)
        
        # Cache fallback result
        if self.enable_cache:
            self._cache[content_hash] = (result, datetime.utcnow())
        
        return result
    
    def _prepare_patent_context(self, patent: Patent) -> str:
        """
        Prepare context string for patent.
        
        Args:
            patent: Patent object
            
        Returns:
            Context string (truncated to MAX_CONTEXT_LENGTH)
        """
        assignee_str = ', '.join(patent.assignees[:2]) if patent.assignees else 'N/A'
        context = (
            f"Type: patent\n"
            f"Title: {patent.title}\n"
            f"Abstract: {patent.abstract}\n"
            f"Assignee: {assignee_str}"
        )
        
        if len(context) > P3Config.MAX_CONTEXT_LENGTH:
            context = context[:P3Config.MAX_CONTEXT_LENGTH] + "..."
        
        return context
    
    def _prepare_news_context(self, article: NewsArticle) -> str:
        """
        Prepare context string for news article.
        
        Args:
            article: NewsArticle object
            
        Returns:
            Context string (truncated to MAX_CONTEXT_LENGTH)
        """
        # Use title + summary (or content if summary is short)
        if len(article.summary) < 100 and article.content_text:
            body = article.content_text[:700]
        else:
            body = article.summary
        
        context = f"Type: news\nTitle: {article.title}\nSummary: {body}"
        
        if len(context) > P3Config.MAX_CONTEXT_LENGTH:
            context = context[:P3Config.MAX_CONTEXT_LENGTH] + "..."
        
        return context
    
    def _extract_with_llm(
        self,
        item_id: str,
        source_type: str,
        context: str,
        content_hash: str
    ) -> ExtractionResult:
        """
        Extract using Gemini LLM.
        
        Args:
            item_id: Item identifier
            source_type: "patent" or "news"
            context: Prepared context string
            content_hash: Hash for caching
            
        Returns:
            ExtractionResult
            
        Raises:
            Exception: If LLM call or parsing fails
        """
        # Build full prompt
        prompt = f"{self.prompt_template}\n\n{context}"
        
        # Call LLM
        response_text = self.gemini_client.generate_content(
            prompt=prompt,
            temperature=P3Config.LLM_TEMPERATURE,
            max_output_tokens=P3Config.LLM_MAX_OUTPUT_TOKENS
        )
        
        # Parse JSON response
        llm_response = self._parse_json_response(response_text)
        
        # Validate and normalize
        llm_response['sector'] = normalize_category(llm_response.get('sector', 'unknown'))
        
        # Ensure arrays
        if not isinstance(llm_response.get('company_names'), list):
            llm_response['company_names'] = []
        if not isinstance(llm_response.get('tech_keywords'), list):
            llm_response['tech_keywords'] = []
        if not isinstance(llm_response.get('rationale'), list):
            llm_response['rationale'] = []
        
        # Create result
        result = ExtractionResult.create_from_llm_response(
            item_id=item_id,
            source_type=source_type,
            llm_response=llm_response,
            content_hash=content_hash
        )
        
        return result
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse and validate JSON response from LLM.
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Parsed JSON dict
            
        Raises:
            ValueError: If parsing fails
        """
        # Clean response (remove markdown code blocks if present)
        response_text = response_text.strip()
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse JSON response: {exc}")
        
        # Validate required fields
        required_fields = ['company_names', 'sector', 'novelty_score', 'tech_keywords', 'rationale']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return data
    
    def clear_cache(self):
        """Clear the result cache."""
        self._cache.clear()
    
    def get_cache_size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

