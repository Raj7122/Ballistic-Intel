# Orchestrator Documentation

## Overview

The Pipeline Orchestrator coordinates all agents (P1a → P1b → P2 → P3 → P4), applies bounded concurrency, handles retries and DLQ, and persists results via the Storage Layer.

- Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
- Last Updated: 2025-10-04
- Status: Complete (Phase 1). Unit tests: 16/16 passing.

## Architecture

```
BigQuery (P1a)      RSS (P1b)
       \              /
        \            /
         \          /
           P2 (Relevance)
                  |
           P3 (Extraction)
                  |
           P4 (Resolution)
                  |
            Storage Writer → Supabase
```

### Components
- `config/orchestrator_config.py`: Run modes, lookback, concurrency, DLQ, logging
- `orchestrator/context.py`: RunContext (correlation_id, stats, errors, duration)
- `orchestrator/dag.py`: DAG nodes, validation, topological execution
- `orchestrator/errors.py`: Exceptions; DLQ utilities (write/list/read)
- `orchestrator/runner.py`: Coordinates agents, threads, and persistence
- `__main__.py`: CLI entrypoint

## Run Modes
- `incremental` (default): processes a lookback window (default 2 days)
- `backfill`: processes a fixed date range (`START_DATE`, `END_DATE`)
- `dry_run`: no external side effects; executes logic paths and prints stats

Environment variables:
```
RUN_MODE=incremental|backfill|dry_run
LOOKBACK_DAYS=2
START_DATE=YYYY-MM-DD
END_DATE=YYYY-MM-DD
P2_CONCURRENCY=4
P3_CONCURRENCY=4
LIVE_INTEGRATION=false
DLQ_DIR=pipeline/.dlq
LOG_LEVEL=INFO
```

## CLI Usage
```
# Incremental (last 2 days)
python -m pipeline --mode incremental --lookback 2

# Backfill specific dates
python -m pipeline --mode backfill --start 2024-12-01 --end 2024-12-07

# Dry run (no side effects)
python -m pipeline --mode dry_run

# Enable live integration testing
LIVE_INTEGRATION=true python -m pipeline --mode incremental
```

## DAG & Execution
- Nodes:
  - `p1a_patents`: ingest from BigQuery and persist to `patents`
  - `p1b_news`: ingest from RSS and persist to `news_articles`
  - `p2_relevance`: classify patents+news; persist to `relevance_results`
  - `p3_extraction`: extract entities/sectors; persist to `extraction_results`
  - `p4_resolution`: entity resolution; persist to `entities`, `entity_aliases`
- Dependencies: P2 depends on P1a/P1b; P3 on P2; P4 on P3
- Topological order computed via Kahn’s algorithm

## Concurrency & Rate Limits
- P2 and P3 run with ThreadPoolExecutor (defaults: 4 workers each)
- Respects Gemini RPM=15; additional throttling already in `GeminiClient`

## Error Handling & DLQ
- Retries: handled in clients and services via tenacity
- DLQ: failed items can be written to `pipeline/.dlq/<node>/YYYYMMDD_HHMMSS_<id>.json`
- Continue-on-error: dependents of failed nodes are skipped

### DLQ Utilities
```python
from orchestrator.errors import write_to_dlq, list_dlq_files, read_dlq_file

# Write
write_to_dlq('pipeline/.dlq', 'p2_relevance', {'item':'data'}, 'timeout', 'item-123')

# List
files = list_dlq_files('pipeline/.dlq', 'p2_relevance')

# Read
entry = read_dlq_file(files[0])
```

## Persistence
- Uses `StorageWriter` for idempotent upserts
- Batch size: default 500 (adaptive on 413/429)

## Metrics & Logging
- Correlation ID per run; stats tracked in `RunContext.stats`
- Example counters: `p1a_patents_fetched`, `p2_items_classified`, `p3_results_persisted`, `p4_entities_resolved`

## Integration Testing
- Set `LIVE_INTEGRATION=true` with valid credentials:
  - `GEMINI_API_KEY`
  - `GOOGLE_APPLICATION_CREDENTIALS`
  - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
- Validate that Supabase tables increase appropriately and re-run idempotently

## Examples
```bash
# Dry run summary
python -m pipeline --mode dry_run

# Incremental two-day window
RUN_MODE=incremental LOOKBACK_DAYS=2 python -m pipeline

# Backfill
RUN_MODE=backfill START_DATE=2024-12-01 END_DATE=2024-12-07 python -m pipeline
```

## Troubleshooting
- BigQuery high bytes processed → shorten date range; select minimal columns
- Gemini 404 model → ensure `gemini-2.5-flash` in `GeminiClient`
- Supabase 429 → reduce batch size via `SUPABASE_BATCH_SIZE`
- Skips due to failed deps → inspect `RunContext.errors` and DLQ files

## Changelog
- 2025-10-04: Initial release (Phase 1). 16 unit tests passing, CLI added, DAG engine implemented.
