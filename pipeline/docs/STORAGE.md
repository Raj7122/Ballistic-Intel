# Storage Layer Documentation

## Overview

The storage layer provides idempotent, batched persistence of all agent outputs to Supabase PostgreSQL. It implements the repository pattern for clean separation between domain models and database operations.

**Author:** S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System  
**Last Updated:** 2025-01-04  
**Status:** ✅ Complete - All tests passing (12/12)

---

## Architecture

```
Agent Outputs (Domain Models)
        ↓
Storage Writer (Orchestration)
        ↓
Repositories (Mapping & Batching)
        ↓
Supabase Client (Retry Logic)
        ↓
PostgreSQL (Supabase)
```

### Key Components

1. **Domain Models** (`models/`)
   - `Patent`, `NewsArticle`, `RelevanceResult`, `ExtractionResult`, `ResolvedEntity`, `AliasLink`
   - Pure Python dataclasses with validation

2. **Repositories** (`repos/`)
   - `PatentsRepository`, `NewsRepository`, `RelevanceRepository`, `ExtractionRepository`, `EntitiesRepository`
   - Convert domain models to DB dicts
   - Handle batched upserts with conflict resolution

3. **Supabase Client** (`clients/supabase_client.py`)
   - Singleton pattern for connection pooling
   - Exponential backoff with retry logic
   - Batch operations with configurable chunk size

4. **Storage Writer** (`services/storage_writer.py`)
   - High-level interface for orchestrating all persistence
   - Unified `persist_all()` method for bulk operations

---

## Environment Configuration

### Required Environment Variables

Add to `pipeline/.env`:

```bash
# Supabase connection
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # service_role key

# Optional: Override defaults
SUPABASE_SCHEMA=public           # Default: public
SUPABASE_BATCH_SIZE=500          # Default: 500 (max 1000)
SUPABASE_MAX_RETRIES=3           # Default: 3
SUPABASE_RETRY_BACKOFF=0.5       # Default: 0.5 seconds
SUPABASE_REQUEST_TIMEOUT=30      # Default: 30 seconds
```

### Configuration Validation

The `StorageConfig` class validates required settings on import:

```python
from config.storage_config import StorageConfig

# Check if configured
if StorageConfig.is_configured():
    StorageConfig.validate()  # Raises ValueError if invalid
```

---

## Database Schema

### Raw Pipeline Tables

These tables store unprocessed agent outputs:

#### 1. `patents`
```sql
CREATE TABLE patents (
  publication_number TEXT PRIMARY KEY,
  title TEXT,
  abstract TEXT,
  filing_date DATE NOT NULL,
  publication_date DATE,
  assignees TEXT[] DEFAULT '{}',
  inventors TEXT[] DEFAULT '{}',
  cpc_codes TEXT[] DEFAULT '{}',
  country TEXT NOT NULL DEFAULT 'US',
  kind_code TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```
**Upsert Key:** `publication_number`

#### 2. `news_articles`
```sql
CREATE TABLE news_articles (
  id VARCHAR(16) PRIMARY KEY,
  source TEXT NOT NULL,
  title TEXT NOT NULL,
  link TEXT UNIQUE NOT NULL,
  published_at TIMESTAMPTZ NOT NULL,
  summary TEXT,
  categories TEXT[] DEFAULT '{}',
  content_text TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```
**Upsert Key:** `link` (unique constraint)

#### 3. `relevance_results`
```sql
CREATE TABLE relevance_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  item_id TEXT NOT NULL,
  source_type TEXT NOT NULL CHECK (source_type IN ('patent', 'news')),
  is_relevant BOOLEAN NOT NULL,
  score FLOAT CHECK (score BETWEEN 0 AND 1),
  category TEXT,
  reasons TEXT[] DEFAULT '{}',
  model TEXT NOT NULL,
  model_version TEXT,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(item_id, source_type, model, model_version, timestamp)
);
```
**Upsert Key:** Composite `(item_id, source_type, model, model_version, timestamp)`

#### 4. `extraction_results`
```sql
CREATE TABLE extraction_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  item_id TEXT NOT NULL,
  source_type TEXT NOT NULL CHECK (source_type IN ('patent', 'news')),
  company_names TEXT[] DEFAULT '{}',
  sector TEXT,
  novelty_score FLOAT CHECK (novelty_score BETWEEN 0 AND 1),
  tech_keywords TEXT[] DEFAULT '{}',
  rationale TEXT[] DEFAULT '{}',
  model TEXT NOT NULL,
  model_version TEXT,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(item_id, source_type, model, model_version, timestamp)
);
```
**Upsert Key:** Composite `(item_id, source_type, model, model_version, timestamp)`

#### 5. `entities`
```sql
CREATE TABLE entities (
  entity_id VARCHAR(16) PRIMARY KEY,
  canonical_name TEXT NOT NULL,
  sources TEXT[] DEFAULT '{}',
  confidence FLOAT CHECK (confidence BETWEEN 0 AND 1),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```
