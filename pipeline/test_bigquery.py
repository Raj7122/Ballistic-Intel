"""
Test BigQuery connection and query USPTO patent data for cybersecurity filings.

This script intentionally limits the scanned data to control cost and validate
connectivity using the public Google Patents dataset hosted in BigQuery.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from google.cloud import bigquery


def set_credentials_env() -> Path:
    """
    Resolve and export GOOGLE_APPLICATION_CREDENTIALS to the service account key.

    Returns the resolved path for logging/verification.
    """
    script_dir = Path(__file__).resolve().parent
    credentials_dir = (script_dir / ".." / "credentials").resolve()

    # NOTE: Update this filename if you rotate/rename your key
    credential_filename = "planar-door-474015-u3-6040c3948b61.json"
    credential_path = (credentials_dir / credential_filename).resolve()

    if not credential_path.exists():
        raise FileNotFoundError(
            f"Credential file not found at: {credential_path}\n"
            "Place your JSON key in ../credentials and update this filename if needed."
        )

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credential_path)
    return credential_path


def format_megabytes(num_bytes: Optional[int]) -> str:
    if num_bytes is None:
        return "unknown"
    return f"{num_bytes / 1024 / 1024:.2f} MB"


def test_bigquery_connection() -> bool:
    try:
        credential_path = set_credentials_env()
        print(f"🔐 Using credentials at: {credential_path}")

        client = bigquery.Client()
        print(f"✅ BigQuery client initialized (project: {client.project})")

        # Query: 2024 US filings with CPC codes in cybersecurity domains
        # filing_date is INT64 (YYYYMMDD). Use a bounded window to control cost.
        query = """
        SELECT
          publication_number,
          title_localized[SAFE_OFFSET(0)].text AS title,
          filing_date,
          assignee_harmonized[SAFE_OFFSET(0)].name AS company_name,
          cpc[SAFE_OFFSET(0)].code AS first_cpc_code
        FROM `patents-public-data.patents.publications`
        WHERE
          filing_date >= 20240101
          AND filing_date <= 20241231
          AND country_code = 'US'
          AND EXISTS (
            SELECT 1 FROM UNNEST(cpc) AS c
            WHERE c.code LIKE 'H04L%' OR c.code LIKE 'G06F21%'
          )
        ORDER BY filing_date DESC
        LIMIT 10
        """

        print("🔎 Running test query (cybersecurity CPC; 2024 US filings)...")
        job = client.query(query)
        rows = list(job.result())

        processed_attr = getattr(job, "total_bytes_processed", None)
        print(f"✅ Query succeeded. Processed {format_megabytes(processed_attr)}")

        if not rows:
            print("⚠️ No rows returned. Try widening the date window.")
            return True

        print("\nSample results:")
        for i, r in enumerate(rows, 1):
            title = (r.title or "")[:90]
            print(f"{i}. {r.publication_number} | {r.filing_date} | {r.company_name} | {title}")
        return True

    except Exception as e:  # noqa: BLE001 - surface any error clearly for setup
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    ok = test_bigquery_connection()
    raise SystemExit(0 if ok else 1)


