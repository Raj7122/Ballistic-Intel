# Database Setup (Supabase)

This folder contains the SQL schema and seed data for the CyberPatent Intelligence Platform.

## Files
- `schema.sql` — All tables (9), indexes, materialized views (3), and helper functions
- `seed.sql` — Initial seed data for `intelligence_source` (4 MVP sources)

## How to Apply Schema in Supabase

### Step 1: Apply Schema
1. Open [Supabase Dashboard](https://supabase.com/dashboard)
2. Navigate to your project: **Ballistic Intel**
3. Click **SQL Editor** in the left sidebar
4. Click **New Query**
5. Copy and paste the entire contents of `schema.sql`
6. Click **Run** (or press Cmd+Enter)
7. Wait for "Success. No rows returned" message

### Step 2: Apply Seed Data
1. In SQL Editor, click **New Query**
2. Copy and paste the entire contents of `seed.sql`
3. Click **Run**
4. You should see 4 rows returned showing the intelligence sources

### Step 3: Validate Setup
Run these validation queries in SQL Editor:

```sql
-- Check tables (should return 9 tables)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check materialized views (should return 3 views)
SELECT matviewname 
FROM pg_matviews 
WHERE schemaname = 'public';

-- Check intelligence sources (should return 4 sources)
SELECT source_name, source_type, is_active 
FROM intelligence_source;

-- Refresh materialized views (will be empty initially)
REFRESH MATERIALIZED VIEW dashboard_company_intelligence;
REFRESH MATERIALIZED VIEW dashboard_active_vcs;
REFRESH MATERIALIZED VIEW dashboard_trending_sectors;
```

## Database Schema Overview

### Core Tables
1. **intelligence_source** - Registry of data sources (patents, newsletters, etc.)
2. **company** - Startup companies being tracked
3. **intelligence_signal** - Unified signals (patents, news, funding)
4. **patent_application** - USPTO patent details
5. **newsletter_mention** - Media mentions and funding announcements
6. **investor** - VC firms and investors
7. **company_investor** - Company-investor relationships
8. **inventor** - Patent inventors
9. **patent_inventor** - Patent-inventor junction table

### Materialized Views (Dashboard Optimization)
1. **dashboard_company_intelligence** - Company metrics with heat scores
2. **dashboard_active_vcs** - Active VC investor rankings
3. **dashboard_trending_sectors** - Trending cybersecurity sub-sectors

### Helper Functions
- `increment_newsletter_mentions(company_id)` - Increment mention counter
- `calculate_company_scores(company_id)` - Calculate innovation/momentum scores
- `refresh_all_dashboard_views()` - Refresh all materialized views
- `refresh_materialized_view(view_name)` - Refresh single view
- `daily_score_update()` - Batch recalculate all company scores

## Security Notes (MVP)

⚠️ **Row-Level Security (RLS) is DISABLED for MVP**
- All data is public (company info, patents, funding)
- No authentication required for demo
- Phase 2 TODO: Enable RLS and add policies

✅ **Security Features Enabled:**
- TLS 1.3 encryption in transit (Supabase default)
- AES-256 encryption at rest (Supabase default)
- Foreign key constraints with CASCADE delete
- CHECK constraints on enum fields

## Backup & Maintenance

### Manual Backup
```bash
# Export schema (via Supabase Dashboard)
# Settings → Database → Backups → Download
```

### Refresh Views (Run daily)
```sql
SELECT refresh_all_dashboard_views();
```

### Check Storage Usage
```sql
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Troubleshooting

### Error: "relation already exists"
Solution: Tables already created. Safe to ignore or drop and recreate:
```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
-- Then re-run schema.sql
```

### Error: "permission denied"
Solution: Ensure you're using the correct Supabase credentials. Check Project Settings → API.

### Materialized view returns 0 rows
Expected: Views will be empty until pipeline ingests data. This is normal.
