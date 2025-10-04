"""
Agent P2: Universal Relevance Filter for patents and news articles.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import time
from typing import List, Union, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.relevance_classifier import RelevanceClassifier
from models import Patent, NewsArticle, RelevanceResult
from config.p2_config import P2Config


class RelevanceFilterError(Exception):
    """Custom exception for relevance filtering failures."""


class RelevanceFilterAgent:
    """
    Agent P2: Universal Relevance Filter.
    
    Responsibilities:
      1. Classify patents and news articles for cybersecurity relevance
      2. Use LLM (Gemini) with heuristic fallback
      3. Apply score threshold filtering
      4. Track statistics and performance metrics
    """
    
    def __init__(
        self,
        *,
        min_score: float = P2Config.MIN_RELEVANCE_SCORE,
        max_workers: int = P2Config.MAX_WORKERS,
        enable_cache: bool = P2Config.ENABLE_CACHE
    ):
        """
        Initialize relevance filter agent.
        
        Args:
            min_score: Minimum relevance score threshold
            max_workers: Max concurrent workers (respects rate limits)
            enable_cache: Enable result caching
        """
        self.classifier = RelevanceClassifier(enable_cache=enable_cache)
        self.min_score = min_score
        self.max_workers = max_workers
        
        self.stats: Dict[str, Any] = {
            "total_items": 0,
            "relevant_items": 0,
            "not_relevant_items": 0,
            "avg_score": 0.0,
            "llm_used": 0,
            "heuristic_fallback": 0,
            "errors": 0,
            "processing_time": 0.0,
            "cache_hits": 0,
        }
    
    def filter_items(
        self,
        items: List[Union[Patent, NewsArticle]],
        use_llm: bool = True
    ) -> tuple[List[RelevanceResult], Dict[str, Any]]:
        """
        Filter items by cybersecurity relevance.
        
        Args:
            items: List of Patent or NewsArticle objects
            use_llm: Whether to use LLM (false forces heuristics only)
            
        Returns:
            Tuple of (results, statistics)
        """
        start_time = time.time()
        results: List[RelevanceResult] = []
        
        initial_cache_size = self.classifier.get_cache_size()
        
        self.stats["total_items"] = len(items)
        
        # Process items with controlled concurrency
        if self.max_workers > 1 and len(items) > 1:
            results = self._process_concurrent(items, use_llm)
        else:
            results = self._process_sequential(items, use_llm)
        
        # Calculate statistics
        self.stats["processing_time"] = time.time() - start_time
        self._calculate_stats(results)
        self.stats["cache_hits"] = self.classifier.get_cache_size() - initial_cache_size
        
        return results, dict(self.stats)
    
    def _process_sequential(
        self,
        items: List[Union[Patent, NewsArticle]],
        use_llm: bool
    ) -> List[RelevanceResult]:
        """Process items sequentially."""
        results = []
        
        for item in items:
            try:
                result = self.classifier.classify(item, use_llm=use_llm)
                results.append(result)
                
                # Track model usage
                if result.model.startswith('gemini'):
                    self.stats["llm_used"] += 1
                elif result.model.startswith('heuristic'):
                    self.stats["heuristic_fallback"] += 1
                    
            except Exception as exc:
                self.stats["errors"] += 1
                print(f"Error classifying item: {exc}")
                continue
        
        return results
    
    def _process_concurrent(
        self,
        items: List[Union[Patent, NewsArticle]],
        use_llm: bool
    ) -> List[RelevanceResult]:
        """Process items concurrently with worker pool."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(self.classifier.classify, item, use_llm): item
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
                    print(f"Error in concurrent classification: {exc}")
                    continue
        
        return results
    
    def get_relevant_items(
        self,
        results: List[RelevanceResult]
    ) -> List[RelevanceResult]:
        """
        Filter results to only relevant items above threshold.
        
        Args:
            results: List of RelevanceResult objects
            
        Returns:
            Filtered list of relevant results
        """
        return [
            r for r in results
            if r.is_relevant and r.score >= self.min_score
        ]
    
    def _calculate_stats(self, results: List[RelevanceResult]):
        """Calculate aggregate statistics from results."""
        if not results:
            return
        
        relevant = [r for r in results if r.is_relevant and r.score >= self.min_score]
        not_relevant = [r for r in results if not r.is_relevant or r.score < self.min_score]
        
        self.stats["relevant_items"] = len(relevant)
        self.stats["not_relevant_items"] = len(not_relevant)
        
        # Average score
        total_score = sum(r.score for r in results)
        self.stats["avg_score"] = total_score / len(results) if results else 0.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return filtering statistics."""
        return dict(self.stats)
    
    def clear_cache(self):
        """Clear the classifier cache."""
        self.classifier.clear_cache()

