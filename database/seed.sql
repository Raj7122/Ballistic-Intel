-- CyberPatent Intelligence Platform - Seed Data (MVP)

-- Insert MVP sources (USPTO + Newsletters)
INSERT INTO intelligence_source (source_name, source_type, source_url, sync_frequency) VALUES
  ('USPTO_Patents', 'PATENT', 'https://patents.google.com/bigquery', 'weekly'),
  ('Newsletter_TheCyberwire', 'NEWSLETTER', 'https://thecyberwire.com/feeds/rss.xml', 'daily'),
  ('Newsletter_DarkReading', 'NEWSLETTER', 'https://www.darkreading.com/rss.xml', 'daily'),
  ('Newsletter_SecurityWeek', 'NEWSLETTER', 'https://www.securityweek.com/feed/', 'daily')
ON CONFLICT (source_name) DO NOTHING;

-- Verify insertion
SELECT 
  source_name, 
  source_type, 
  is_active, 
  created_at 
FROM intelligence_source 
ORDER BY created_at DESC;
