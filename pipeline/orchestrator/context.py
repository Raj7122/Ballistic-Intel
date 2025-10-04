"""
Run Context for Orchestrator
Tracks execution state, metadata, and statistics
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class RunContext:
    """
    Context for a single orchestrator run
    
    Attributes:
        correlation_id: Unique ID for this run
        run_mode: incremental|backfill|dry_run
        start_date: Start of date range (YYYY-MM-DD)
        end_date: End of date range (YYYY-MM-DD)
        started_at: Run start timestamp
        is_dry_run: If true, skip external side effects
        stats: Statistics counters
        errors: Error log
    """
    
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_mode: str = "incremental"
    start_date: str = ""
    end_date: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    is_dry_run: bool = False
    
    # Statistics
    stats: Dict[str, int] = field(default_factory=dict)
    
    # Errors
    errors: List[Dict[str, str]] = field(default_factory=list)
    
    def increment(self, key: str, count: int = 1) -> None:
        """Increment a statistics counter"""
        self.stats[key] = self.stats.get(key, 0) + count
    
    def get_stat(self, key: str) -> int:
        """Get a statistics counter value"""
        return self.stats.get(key, 0)
    
    def add_error(self, node: str, message: str, item_id: Optional[str] = None) -> None:
        """Log an error"""
        self.errors.append({
            'node': node,
            'message': message,
            'item_id': item_id or 'N/A',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def get_duration_seconds(self) -> float:
        """Get run duration in seconds"""
        return (datetime.utcnow() - self.started_at).total_seconds()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging"""
        return {
            'correlation_id': self.correlation_id,
            'run_mode': self.run_mode,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'started_at': self.started_at.isoformat(),
            'duration_seconds': self.get_duration_seconds(),
            'is_dry_run': self.is_dry_run,
            'stats': self.stats,
            'errors': self.errors
        }
    
    def summary(self) -> str:
        """Get human-readable summary"""
        duration = self.get_duration_seconds()
        return (
            f"Run {self.correlation_id[:8]}: {self.run_mode} mode, "
            f"{self.start_date} to {self.end_date}, "
            f"{duration:.1f}s, {len(self.errors)} errors"
        )

