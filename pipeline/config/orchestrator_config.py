"""
Orchestrator Configuration
Controls pipeline execution, concurrency, and integration behavior
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, Literal


class OrchestratorConfig:
    """Configuration for pipeline orchestrator"""
    
    # Run mode
    RUN_MODE: Literal["incremental", "backfill", "dry_run"] = os.getenv(
        "RUN_MODE", "incremental"
    )
    
    # Incremental mode: lookback window
    LOOKBACK_DAYS: int = int(os.getenv("LOOKBACK_DAYS", 2))
    
    # Backfill mode: date range
    START_DATE: Optional[str] = os.getenv("START_DATE")  # YYYY-MM-DD
    END_DATE: Optional[str] = os.getenv("END_DATE")      # YYYY-MM-DD
    
    # Concurrency limits (respect Gemini RPM=15)
    P2_CONCURRENCY: int = int(os.getenv("P2_CONCURRENCY", 4))  # Relevance
    P3_CONCURRENCY: int = int(os.getenv("P3_CONCURRENCY", 4))  # Extraction
    
    # Rate limiting (reuse from existing configs where possible)
    GEMINI_MAX_RPM: int = int(os.getenv("GEMINI_MAX_RPM", 15))
    BIGQUERY_MAX_ROWS: int = int(os.getenv("BIGQUERY_MAX_ROWS", 1000))
    
    # Integration tests
    LIVE_INTEGRATION: bool = os.getenv("LIVE_INTEGRATION", "false").lower() == "true"
    
    # Dead letter queue
    DLQ_DIR: str = os.getenv("DLQ_DIR", "pipeline/.dlq")
    DLQ_ENABLED: bool = os.getenv("DLQ_ENABLED", "true").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    STRUCTURED_LOGGING: bool = os.getenv("STRUCTURED_LOGGING", "true").lower() == "true"
    
    # Performance targets
    TIME_BUDGET_MINUTES: int = int(os.getenv("TIME_BUDGET_MINUTES", 15))
    
    # Dashboard refresh
    REFRESH_VIEWS: bool = os.getenv("REFRESH_VIEWS", "false").lower() == "true"
    
    @classmethod
    def get_date_range(cls) -> Tuple[str, str]:
        """
        Get date range for current run based on mode
        
        Returns:
            (start_date, end_date) as YYYY-MM-DD strings
        """
        if cls.RUN_MODE == "backfill":
            if not cls.START_DATE or not cls.END_DATE:
                raise ValueError("Backfill mode requires START_DATE and END_DATE")
            return cls.START_DATE, cls.END_DATE
        
        elif cls.RUN_MODE == "incremental":
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=cls.LOOKBACK_DAYS)
            return start_date.isoformat(), end_date.isoformat()
        
        elif cls.RUN_MODE == "dry_run":
            # Use a very short window for dry run
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=1)
            return start_date.isoformat(), end_date.isoformat()
        
        else:
            raise ValueError(f"Unknown RUN_MODE: {cls.RUN_MODE}")
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration"""
        # Check mode
        if cls.RUN_MODE not in ["incremental", "backfill", "dry_run"]:
            raise ValueError(f"Invalid RUN_MODE: {cls.RUN_MODE}")
        
        # Check backfill dates
        if cls.RUN_MODE == "backfill":
            if not cls.START_DATE or not cls.END_DATE:
                raise ValueError("Backfill mode requires START_DATE and END_DATE")
            # Parse to validate format
            try:
                datetime.fromisoformat(cls.START_DATE)
                datetime.fromisoformat(cls.END_DATE)
            except ValueError as e:
                raise ValueError(f"Invalid date format: {e}")
        
        # Check concurrency
        if cls.P2_CONCURRENCY < 1 or cls.P3_CONCURRENCY < 1:
            raise ValueError("Concurrency must be >= 1")
        
        # Warn if concurrency too high for Gemini RPM
        total_concurrency = cls.P2_CONCURRENCY + cls.P3_CONCURRENCY
        if total_concurrency > cls.GEMINI_MAX_RPM:
            import warnings
            warnings.warn(
                f"Total concurrency ({total_concurrency}) exceeds Gemini RPM ({cls.GEMINI_MAX_RPM}). "
                "Rate limiting will throttle requests."
            )
    
    @classmethod
    def is_dry_run(cls) -> bool:
        """Check if running in dry-run mode"""
        return cls.RUN_MODE == "dry_run"
    
    @classmethod
    def get_dlq_path(cls, node_name: str) -> str:
        """Get DLQ directory path for a specific node"""
        import os
        path = os.path.join(cls.DLQ_DIR, node_name)
        os.makedirs(path, exist_ok=True)
        return path


# Validate on import
try:
    OrchestratorConfig.validate()
except ValueError as e:
    import warnings
    warnings.warn(f"Orchestrator configuration invalid: {e}")