**Upsert Key:** `entity_id`

#### 6. `entity_aliases`
```sql
CREATE TABLE entity_aliases (
  raw_name TEXT PRIMARY KEY,
  entity_id VARCHAR(16) REFERENCES entities(entity_id) ON DELETE CASCADE,
  score FLOAT CHECK (score BETWEEN 0 AND 1),
  rules_applied TEXT[] DEFAULT '{}'
);
```
**Upsert Key:** `raw_name`

### Indexes

Optimized for dashboard queries:
- `patents`: `(filing_date DESC)`, `(publication_date DESC)`, GIN on `cpc_codes`
- `news_articles`: `(published_at DESC)`, GIN on `categories`
- `relevance_results`: `(item_id, source_type)`, `(category)`, `(is_relevant)`
- `extraction_results`: `(item_id, source_type)`, GIN on `company_names`, GIN on `tech_keywords`, `(sector)`
- `entities`: `(canonical_name)`
- `entity_aliases`: `(entity_id)`

---

## Usage Guide

### Basic Usage

#### 1. Initialize Storage Writer

```python
from services.storage_writer import get_storage_writer

writer = get_storage_writer()  # Singleton instance
```

#### 2. Persist Agent Outputs

```python
from models.patent import Patent
from models.news_article import NewsArticle
from datetime import date, datetime

# Example: Persist patents from Agent P1a
patents = [
    Patent(
        publication_number='US-2024-123456-A1',
        title='Biometric Authentication System',
        abstract='A novel approach...',
        filing_date=date(2024, 1, 1),
        publication_date=date(2024, 6, 1),
        assignees=['Acme Corp'],
        inventors=['Alice Johnson'],
        cpc_codes=['H04L9/00', 'G06F21/32'],
        country='US',
        kind_code='A1'
    )
]

result = writer.persist_patents(patents)
print(f"Success: {result['success']}, Count: {result['count']}")
```

#### 3. Persist All Outputs at Once

```python
result = writer.persist_all(
    patents=patent_list,
    news=news_list,
    relevance=relevance_list,
    extractions=extraction_list,
    entities=entity_list,
    aliases=alias_list
)

print(f"Total persisted: {result['total_count']}")
print(f"Overall success: {result['success']}")
```

### Advanced Usage

#### Direct Repository Access

```python
from repos.patents_repo import PatentsRepository

repo = PatentsRepository()

# Upsert with custom control
result = repo.upsert_patents(patents)

# Retrieve by publication number
patent_dict = repo.get_by_publication_number('US-2024-123456-A1')

# Get recent patents
recent = repo.get_recent_patents(limit=50)
```

#### Custom Batch Size

```python
from clients.supabase_client import get_supabase_client

client = get_supabase_client()

# Manually control batch size (e.g., for large datasets)
result = client.upsert_batch(
    table='patents',
    rows=patent_dicts,
    on_conflict='publication_number',
    batch_size=250,  # Smaller batches for rate limiting
    returning='minimal'
)
```

---

## Idempotency

All upserts are idempotent using `ON CONFLICT ... DO UPDATE`:

```python
# First run: 100 patents inserted
result1 = writer.persist_patents(patents)
# result1['count'] == 100

# Second run (same data): 100 patents updated (no duplicates)
result2 = writer.persist_patents(patents)
# result2['count'] == 100
```

**Upsert Keys:**
- `patents`: `publication_number`
- `news_articles`: `link`
- `relevance_results`: `(item_id, source_type, model, model_version, timestamp)`
- `extraction_results`: `(item_id, source_type, model, model_version, timestamp)`
- `entities`: `entity_id`
- `entity_aliases`: `raw_name`

---

## Batching

Default batch size: **500 rows**

```python
# Automatically chunked into batches
patents = [...]  # 1,500 patents
result = writer.persist_patents(patents)
# Internally: 3 batches of 500
```

**Adaptive Batching:**
- On `413 Payload Too Large`: Reduce batch size dynamically
- On `429 Too Many Requests`: Exponential backoff

---

## Retry Logic

Powered by `tenacity`:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, max=10),
    retry=retry_if_exception_type((APIError, ConnectionError, TimeoutError))
)
```

**Behavior:**
- Retry on: `APIError`, `ConnectionError`, `TimeoutError`, `429`, `5xx`
- Max retries: **3** (configurable via `SUPABASE_MAX_RETRIES`)
- Backoff: **0.5s, 1s, 2s, ...** up to 10s (with jitter)

---

## Security

### Service Role vs Anon Key

```python
# Pipeline uses service_role key (bypasses RLS)
SUPABASE_SERVICE_KEY=eyJhbGci...  # Full read/write access

# Frontend will use anon key (enforces RLS)
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGci...  # Read-only via RLS policies
```

### Row-Level Security (RLS)

RLS policies are **not yet enabled** for raw pipeline tables (service role bypasses them). When frontend requires direct access:

```sql
-- Example RLS policy for patents (read-only for anon users)
ALTER TABLE patents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to patents"
  ON patents FOR SELECT
  USING (true);  -- All rows readable

