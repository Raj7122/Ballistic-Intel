/**
 * Supabase Client Configuration
 * 
 * Creates a singleton Supabase client for browser usage.
 * Uses Next.js environment variables for configuration.
 * 
 * Security: Public anon key is safe to expose (Row-Level Security enforced server-side)
 */

import { createClient } from '@supabase/supabase-js';
import type { Database } from '@/types/database.types';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing Supabase environment variables. Please check your .env.local file.'
  );
}

/**
 * Supabase client instance
 * 
 * @example
 * ```ts
 * import { supabase } from '@/lib/supabase';
 * 
 * const { data, error } = await supabase
 *   .from('company')
 *   .select('*')
 *   .limit(10);
 * ```
 */
export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: false, // MVP: No authentication
    autoRefreshToken: false,
  },
  realtime: {
    params: {
      eventsPerSecond: 10, // Rate limit for real-time updates
    },
  },
});


