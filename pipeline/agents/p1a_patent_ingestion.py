from __future__ import annotations

import time
from typing import List, Dict, Any

from clients.bigquery_client import BigQueryClient
from agents.query_builder import PatentQueryBuilder
from models import Patent


class PatentIngestionError(Exception):
    """Custom exception for patent ingestion failures."""


class PatentIngestionAgent:
    """
    Agent P1a: Patent Ingestion from BigQuery

    Responsibilities:
      1. Query BigQuery for cybersecurity patents
      2. Parse raw results into Patent objects
      3. Validate data completeness
      4. Fallback to larger window if insufficient results
      5. Track statistics (patents fetched, bytes processed)
    """

    def __init__(
        self,
        bigquery_client: BigQueryClient,
        *,
        lookback_days: int = 7,
        min_patents: int = 50,
    ):
        self.bq_client = bigquery_client
        self.query_builder = PatentQueryBuilder(lookback_days)
        self.min_patents = min_patents
        self.stats: Dict[str, Any] = {
            "patents_fetched": 0,
            "bytes_processed": 0,
            "query_time": 0.0,
            "errors": [],
            "start_date": None,
            "end_date": None,
        }

    def fetch_patents(self) -> List[Patent]:
        """
        Fetch patents from BigQuery. Falls back to 30-day window if needed.
        """
        start_date, end_date = self.query_builder.get_date_range()
        self.stats["start_date"] = start_date
        self.stats["end_date"] = end_date

        patents = self._run_query_and_parse(start_date, end_date)
        if len(patents) < self.min_patents:
            # Fallback to 30-day window
            try:
                fallback_builder = PatentQueryBuilder(lookback_days=30)
                fb_start, fb_end = fallback_builder.get_date_range()
                self.stats["start_date"] = fb_start
                self.stats["end_date"] = fb_end
                patents = self._run_query_and_parse(fb_start, fb_end, builder=fallback_builder)
            except Exception as exc:  # surfaced as ingestion error
                self.stats["errors"].append(str(exc))
                raise PatentIngestionError(f"Fallback query failed: {exc}") from exc

        if not patents:
            raise PatentIngestionError("No patents retrieved from BigQuery")

        self.stats["patents_fetched"] = len(patents)
        self.stats["bytes_processed"] = self.bq_client.bytes_processed
        return patents

    def _run_query_and_parse(
        self,
        start_date: str,
        end_date: str,
        *,
        builder: PatentQueryBuilder | None = None,
    ) -> List[Patent]:
        builder = builder or self.query_builder
        query = builder.build_patent_query(start_date, end_date)

        # Execute and time the query
        t0 = time.time()
        rows = self.bq_client.execute_query(query, timeout_secs=30, max_retries=3, use_cache=True)
        self.stats["query_time"] = time.time() - t0

        # Parse and validate
        patents: List[Patent] = []
        for row in rows:
            patent = Patent.from_bigquery_row(row)
            if patent.is_valid_minimal():
                patents.append(patent)
        return patents

    def get_statistics(self) -> Dict[str, Any]:
        return dict(self.stats)
