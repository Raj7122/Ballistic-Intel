"""
Patents Repository
Maps Patent domain models to database schema and handles upserts
"""
import logging
from typing import List, Dict, Any
from datetime import date

from models.patent import Patent
from clients.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class PatentsRepository:
    """Repository for patents table"""
    
    TABLE_NAME = 'patents'
    CONFLICT_KEY = 'publication_number'
    
    def __init__(self):
        self.client = get_supabase_client()
    
    @staticmethod
    def _to_db_dict(patent: Patent) -> Dict[str, Any]:
        """
        Convert Patent model to database dict
        
        Args:
            patent: Patent domain model
        
        Returns:
            Dict matching patents table schema
        """
        return {
            'publication_number': patent.publication_number,
            'title': patent.title,
            'abstract': patent.abstract,
            'filing_date': patent.filing_date.isoformat() if isinstance(patent.filing_date, date) else patent.filing_date,
            'publication_date': patent.publication_date.isoformat() if isinstance(patent.publication_date, date) else patent.publication_date,
            'assignees': patent.assignees or [],
            'inventors': patent.inventors or [],
            'cpc_codes': patent.cpc_codes or [],
            'country': patent.country,
            'kind_code': patent.kind_code,
        }
    
    def upsert_patents(self, patents: List[Patent]) -> Dict[str, Any]:
        """
        Upsert patents in batches
        
        Args:
            patents: List of Patent models
        
        Returns:
            Dict with 'count' (rows written) and 'success' (bool)
        
        Raises:
            RuntimeError: On persistent failures
        """
        if not patents:
            logger.warning("upsert_patents called with empty list")
            return {'count': 0, 'success': True}
        
        logger.info(f"Upserting {len(patents)} patents")
        
        try:
            # Convert to DB format
            rows = [self._to_db_dict(p) for p in patents]
            
            # Batch upsert
            result = self.client.upsert_batch(
                table=self.TABLE_NAME,
                rows=rows,
                on_conflict=self.CONFLICT_KEY,
                returning='minimal'
            )
            
            count = result.get('count', 0)
            logger.info(f"Successfully upserted {count} patents")
            
            return {
                'count': count,
                'success': True,
                'table': self.TABLE_NAME
            }
        
        except Exception as e:
            logger.error(f"Failed to upsert patents: {e}", exc_info=True)
            return {
                'count': 0,
                'success': False,
                'error': str(e),
                'table': self.TABLE_NAME
            }
    
    def get_by_publication_number(self, publication_number: str) -> Dict[str, Any]:
        """
        Get a single patent by publication number
        
        Args:
            publication_number: Patent publication number
        
        Returns:
            Patent dict or empty dict if not found
        """
        results = self.client.select(
            table=self.TABLE_NAME,
            filters={'publication_number': publication_number},
            limit=1
        )
        return results[0] if results else {}
    
    def get_recent_patents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recently filed patents
        
        Args:
            limit: Max number of patents
        
        Returns:
            List of patent dicts
        """
        # Note: Supabase postgrest doesn't support ORDER BY directly in select
        # For now, we'll return unsorted; add ordering in future if needed
        return self.client.select(
            table=self.TABLE_NAME,
            limit=limit
        )

