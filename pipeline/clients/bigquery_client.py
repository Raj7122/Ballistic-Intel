from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from google.cloud import bigquery


class BigQueryClient:
    """
    Thin wrapper around google.cloud.bigquery.Client with:
    - Service account initialization via GOOGLE_APPLICATION_CREDENTIALS
    - Dry-run cost estimation
    - Query timeout control
    - Basic retry with exponential backoff
    - Bytes processed tracking
    """

    def __init__(self, credentials_path: Optional[str] = None, location: Optional[str] = None):
        credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path or not os.path.exists(credentials_path):
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS not set or file does not exist: "
                f"{credentials_path}"
            )

        self.client = bigquery.Client.from_service_account_json(credentials_path, location=location)
        self.bytes_processed: int = 0

    def estimate_query_cost(self, query: str) -> Dict[str, Any]:
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=True)
        query_job = self.client.query(query, job_config=job_config)
        return {
            "total_bytes_processed": int(query_job.total_bytes_processed or 0),
            "cache_hit": bool(query_job.cache_hit),
        }

    def execute_query(
        self,
        query: str,
        *,
        timeout_secs: int = 30,
        max_retries: int = 3,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        last_exc: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                job_config = bigquery.QueryJobConfig(use_query_cache=use_cache)
                start = time.time()
                query_job = self.client.query(query, job_config=job_config)
                rows = list(query_job.result(timeout=timeout_secs))
                elapsed = time.time() - start
                self.bytes_processed += int(query_job.total_bytes_processed or 0)

                # Convert Row objects to plain dicts
                result: List[Dict[str, Any]] = []
                for r in rows:
                    result.append({k: r.get(k) for k in r.keys()})

                return result
            except Exception as exc:
                last_exc = exc
                # Exponential backoff: 1, 2, 4 seconds
                time.sleep(2 ** attempt)
        # Exhausted retries
        if last_exc:
            raise last_exc
        return []


