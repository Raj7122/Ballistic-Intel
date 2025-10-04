"""
Extraction Results Repository
Maps ExtractionResult domain models to database schema and handles upserts
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

from models.extraction import ExtractionResult
from clients.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class ExtractionRepository:
    """Repository for extraction_results table"""
    
    TABLE_NAME = 'extraction_results'
    # No single conflict key; using composite unique constraint in schema
    
    def __init__(self):
        self.client = get_supabase_client()
    
    @staticmethod
    def _to_db_dict(result: ExtractionResult) -> Dict[str, Any]:
        """
        Convert ExtractionResult model to database dict
        
        Args:
            result: ExtractionResult domain model
        
        Returns:
            Dict matching extraction_results table schema
        """
        return {
            'item_id': result.item_id,
            'source_type': result.source_type,
            'company_names': result.company_names or [],
            'sector': result.sector,
            'novelty_score': result.novelty_score,
            'tech_keywords': result.tech_keywords or [],
            'rationale': result.rationale or [],
            'model': result.model,
            'model_version': result.model_version,
            'timestamp': result.timestamp.isoformat() if isinstance(result.timestamp, datetime) else result.timestamp,
        }
    
    def upsert_extractions(self, results: List[ExtractionResult]) -> Dict[str, Any]:
        """
        Upsert extraction results in batches
        
        Args:
            results: List of ExtractionResult models
        
        Returns:
            Dict with 'count' (rows written) and 'success' (bool)
        
        Raises:
            RuntimeError: On persistent failures
        """
        if not results:
            logger.warning("upsert_extractions called with empty list")
            return {'count': 0, 'success': True}
        
        logger.info(f"Upserting {len(results)} extraction results")
        
        try:
            # Convert to DB format
            rows = [self._to_db_dict(r) for r in results]
            
            # Batch upsert (composite conflict key)
            result = self.client.upsert_batch(
                table=self.TABLE_NAME,
                rows=rows,
                on_conflict='item_id,source_type,model,model_version,timestamp',
                returning='minimal'
            )
            
            count = result.get('count', 0)
            logger.info(f"Successfully upserted {count} extraction results")
            
            return {
                'count': count,
                'success': True,
                'table': self.TABLE_NAME
            }
        
        except Exception as e:
            logger.error(f"Failed to upsert extraction results: {e}", exc_info=True)
            return {
                'count': 0,
                'success': False,
                'error': str(e),
                'table': self.TABLE_NAME
            }
    
    def get_by_sector(self, sector: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get extraction results by sector
        
        Args:
            sector: Sector name
            limit: Max number of results
        
        Returns:
            List of extraction result dicts
        """
        return self.client.select(
            table=self.TABLE_NAME,
            filters={'sector': sector},
            limit=limit
        )

