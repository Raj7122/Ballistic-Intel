"""
Relevance Results Repository
Maps RelevanceResult domain models to database schema and handles upserts
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

from models.relevance import RelevanceResult
from clients.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class RelevanceRepository:
    """Repository for relevance_results table"""
    
    TABLE_NAME = 'relevance_results'
    # No single conflict key; using composite unique constraint in schema
    
    def __init__(self):
        self.client = get_supabase_client()
    
    @staticmethod
    def _to_db_dict(result: RelevanceResult) -> Dict[str, Any]:
        """
        Convert RelevanceResult model to database dict
        
        Args:
            result: RelevanceResult domain model
        
        Returns:
            Dict matching relevance_results table schema
        """
        return {
            'item_id': result.item_id,
            'source_type': result.source_type,
            'is_relevant': result.is_relevant,
            'score': result.score,
            'category': result.category,
            'reasons': result.reasons or [],
            'model': result.model,
            'model_version': result.model_version,
            'timestamp': result.timestamp.isoformat() if isinstance(result.timestamp, datetime) else result.timestamp,
        }
    
    def upsert_relevance(self, results: List[RelevanceResult]) -> Dict[str, Any]:
        """
        Upsert relevance results in batches
        
        Args:
            results: List of RelevanceResult models
        
        Returns:
            Dict with 'count' (rows written) and 'success' (bool)
        
        Raises:
            RuntimeError: On persistent failures
        """
        if not results:
            logger.warning("upsert_relevance called with empty list")
            return {'count': 0, 'success': True}
        
        logger.info(f"Upserting {len(results)} relevance results")
        
        try:
            # Convert to DB format
            rows = [self._to_db_dict(r) for r in results]
            
            # Batch upsert (no single conflict key; relies on composite UNIQUE constraint)
            result = self.client.upsert_batch(
                table=self.TABLE_NAME,
                rows=rows,
                on_conflict='item_id,source_type,model,model_version,timestamp',  # composite
                returning='minimal'
            )
            
            count = result.get('count', 0)
            logger.info(f"Successfully upserted {count} relevance results")
            
            return {
                'count': count,
                'success': True,
                'table': self.TABLE_NAME
            }
        
        except Exception as e:
            logger.error(f"Failed to upsert relevance results: {e}", exc_info=True)
            return {
                'count': 0,
                'success': False,
                'error': str(e),
                'table': self.TABLE_NAME
            }
    
    def get_relevant_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get items marked as relevant
        
        Args:
            limit: Max number of results
        
        Returns:
            List of relevance result dicts
        """
        return self.client.select(
            table=self.TABLE_NAME,
            filters={'is_relevant': True},
            limit=limit
        )

