# Data Pipeline - BigQuery Setup

This directory contains the Python environment and utilities to connect to Google BigQuery and query the public Google Patents dataset.

## Prerequisites

- Service account JSON key placed at `../credentials/<your-key>.json`
- BigQuery API enabled on your GCP project
- Python 3.10+ installed

## Quick Start

```bash
cd "/Users/rajivsukhnandan/Ballistic Intel/pipeline"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip google-cloud-bigquery
python test_bigquery.py
```

The script will:
- Use your service account at `../credentials/planar-door-474015-u3-6040c3948b61.json`
- Run a bounded query (2024) against `patents-public-data.patents.publications`
- Filter for cybersecurity CPC families (H04L*, G06F21*)
- Print up to 10 recent results and report scanned MB

## Notes

- Do not commit credentials. The repository `.gitignore` excludes `credentials/` and `pipeline/.env`.
- If you rotate or rename the key file, update `test_bigquery.py` accordingly.
- To reduce costs, keep queries bounded by date and use `LIMIT` for sampling.


