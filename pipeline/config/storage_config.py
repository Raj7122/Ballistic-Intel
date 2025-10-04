"""
Storage Configuration for Supabase PostgreSQL
Provides batch size, retries, timeouts, and connection settings
"""
import os
from typing import Optional


class StorageConfig:
    """Configuration for Supabase/PostgreSQL storage layer"""
    
    # Supabase credentials
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_SERVICE_KEY: str = os.getenv('SUPABASE_SERVICE_KEY', '')  # service_role key
    SUPABASE_SCHEMA: str = os.getenv('SUPABASE_SCHEMA', 'public')
    
    # Batch settings
    BATCH_SIZE: int = int(os.getenv('SUPABASE_BATCH_SIZE', 500))
    MAX_BATCH_SIZE: int = 1000  # Hard limit
    
    # Retry settings
    MAX_RETRIES: int = int(os.getenv('SUPABASE_MAX_RETRIES', 3))
    RETRY_BACKOFF: float = float(os.getenv('SUPABASE_RETRY_BACKOFF', 0.5))  # seconds
    RETRY_BACKOFF_MAX: float = 10.0  # max backoff in seconds
    
    # Timeout settings
    REQUEST_TIMEOUT: int = int(os.getenv('SUPABASE_REQUEST_TIMEOUT', 30))  # seconds
    
    # Connection settings
    POOL_SIZE: int = int(os.getenv('SUPABASE_POOL_SIZE', 10))
    MAX_OVERFLOW: int = int(os.getenv('SUPABASE_MAX_OVERFLOW', 5))
    
    # Validation
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration"""
        if not cls.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is required")
        if not cls.SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_SERVICE_KEY is required")
        if cls.BATCH_SIZE > cls.MAX_BATCH_SIZE:
            raise ValueError(f"BATCH_SIZE {cls.BATCH_SIZE} exceeds MAX_BATCH_SIZE {cls.MAX_BATCH_SIZE}")
    
    @classmethod
    def get_connection_string(cls) -> str:
        """Get PostgreSQL connection string from Supabase URL"""
        # Convert Supabase URL to Postgres connection string
        # Example: https://xxx.supabase.co -> postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres
        # Note: This is for direct psycopg2/SQLAlchemy if needed; we'll use Supabase client for REST API
        raise NotImplementedError("Direct PostgreSQL connection not implemented; use Supabase REST API")
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if storage is configured"""
        return bool(cls.SUPABASE_URL and cls.SUPABASE_SERVICE_KEY)


# Validate on import if configured
if StorageConfig.is_configured():
    try:
        StorageConfig.validate()
    except ValueError as e:
        import warnings
        warnings.warn(f"Storage configuration invalid: {e}")

