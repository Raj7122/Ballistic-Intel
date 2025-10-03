/**
 * Application Providers
 * 
 * Wraps the app with necessary context providers:
 * - TanStack Query (React Query) for server state management
 * 
 * Configuration:
 * - 5-minute stale time for dashboard data
 * - Auto-refetch on window focus
 * - Retry failed queries 3 times with exponential backoff
 */

'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState, type ReactNode } from 'react';
import { Toaster } from 'react-hot-toast';

/**
 * Query client configuration
 * Optimized for dashboard use case with moderate caching
 */
function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // 5-minute stale time (matches materialized view refresh)
        staleTime: 5 * 60 * 1000,
        // Refetch when window regains focus (for live demos)
        refetchOnWindowFocus: true,
        // Retry failed queries (network resilience)
        retry: 3,
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      },
      mutations: {
        // Show error toasts for failed mutations
        onError: (error) => {
          console.error('Mutation error:', error);
        },
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined = undefined;

function getQueryClient() {
  if (typeof window === 'undefined') {
    // Server: always create a new query client
    return makeQueryClient();
  } else {
    // Browser: reuse existing client (singleton pattern)
    if (!browserQueryClient) browserQueryClient = makeQueryClient();
    return browserQueryClient;
  }
}

interface ProvidersProps {
  children: ReactNode;
}

/**
 * Providers component
 * 
 * Wraps the application with React Query and toast notifications
 * 
 * @example
 * ```tsx
 * // app/layout.tsx
 * export default function RootLayout({ children }) {
 *   return (
 *     <html>
 *       <body>
 *         <Providers>{children}</Providers>
 *       </body>
 *     </html>
 *   );
 * }
 * ```
 */
export function Providers({ children }: ProvidersProps) {
  const [queryClient] = useState(() => getQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#333',
            color: '#fff',
          },
          success: {
            iconTheme: {
              primary: '#10B981',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#EF4444',
              secondary: '#fff',
            },
          },
        }}
      />
      {/* Dev tools only in development */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}


