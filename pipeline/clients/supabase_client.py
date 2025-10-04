"""
Supabase Client with Retry Logic and Batching
Singleton client for all database operations
"""
import os
import logging
from typing import Any, Dict, List, Literal, Optional
from supabase import create_client, Client
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from postgrest.exceptions import APIError

from config.storage_config import StorageConfig

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase client with retry logic and batch operations"""
    
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    
    def __new__(cls) -> 'SupabaseClient':
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Supabase client (only once)"""
        if self._client is None:
            StorageConfig.validate()
            self._client = create_client(
                StorageConfig.SUPABASE_URL,
                StorageConfig.SUPABASE_SERVICE_KEY  # service_role bypasses RLS
            )
            logger.info(f"Supabase client initialized for {StorageConfig.SUPABASE_URL}")
    
    @property
    def client(self) -> Client:
        """Get underlying Supabase client"""
        if self._client is None:
            raise RuntimeError("SupabaseClient not initialized")
        return self._client
    
    @retry(
        stop=stop_after_attempt(StorageConfig.MAX_RETRIES),
        wait=wait_exponential(
            multiplier=StorageConfig.RETRY_BACKOFF,
            max=StorageConfig.RETRY_BACKOFF_MAX
        ),
        retry=retry_if_exception_type((APIError, ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def upsert(
        self,
        table: str,
        rows: List[Dict[str, Any]],
        on_conflict: Optional[str] = None,
        returning: Literal['minimal', 'representation'] = 'minimal'
    ) -> Dict[str, Any]:
        """
        Upsert rows into a table with retry logic
        
        Args:
            table: Table name
            rows: List of row dicts to upsert
            on_conflict: Column(s) for conflict detection (e.g., 'publication_number')
            returning: 'minimal' (count only) or 'representation' (full rows)
        
        Returns:
            Response dict with 'data' and 'count'
        
        Raises:
            APIError: On persistent API failures
        """
        if not rows:
            logger.warning(f"upsert called on {table} with empty rows")
            return {'data': [], 'count': 0}
        
        logger.info(f"Upserting {len(rows)} rows to {table} (on_conflict={on_conflict})")
        
        try:
            response = self.client.table(table).upsert(
                rows,
                on_conflict=on_conflict,
                returning=returning
            ).execute()
            
            logger.info(f"Upserted {len(rows)} rows to {table} successfully")
            return {'data': response.data, 'count': len(response.data) if response.data else len(rows)}
        
        except APIError as e:
            logger.error(f"Supabase API error on {table}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error upserting to {table}: {e}")
            raise RuntimeError(f"Upsert failed: {e}") from e
    
    def upsert_batch(
        self,
        table: str,
        rows: List[Dict[str, Any]],
        on_conflict: Optional[str] = None,
        batch_size: Optional[int] = None,
        returning: Literal['minimal', 'representation'] = 'minimal'
    ) -> Dict[str, Any]:
        """
        Upsert rows in batches
        
        Args:
            table: Table name
            rows: List of row dicts
            on_conflict: Column(s) for conflict detection
            batch_size: Batch size (default: StorageConfig.BATCH_SIZE)
            returning: 'minimal' or 'representation'
        
        Returns:
            Aggregated response with total count
        """
        if not rows:
            return {'data': [], 'count': 0}
        
        batch_size = batch_size or StorageConfig.BATCH_SIZE
        total_count = 0
        all_data = []
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            result = self.upsert(table, batch, on_conflict, returning)
            total_count += result.get('count', 0)
            if returning == 'representation':
                all_data.extend(result.get('data', []))
        
        logger.info(f"Batch upsert complete: {total_count} rows to {table}")
        return {'data': all_data if returning == 'representation' else [], 'count': total_count}
    
    @retry(
        stop=stop_after_attempt(StorageConfig.MAX_RETRIES),
        wait=wait_exponential(
            multiplier=StorageConfig.RETRY_BACKOFF,
            max=StorageConfig.RETRY_BACKOFF_MAX
        ),
        retry=retry_if_exception_type((APIError, ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def select(
        self,
        table: str,
        columns: str = '*',
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Select rows from a table
        
        Args:
            table: Table name
            columns: Comma-separated column names (default: '*')
            filters: Dict of column=value filters (equality only)
            limit: Max rows to return
        
        Returns:
            List of row dicts
        """
        query = self.client.table(table).select(columns)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        return response.data or []
    
    def health_check(self) -> bool:
        """
        Check if Supabase connection is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple query to test connection
            self.client.table('patents').select('publication_number').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Singleton instance
_client_instance: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get or create the singleton Supabase client"""
    global _client_instance
    if _client_instance is None:
        _client_instance = SupabaseClient()
    return _client_instance

