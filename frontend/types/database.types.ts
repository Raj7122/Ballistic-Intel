/**
 * Supabase Database Types
 * 
 * Auto-generated TypeScript types for Supabase schema.
 * 
 * To regenerate:
 * npx supabase gen types typescript --project-id <project-id> > types/database.types.ts
 * 
 * For now, this is a placeholder. Will be populated after Supabase setup.
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      company: {
        Row: {
          company_id: string;
          company_name: string;
          company_name_normalized: string;
          company_website: string | null;
          company_country: string;
          company_state: string | null;
          company_city: string | null;
          founded_year: number | null;
          employee_range: string | null;
          company_type: string;
          is_active: boolean;
          total_funding_usd: number | null;
          last_funding_round: string | null;
          last_funding_date: string | null;
          last_funding_amount_usd: number | null;
          lead_investors: string[] | null;
          all_investors: string[] | null;
          patent_count: number;
          newsletter_mentions: number;
          total_funding_rounds: number;
          innovation_score: number | null;
          market_momentum_score: number | null;
          funding_velocity_score: number | null;
          first_seen_date: string;
          last_updated: string;
          data_sources: string[] | null;
        };
        Insert: Omit<Database['public']['Tables']['company']['Row'], 'company_id' | 'first_seen_date' | 'last_updated'>;
        Update: Partial<Database['public']['Tables']['company']['Insert']>;
      };
      // Add other tables as needed
      [key: string]: {
        Row: Record<string, unknown>;
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
      };
    };
    Views: {
      dashboard_company_intelligence: {
        Row: {
          company_id: string;
          company_name: string;
          company_website: string | null;
          founded_year: number | null;
          last_funding_round: string | null;
          last_funding_date: string | null;
          last_funding_amount_usd: number | null;
          lead_investors: string[] | null;
          patent_count: number;
          newsletter_mentions: number;
          last_patent_date: string | null;
          last_mention_date: string | null;
          last_funding_signal_date: string | null;
          innovation_score: number | null;
          market_momentum_score: number | null;
          primary_sector: string | null;
          recency_score: number;
          heat_score: number;
        };
      };
      dashboard_active_vcs: {
        Row: {
          investor_id: string;
          investor_name: string;
          investor_website: string | null;
          investor_location: string | null;
          sector_focus: string[] | null;
          investments_this_month: number;
          investments_this_quarter: number;
          total_deployed_this_month: number | null;
          companies_invested_this_month: string[] | null;
          most_common_stage: string | null;
          last_investment_date: string | null;
        };
      };
      dashboard_trending_sectors: {
        Row: {
          sector_primary: string;
          signals_this_month: number;
          signals_last_month: number;
          patents_this_month: number;
          funding_rounds_this_month: number;
          total_funding_this_month: number | null;
          active_companies_this_month: number;
          momentum_percent: number;
          trend_direction: string;
        };
      };
      [key: string]: {
        Row: Record<string, unknown>;
      };
    };
    Functions: {
      [key: string]: {
        Args: Record<string, unknown>;
        Returns: unknown;
      };
    };
  };
}


