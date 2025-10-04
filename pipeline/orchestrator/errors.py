"""
Orchestrator Error Classes and DLQ Utilities
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class OrchestratorError(Exception):
    """Base exception for orchestrator errors"""
    pass


class PreflightCheckError(OrchestratorError):
    """Pre-flight connectivity check failed"""
    pass


class AgentExecutionError(OrchestratorError):
    """Agent execution failed"""
    def __init__(self, node: str, message: str, item_id: Optional[str] = None):
        self.node = node
        self.item_id = item_id
        super().__init__(f"[{node}] {message}" + (f" (item: {item_id})" if item_id else ""))


class PersistenceError(OrchestratorError):
    """Storage layer persistence failed"""
    pass


class TimeoutError(OrchestratorError):
    """Orchestrator run exceeded time budget"""
    pass


def write_to_dlq(
    dlq_dir: str,
    node_name: str,
    payload: Dict[str, Any],
    error_message: str,
    item_id: Optional[str] = None
) -> str:
    """
    Write failed item to dead letter queue
    
    Args:
        dlq_dir: Base DLQ directory
        node_name: Node that failed (e.g., 'p2_relevance')
        payload: Item data to save
        error_message: Error description
        item_id: Optional item identifier
        
    Returns:
        Path to DLQ file
    """
    # Create DLQ directory for this node
    node_dlq = Path(dlq_dir) / node_name
    node_dlq.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    item_suffix = f"_{item_id}" if item_id else ""
    filename = f"{timestamp}{item_suffix}.json"
    filepath = node_dlq / filename
    
    # Prepare DLQ entry
    dlq_entry = {
        'node': node_name,
        'item_id': item_id,
        'error': error_message,
        'timestamp': datetime.utcnow().isoformat(),
        'payload': payload
    }
    
    # Write to file
    try:
        with open(filepath, 'w') as f:
            json.dump(dlq_entry, f, indent=2, default=str)
        logger.warning(f"DLQ: Wrote failed item to {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"Failed to write DLQ file {filepath}: {e}")
        raise


def list_dlq_files(dlq_dir: str, node_name: Optional[str] = None) -> list:
    """
    List DLQ files
    
    Args:
        dlq_dir: Base DLQ directory
        node_name: Optional node filter
        
    Returns:
        List of DLQ file paths
    """
    base_path = Path(dlq_dir)
    
    if node_name:
        search_path = base_path / node_name
        if not search_path.exists():
            return []
        return sorted([str(f) for f in search_path.glob("*.json")])
    else:
        # All nodes
        files = []
        if base_path.exists():
            for node_dir in base_path.iterdir():
                if node_dir.is_dir():
                    files.extend([str(f) for f in node_dir.glob("*.json")])
        return sorted(files)


def read_dlq_file(filepath: str) -> Dict[str, Any]:
    """
    Read a DLQ file
    
    Args:
        filepath: Path to DLQ JSON file
        
    Returns:
        DLQ entry dict
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def delete_dlq_file(filepath: str) -> None:
    """
    Delete a DLQ file after successful reprocessing
    
    Args:
        filepath: Path to DLQ JSON file
    """
    try:
        os.remove(filepath)
        logger.info(f"Deleted DLQ file: {filepath}")
    except Exception as e:
        logger.warning(f"Failed to delete DLQ file {filepath}: {e}")

