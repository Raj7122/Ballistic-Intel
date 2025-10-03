-- CyberPatent Intelligence Platform - Database Schema (MVP)
-- Compatible with Supabase (PostgreSQL)

-- ============================================
-- EXTENSIONS
-- ============================================
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid()

-- ============================================
-- SECTION 1: TABLES (9 tables)
-- ============================================

-- 1.1 Intelligence Sources (Registry)
CREATE TABLE IF NOT EXISTS intelligence_source (
  source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name TEXT UNIQUE NOT NULL,
  source_type TEXT CHECK (source_type IN ('PATENT', 'NEWSLETTER', 'FUNDING', 'CONFERENCE', 'THREAT_INTEL')),
  source_url TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  last_sync_date TIMESTAMP,
  sync_frequency TEXT,
  total_records_ingested INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 1.2 Company (Enhanced with VC tracking)
CREATE TABLE IF NOT EXISTS company (
  company_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_name TEXT NOT NULL,
  company_name_normalized TEXT NOT NULL UNIQUE,

  -- Basic Info
  company_website TEXT,
  company_country TEXT DEFAULT 'US',
  company_state TEXT,
  company_city TEXT,
  founded_year INTEGER,
  employee_range TEXT CHECK (employee_range IN ('1-10', '11-50', '51-200', '201-500', '500+', 'UNKNOWN')),

  -- Classification
  company_type TEXT CHECK (company_type IN ('STARTUP', 'SCALEUP', 'ENTERPRISE', 'UNKNOWN')) DEFAULT 'STARTUP',
  is_active BOOLEAN DEFAULT TRUE,

  -- Funding Status (extracted from newsletters)
  total_funding_usd NUMERIC,
  last_funding_round TEXT,
  last_funding_date DATE,
  last_funding_amount_usd NUMERIC,
  lead_investors TEXT[],
  all_investors TEXT[],

  -- Intelligence Metrics
  patent_count INTEGER DEFAULT 0,
  newsletter_mentions INTEGER DEFAULT 0,
  total_funding_rounds INTEGER DEFAULT 0,

  -- Composite Scores
  innovation_score INTEGER CHECK (innovation_score BETWEEN 0 AND 100),
  market_momentum_score INTEGER CHECK (market_momentum_score BETWEEN 0 AND 100),
  funding_velocity_score INTEGER CHECK (funding_velocity_score BETWEEN 0 AND 100),

  -- Metadata
  first_seen_date TIMESTAMP DEFAULT NOW(),
  last_updated TIMESTAMP DEFAULT NOW(),
  data_sources TEXT[]
);

-- 1.3 Intelligence Signals (Unified)
CREATE TABLE IF NOT EXISTS intelligence_signal (
  signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID REFERENCES company(company_id) ON DELETE CASCADE,
  source_id UUID REFERENCES intelligence_source(source_id),

  -- Signal Metadata
  signal_type TEXT CHECK (signal_type IN ('PATENT', 'NEWSLETTER_MENTION', 'FUNDING_ANNOUNCEMENT', 'PRODUCT_LAUNCH', 'ACQUISITION', 'PARTNERSHIP')),
  signal_date DATE NOT NULL,
  signal_title TEXT NOT NULL,
  signal_description TEXT,
  signal_url TEXT,

  -- Relevance
  relevance_score FLOAT CHECK (relevance_score BETWEEN 0 AND 1),
  confidence_score FLOAT CHECK (confidence_score BETWEEN 0 AND 1),

  -- Classification
  sector_primary TEXT,
  sector_tags TEXT[],

  -- Signal-Specific Data (JSONB)
  signal_metadata JSONB,

  -- Metadata
  ingested_at TIMESTAMP DEFAULT NOW(),
  last_analyzed TIMESTAMP DEFAULT NOW()
);

-- 1.4 Patent Applications (Specialized)
CREATE TABLE IF NOT EXISTS patent_application (
  patent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_id UUID REFERENCES intelligence_signal(signal_id) ON DELETE CASCADE,
  company_id UUID REFERENCES company(company_id) ON DELETE CASCADE,

  -- USPTO Identifiers
  publication_number TEXT UNIQUE NOT NULL,
  application_number TEXT,

  -- Patent Content
  title TEXT NOT NULL,
  abstract TEXT,
  claims_text TEXT,
  filing_date DATE NOT NULL,
  publication_date DATE,

  -- Classification
  primary_cpc_code TEXT,
  all_cpc_codes TEXT[],
  sector_primary TEXT,
  sector_tags TEXT[],

  -- AI Analysis
  innovation_summary TEXT,
  technical_novelty_score INTEGER CHECK (technical_novelty_score BETWEEN 1 AND 10),
  market_relevance TEXT CHECK (market_relevance IN ('High', 'Medium', 'Low')),
  commercial_potential TEXT CHECK (commercial_potential IN ('High', 'Medium', 'Low')),

  -- Links
  google_patents_url TEXT,

  -- Metadata
  ingested_at TIMESTAMP DEFAULT NOW()
);

-- 1.5 Newsletter Mentions (Enhanced for VC Tracking)
CREATE TABLE IF NOT EXISTS newsletter_mention (
  mention_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_id UUID REFERENCES intelligence_signal(signal_id) ON DELETE CASCADE,
  company_id UUID REFERENCES company(company_id) ON DELETE CASCADE,

  -- Article Metadata
  article_title TEXT NOT NULL,
  article_url TEXT UNIQUE NOT NULL,
  publication_name TEXT NOT NULL,
  publication_date DATE NOT NULL,
  author TEXT,

  -- Content
  article_excerpt TEXT,
  mention_context TEXT,
  full_article_text TEXT,

  -- Classification
  article_category TEXT CHECK (article_category IN (
    'FUNDING_ANNOUNCEMENT', 
    'PRODUCT_LAUNCH', 
    'ACQUISITION', 
    'PARTNERSHIP', 
    'THREAT_ANALYSIS', 
    'INDUSTRY_NEWS',
    'PERSONNEL_CHANGE',
    'GENERAL'
  )),
  sentiment TEXT CHECK (sentiment IN ('positive', 'neutral', 'negative', 'unknown')),
  sector_tags TEXT[],

  -- Funding Data
  funding_round_type TEXT,
  funding_amount_usd NUMERIC,
  lead_investor TEXT,
  participating_investors TEXT[],

  -- Metadata
  ingested_at TIMESTAMP DEFAULT NOW()
);

-- 1.6 Investor Intelligence
CREATE TABLE IF NOT EXISTS investor (
  investor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  investor_name TEXT NOT NULL UNIQUE,
  investor_name_normalized TEXT NOT NULL UNIQUE,

  -- Investor Profile
  investor_type TEXT CHECK (investor_type IN ('VC', 'CORPORATE_VC', 'ANGEL', 'PE', 'ACCELERATOR', 'UNKNOWN')),
  investor_website TEXT,
  investor_location TEXT,

  -- Focus Areas
  stage_focus TEXT[],
  sector_focus TEXT[],

  -- Activity Metrics
  total_investments INTEGER DEFAULT 0,
  total_investments_this_month INTEGER DEFAULT 0,
  total_investments_this_quarter INTEGER DEFAULT 0,
  last_investment_date DATE,
  avg_check_size_usd NUMERIC,

  -- Intelligence Signals
  portfolio_companies TEXT[],
  recent_activity_score INTEGER CHECK (recent_activity_score BETWEEN 0 AND 100),

  -- Metadata
  first_seen_date TIMESTAMP DEFAULT NOW(),
  last_updated TIMESTAMP DEFAULT NOW()
);

-- 1.7 Company-Investor Relationships (Junction)
CREATE TABLE IF NOT EXISTS company_investor (
  relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID REFERENCES company(company_id) ON DELETE CASCADE,
  investor_id UUID REFERENCES investor(investor_id) ON DELETE CASCADE,

  -- Investment Details
  round_type TEXT,
  investment_date DATE,
  amount_usd NUMERIC,
  is_lead BOOLEAN DEFAULT FALSE,

  -- Source
  source_signal_id UUID REFERENCES intelligence_signal(signal_id),

  -- Metadata
  recorded_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(company_id, investor_id, round_type, investment_date)
);

-- 1.8 Inventor Profiles (From Patents)
CREATE TABLE IF NOT EXISTS inventor (
  inventor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  inventor_name TEXT NOT NULL,
  inventor_name_normalized TEXT NOT NULL UNIQUE,

  -- Career Tracking
  patent_count INTEGER DEFAULT 1,
  is_serial_inventor BOOLEAN DEFAULT FALSE,
  companies_list TEXT[],

  -- Enrichment (Phase 2)
  linkedin_url TEXT,
  current_title TEXT,
  current_company TEXT,

  -- Flags
  is_academic BOOLEAN DEFAULT FALSE,
  is_solo_inventor BOOLEAN DEFAULT FALSE,

  -- Metadata
  first_seen_date TIMESTAMP DEFAULT NOW(),
  last_updated TIMESTAMP DEFAULT NOW()
);

-- 1.9 Patent-Inventor Junction
CREATE TABLE IF NOT EXISTS patent_inventor (
  patent_id UUID REFERENCES patent_application(patent_id) ON DELETE CASCADE,
  inventor_id UUID REFERENCES inventor(inventor_id) ON DELETE CASCADE,
  inventor_sequence INTEGER,
  PRIMARY KEY (patent_id, inventor_id)
);

-- ============================================
-- SECTION 2: INDEXES
-- ============================================

-- Company
CREATE INDEX IF NOT EXISTS idx_company_name_normalized ON company(company_name_normalized);
CREATE INDEX IF NOT EXISTS idx_company_type ON company(company_type) WHERE company_type = 'STARTUP';
CREATE INDEX IF NOT EXISTS idx_company_innovation_score ON company(innovation_score DESC);
CREATE INDEX IF NOT EXISTS idx_company_last_funding ON company(last_funding_date DESC NULLS LAST);

-- Intelligence Signal
CREATE INDEX IF NOT EXISTS idx_signal_company ON intelligence_signal(company_id);
CREATE INDEX IF NOT EXISTS idx_signal_date ON intelligence_signal(signal_date DESC);
CREATE INDEX IF NOT EXISTS idx_signal_type ON intelligence_signal(signal_type);
CREATE INDEX IF NOT EXISTS idx_signal_sector ON intelligence_signal(sector_primary);

-- Patent Application
CREATE INDEX IF NOT EXISTS idx_patent_filing_date ON patent_application(filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_patent_company ON patent_application(company_id);
CREATE INDEX IF NOT EXISTS idx_patent_novelty ON patent_application(technical_novelty_score DESC);

-- Newsletter Mention
CREATE INDEX IF NOT EXISTS idx_mention_company ON newsletter_mention(company_id);
CREATE INDEX IF NOT EXISTS idx_mention_date ON newsletter_mention(publication_date DESC);
CREATE INDEX IF NOT EXISTS idx_mention_category ON newsletter_mention(article_category);
CREATE INDEX IF NOT EXISTS idx_mention_funding ON newsletter_mention(article_category) WHERE article_category = 'FUNDING_ANNOUNCEMENT';

-- Investor
CREATE INDEX IF NOT EXISTS idx_investor_name_normalized ON investor(investor_name_normalized);
CREATE INDEX IF NOT EXISTS idx_investor_activity ON investor(total_investments_this_month DESC);
CREATE INDEX IF NOT EXISTS idx_investor_last_investment ON investor(last_investment_date DESC);

-- Company-Investor
CREATE INDEX IF NOT EXISTS idx_company_investor_company ON company_investor(company_id);
CREATE INDEX IF NOT EXISTS idx_company_investor_investor ON company_investor(investor_id);
CREATE INDEX IF NOT EXISTS idx_company_investor_date ON company_investor(investment_date DESC);

-- Inventor
CREATE INDEX IF NOT EXISTS idx_inventor_patent_count ON inventor(patent_count DESC);
CREATE INDEX IF NOT EXISTS idx_inventor_serial ON inventor(is_serial_inventor) WHERE is_serial_inventor = TRUE;

-- Patent-Inventor
CREATE INDEX IF NOT EXISTS idx_patent_inventor_patent ON patent_inventor(patent_id);
CREATE INDEX IF NOT EXISTS idx_patent_inventor_inventor ON patent_inventor(inventor_id);

-- ============================================
-- SECTION 3: MATERIALIZED VIEWS
-- ============================================

-- Dashboard - Company Intelligence
CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_company_intelligence AS
SELECT 
  c.company_id,
  c.company_name,
  c.company_website,
  c.founded_year,
  c.last_funding_round,
  c.last_funding_date,
  c.last_funding_amount_usd,
  c.lead_investors,
  c.patent_count,
  c.newsletter_mentions,
  MAX(CASE WHEN s.signal_type = 'PATENT' THEN s.signal_date END) AS last_patent_date,
  MAX(CASE WHEN s.signal_type = 'NEWSLETTER_MENTION' THEN s.signal_date END) AS last_mention_date,
  MAX(CASE WHEN s.signal_type = 'FUNDING_ANNOUNCEMENT' THEN s.signal_date END) AS last_funding_signal_date,
  c.innovation_score,
  c.market_momentum_score,
  MODE() WITHIN GROUP (ORDER BY s.sector_primary) AS primary_sector,
  CASE 
    WHEN MAX(s.signal_date) >= CURRENT_DATE - INTERVAL '30 days' THEN 100
    WHEN MAX(s.signal_date) >= CURRENT_DATE - INTERVAL '90 days' THEN 70
    WHEN MAX(s.signal_date) >= CURRENT_DATE - INTERVAL '180 days' THEN 40
    ELSE 10
  END AS recency_score,
  (
    COUNT(DISTINCT CASE WHEN s.signal_type = 'PATENT' AND s.signal_date > CURRENT_DATE - INTERVAL '6 months' THEN s.signal_id END) * 5 +
    COUNT(DISTINCT CASE WHEN s.signal_type = 'NEWSLETTER_MENTION' AND s.signal_date > CURRENT_DATE - INTERVAL '3 months' THEN s.signal_id END) * 3 +
    COUNT(DISTINCT CASE WHEN s.signal_type = 'FUNDING_ANNOUNCEMENT' AND s.signal_date > CURRENT_DATE - INTERVAL '12 months' THEN s.signal_id END) * 10
  ) AS heat_score
FROM company c
LEFT JOIN intelligence_signal s ON c.company_id = s.company_id
WHERE c.company_type = 'STARTUP' AND c.is_active = TRUE
GROUP BY 
  c.company_id, c.company_name, c.company_website, c.founded_year,
  c.last_funding_round, c.last_funding_date, c.last_funding_amount_usd,
  c.lead_investors, c.patent_count, c.newsletter_mentions,
  c.innovation_score, c.market_momentum_score;

CREATE INDEX IF NOT EXISTS idx_dashboard_heat_score ON dashboard_company_intelligence(heat_score DESC);

-- Dashboard - Active VCs
CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_active_vcs AS
SELECT 
  i.investor_id,
  i.investor_name,
  i.investor_website,
  i.investor_location,
  i.sector_focus,
  COUNT(DISTINCT CASE 
    WHEN ci.investment_date >= DATE_TRUNC('month', CURRENT_DATE) 
    THEN ci.company_id 
  END) AS investments_this_month,
  COUNT(DISTINCT CASE 
    WHEN ci.investment_date >= DATE_TRUNC('quarter', CURRENT_DATE) 
    THEN ci.company_id 
  END) AS investments_this_quarter,
  SUM(CASE 
    WHEN ci.investment_date >= DATE_TRUNC('month', CURRENT_DATE) AND ci.is_lead = TRUE
    THEN ci.amount_usd 
  END) AS total_deployed_this_month,
  ARRAY_AGG(
    DISTINCT c.company_name
  ) FILTER (WHERE ci.investment_date >= DATE_TRUNC('month', CURRENT_DATE)) AS companies_invested_this_month,
  MODE() WITHIN GROUP (ORDER BY ci.round_type) AS most_common_stage,
  MAX(ci.investment_date) AS last_investment_date
FROM investor i
LEFT JOIN company_investor ci ON i.investor_id = ci.investor_id
LEFT JOIN company c ON ci.company_id = c.company_id
WHERE ci.investment_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY i.investor_id, i.investor_name, i.investor_website, i.investor_location, i.sector_focus
HAVING COUNT(DISTINCT CASE WHEN ci.investment_date >= DATE_TRUNC('month', CURRENT_DATE) THEN ci.company_id END) > 0;

CREATE INDEX IF NOT EXISTS idx_dashboard_vc_activity ON dashboard_active_vcs(investments_this_month DESC);

-- Dashboard - Trending Sectors
CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_trending_sectors AS
WITH sector_momentum AS (
  SELECT 
    s.sector_primary,
    COUNT(DISTINCT CASE 
      WHEN s.signal_date >= DATE_TRUNC('month', CURRENT_DATE) 
      THEN s.signal_id 
    END) AS signals_this_month,
    COUNT(DISTINCT CASE 
      WHEN s.signal_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
           AND s.signal_date < DATE_TRUNC('month', CURRENT_DATE)
      THEN s.signal_id 
    END) AS signals_last_month,
    COUNT(DISTINCT CASE 
      WHEN s.signal_type = 'PATENT' AND s.signal_date >= DATE_TRUNC('month', CURRENT_DATE)
      THEN s.signal_id 
    END) AS patents_this_month,
    COUNT(DISTINCT CASE 
      WHEN s.signal_type = 'FUNDING_ANNOUNCEMENT' AND s.signal_date >= DATE_TRUNC('month', CURRENT_DATE)
      THEN s.signal_id 
    END) AS funding_rounds_this_month,
    SUM(CASE 
      WHEN nm.funding_amount_usd IS NOT NULL AND nm.publication_date >= DATE_TRUNC('month', CURRENT_DATE)
      THEN nm.funding_amount_usd 
    END) AS total_funding_this_month,
    COUNT(DISTINCT CASE 
      WHEN s.signal_date >= DATE_TRUNC('month', CURRENT_DATE)
      THEN s.company_id 
    END) AS active_companies_this_month
  FROM intelligence_signal s
  LEFT JOIN newsletter_mention nm ON s.signal_id = nm.signal_id
  WHERE s.sector_primary IS NOT NULL
    AND s.signal_date >= CURRENT_DATE - INTERVAL '3 months'
  GROUP BY s.sector_primary
)
SELECT 
  sector_primary,
  signals_this_month,
  signals_last_month,
  patents_this_month,
  funding_rounds_this_month,
  total_funding_this_month,
  active_companies_this_month,
  CASE 
    WHEN signals_last_month > 0 THEN 
      ROUND(((signals_this_month::FLOAT - signals_last_month::FLOAT) / signals_last_month::FLOAT * 100)::NUMERIC, 1)
    ELSE 100.0
  END AS momentum_percent,
  CASE 
    WHEN signals_this_month > signals_last_month THEN 'UP'
    WHEN signals_this_month < signals_last_month THEN 'DOWN'
    ELSE 'FLAT'
  END AS trend_direction
FROM sector_momentum
WHERE signals_this_month > 0
ORDER BY signals_this_month DESC;

CREATE INDEX IF NOT EXISTS idx_dashboard_sector_momentum ON dashboard_trending_sectors(signals_this_month DESC);

-- ============================================
-- SECTION 4: HELPER FUNCTIONS
-- ============================================

CREATE OR REPLACE FUNCTION increment_newsletter_mentions(company_id_param UUID)
RETURNS VOID AS $$
BEGIN
  UPDATE company 
  SET newsletter_mentions = newsletter_mentions + 1,
      last_updated = NOW()
  WHERE company_id = company_id_param;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculate_company_scores(company_id_param UUID)
RETURNS TABLE(
  innovation_score INT,
  market_momentum_score INT,
  funding_velocity_score INT
) AS $$
BEGIN
  RETURN QUERY
  WITH company_signals AS (
    SELECT 
      COUNT(DISTINCT CASE WHEN signal_type = 'PATENT' THEN signal_id END) AS patent_count,
      COUNT(DISTINCT CASE WHEN signal_type = 'NEWSLETTER_MENTION' THEN signal_id END) AS mention_count,
      COUNT(DISTINCT CASE WHEN signal_type = 'FUNDING_ANNOUNCEMENT' THEN signal_id END) AS funding_count,
      AVG(CASE WHEN signal_type = 'PATENT' THEN 
        (SELECT technical_novelty_score FROM patent_application WHERE signal_id = s.signal_id)
      END) AS avg_novelty
    FROM intelligence_signal s
    WHERE s.company_id = company_id_param
      AND s.signal_date >= CURRENT_DATE - INTERVAL '12 months'
  )
  SELECT 
    LEAST(100, (patent_count * 15 + (avg_novelty * 5))::INT) AS innovation_score,
    LEAST(100, (mention_count * 10)::INT) AS market_momentum_score,
    LEAST(100, (funding_count * 25)::INT) AS funding_velocity_score
  FROM company_signals;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION refresh_all_dashboard_views()
RETURNS VOID AS $$
BEGIN
  REFRESH MATERIALIZED VIEW dashboard_company_intelligence;
  REFRESH MATERIALIZED VIEW dashboard_active_vcs;
  REFRESH MATERIALIZED VIEW dashboard_trending_sectors;
  RAISE NOTICE 'All dashboard views refreshed at %', NOW();
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION refresh_materialized_view(view_name TEXT)
RETURNS VOID AS $$
BEGIN
  EXECUTE format('REFRESH MATERIALIZED VIEW %I', view_name);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION daily_score_update()
RETURNS VOID AS $$
DECLARE
  company_record RECORD;
  scores RECORD;
BEGIN
  FOR company_record IN 
    SELECT company_id FROM company WHERE is_active = TRUE
  LOOP
    SELECT * INTO scores FROM calculate_company_scores(company_record.company_id);
    UPDATE company SET
      innovation_score = scores.innovation_score,
      market_momentum_score = scores.market_momentum_score,
      funding_velocity_score = scores.funding_velocity_score,
      last_updated = NOW()
    WHERE company_id = company_record.company_id;
  END LOOP;
  PERFORM refresh_all_dashboard_views();
END;
$$ LANGUAGE plpgsql;