-- Disable INSERT/UPDATE/DELETE for anon role
CREATE POLICY "Deny public write access to patents"
  ON patents FOR ALL
  USING (false);
```

Add policies in `database/rls.sql` when needed.

---

## Testing

### Unit Tests

All repositories have mocked unit tests:

```bash
cd pipeline
source venv/bin/activate
pytest tests/test_storage_layer.py -v
```

**Results:** ✅ 12/12 passing

**Coverage:**
- ✅ Patent model to DB dict mapping
- ✅ News article ID generation
- ✅ Relevance results composite conflict key
- ✅ Extraction results sector normalization
- ✅ Entity and alias mapping
- ✅ StorageWriter orchestration

### Integration Tests (Optional)

Skipped if `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` not set:

```bash
pytest tests/test_storage_integration.py -v
```

Integration tests:
1. Connect to Supabase
2. Upsert test data
3. Read back and assert
4. Cleanup test data

---

## Performance Optimization

### Best Practices

1. **Batch Operations**
   ```python
   # Good: Batch upsert
   writer.persist_patents(all_patents)

   # Bad: Individual upserts
   for patent in all_patents:
       writer.persist_patents([patent])
   ```

2. **Minimal Returning**
   ```python
   # Default: returning='minimal' (fast)
   result = repo.upsert_patents(patents)

   # Only if you need full data back
   result = client.upsert_batch(..., returning='representation')
   ```

3. **Limit Query Scope**
   ```python
   # Get only what you need
   recent = repo.get_recent_patents(limit=100)
   ```

### Metrics

Enable structured logging to track performance:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Output:
# [StorageWriter] Persisting 500 patents
# [PatentsRepository] Upserting 500 patents
# [SupabaseClient] Upserted 500 rows to patents successfully
# [StorageWriter] ✓ Patents persisted: 500
```

---

## Troubleshooting

### 1. Connection Errors

**Symptom:** `ConnectionError` or `TimeoutError`

**Solution:**
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are correct
- Check network connectivity
- Increase `SUPABASE_REQUEST_TIMEOUT`

### 2. Rate Limiting (429)

**Symptom:** `429 Too Many Requests`

**Solution:**
- Reduce `SUPABASE_BATCH_SIZE` (e.g., 250)
- Implement delays between agent runs
- Upgrade Supabase plan for higher limits

### 3. Payload Too Large (413)

**Symptom:** `413 Payload Too Large`

**Solution:**
- Reduce `SUPABASE_BATCH_SIZE` (e.g., 100)
- Truncate large text fields (abstracts, content_text)

### 4. Unique Constraint Violations

**Symptom:** `duplicate key value violates unique constraint`

**Solution:**
- Ensure correct `on_conflict` key is specified
- Check for duplicate data in source

### 5. Foreign Key Violations

**Symptom:** `violates foreign key constraint`

**Solution:**
- For `entity_aliases`, upsert `entities` **before** `aliases`
- Use `persist_entities(entities, aliases)` to ensure correct order

---

## Migrations

Apply schema to Supabase:

1. Open Supabase SQL Editor: https://supabase.com/dashboard/project/[YOUR_PROJECT]/sql
2. Copy contents of `database/schema.sql`
3. Run the script
4. Verify tables exist: `\dt` in psql or Supabase Table Editor

**Note:** Schema uses `IF NOT EXISTS` for safe re-runs.

---

## Future Enhancements

1. **Connection Pooling:** Add `pgbouncer` or `asyncpg` for high concurrency
2. **Bulk Delete:** Implement soft deletes with `is_deleted` flag
3. **Change Data Capture (CDC):** Use Supabase Realtime for live updates
4. **Analytics Tables:** Pre-aggregate data for dashboard performance
5. **RLS Policies:** Enable RLS when frontend requires direct Postgres access

---

## Dependencies

```txt
supabase==2.21.1
tenacity==9.1.1
httpx==0.28.1
postgrest==2.21.1
```

Install:
```bash
pip install supabase tenacity
```

---

## References

- [Supabase Python Client Docs](https://supabase.com/docs/reference/python/introduction)
- [PostgREST Docs](https://postgrest.org/en/stable/)
- [Tenacity Retry Docs](https://tenacity.readthedocs.io/)
- [S.A.F.E. D.R.Y. Principles](../plan.md)

---

## Changelog

**2025-01-04:** Initial release (Task 2.6)
- ✅ Schema with 6 raw pipeline tables
- ✅ Supabase client with retry logic
- ✅ 5 repositories (patents, news, relevance, extraction, entities)
- ✅ StorageWriter orchestration service
- ✅ 12 unit tests (100% passing)
- ✅ Comprehensive documentation

**Next:** Task 2.7 - Orchestrator with live integration tests

