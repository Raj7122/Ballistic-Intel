"""
Agent P3: Extraction & Classification for patents and news articles.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import time
from typing import List, Union, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.extraction_classifier import ExtractionClassifier
from models import Patent, NewsArticle, ExtractionResult
from config.p3_config import P3Config


class ExtractionClassifierError(Exception):
    """Custom exception for extraction failures."""


class ExtractionClassifierAgent:
    """
    Agent P3: Extraction & Classification.
    
    Responsibilities:
      1. Extract company names from patents and news
      2. Classify items into cybersecurity sectors
      3. Assign novelty scores
      4. Extract technical keywords
      5. Track statistics and performance metrics
    """
    
    def __init__(
        self,
        *,
        max_workers: int = P3Config.MAX_WORKERS,
        enable_cache: bool = P3Config.ENABLE_CACHE
    ):
        """
        Initialize extraction classifier agent.
        
        Args:
            max_workers: Max concurrent workers (respects rate limits)
            enable_cache: Enable result caching
        """
        self.classifier = ExtractionClassifier(enable_cache=enable_cache)
        self.max_workers = max_workers
        
        self.stats: Dict[str, Any] = {
            "total_items": 0,
            "patents_processed": 0,
            "news_processed": 0,
            "companies_extracted": 0,
            "avg_novelty_score": 0.0,
            "llm_used": 0,
            "heuristic_fallback": 0,
            "errors": 0,
            "processing_time": 0.0,
            "cache_hits": 0,
            "sector_distribution": {},
        }
    
    def extract(
        self,
        items: List[Union[Patent, NewsArticle]],
        use_llm: bool = True
    ) -> tuple[List[ExtractionResult], Dict[str, Any]]:
        """
        Extract structured data from items.
        
        Args:
            items: List of Patent or NewsArticle objects
            use_llm: Whether to use LLM (false forces heuristics only)
            
        Returns:
            Tuple of (results, statistics)
        """
        start_time = time.time()
        results: List[ExtractionResult] = []
        
        initial_cache_size = self.classifier.get_cache_size()
        
        self.stats["total_items"] = len(items)
        
        # Process items with controlled concurrency
        if self.max_workers > 1 and len(items) > 1:
            results = self._process_concurrent(items, use_llm)
        else:
            results = self._process_sequential(items, use_llm)
        
        # Calculate statistics
        self.stats["processing_time"] = time.time() - start_time
        self._calculate_stats(results, items)
        self.stats["cache_hits"] = self.classifier.get_cache_size() - initial_cache_size
        
        return results, dict(self.stats)
    
    def _process_sequential(
        self,
        items: List[Union[Patent, NewsArticle]],
        use_llm: bool
    ) -> List[ExtractionResult]:
        """Process items sequentially."""
        results = []
        
        for item in items:
            try:
                result = self.classifier.extract(item, use_llm=use_llm)
                results.append(result)
                
                # Track model usage
                if result.model.startswith('gemini'):
                    self.stats["llm_used"] += 1
                elif result.model.startswith('heuristic'):
                    self.stats["heuristic_fallback"] += 1
                    
            except Exception as exc:
                self.stats["errors"] += 1
                print(f"Error extracting from item: {exc}")
                continue
        
        return results
    
    def _process_concurrent(
        self,
        items: List[Union[Patent, NewsArticle]],
        use_llm: bool
    ) -> List[ExtractionResult]:
        """Process items concurrently with worker pool."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(self.classifier.extract, item, use_llm): item
                for item in items
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_item):
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Track model usage
                    if result.model.startswith('gemini'):
                        self.stats["llm_used"] += 1
                    elif result.model.startswith('heuristic'):
                        self.stats["heuristic_fallback"] += 1
                        
                except Exception as exc:
                    self.stats["errors"] += 1
                    print(f"Error in concurrent extraction: {exc}")
                    continue
        
        return results
    
    def _calculate_stats(
        self,
        results: List[ExtractionResult],
        items: List[Union[Patent, NewsArticle]]
    ):
        """Calculate aggregate statistics from results."""
        if not results:
            return
        
        # Count source types
        self.stats["patents_processed"] = sum(
            1 for item in items if isinstance(item, Patent)
        )
        self.stats["news_processed"] = sum(
            1 for item in items if isinstance(item, NewsArticle)
        )
        
        # Count companies extracted
        total_companies = sum(len(r.company_names) for r in results)
        self.stats["companies_extracted"] = total_companies
        
        # Average novelty score
        total_novelty = sum(r.novelty_score for r in results)
        self.stats["avg_novelty_score"] = total_novelty / len(results) if results else 0.0
        
        # Sector distribution
        sector_counts: Dict[str, int] = {}
        for result in results:
            sector_counts[result.sector] = sector_counts.get(result.sector, 0) + 1
        self.stats["sector_distribution"] = sector_counts
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return extraction statistics."""
        return dict(self.stats)
    
    def clear_cache(self):
        """Clear the classifier cache."""
        self.classifier.clear_cache()

