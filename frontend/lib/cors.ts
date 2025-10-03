/**
 * CORS Utility - API Route Protection (Task 1.5)
 * 
 * Provides helper functions for setting CORS headers on API routes.
 * 
 * Security Features:
 * - Origin validation against whitelist
 * - Method restrictions
 * - Header restrictions
 * - Preflight request handling
 * 
 * Usage:
 * ```typescript
 * import { corsHeaders, handleCors } from '@/lib/cors';
 * 
 * export async function GET(request: Request) {
 *   const corsResponse = handleCors(request);
 *   if (corsResponse) return corsResponse;
 *   
 *   // Your API logic here
 *   return new Response('OK', { headers: corsHeaders(request) });
 * }
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';

// CORS configuration
const ALLOWED_ORIGINS = [
  'http://localhost:3000',
  'https://localhost:3000',
  // Add production domains dynamically
  ...(process.env.NEXT_PUBLIC_VERCEL_URL 
    ? [`https://${process.env.NEXT_PUBLIC_VERCEL_URL}`] 
    : []
  ),
  ...(process.env.VERCEL_URL 
    ? [`https://${process.env.VERCEL_URL}`] 
    : []
  ),
];

const ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'];
const ALLOWED_HEADERS = ['Content-Type', 'Authorization', 'X-Requested-With', 'X-CSRF-Token'];

/**
 * Check if origin is allowed
 */
function isOriginAllowed(origin: string | null): boolean {
  if (!origin) return true; // Same-origin requests don't send Origin header
  
  // Check exact match
  if (ALLOWED_ORIGINS.includes(origin)) return true;
  
  // Allow all Vercel preview deployments
  if (origin.endsWith('.vercel.app')) return true;
  
  return false;
}

/**
 * Get CORS headers for a request
 * 
 * @param request - The incoming request
 * @returns Headers object with CORS headers
 */
export function corsHeaders(request: Request | NextRequest): Headers {
  const headers = new Headers();
  const origin = request.headers.get('origin');
  
  if (origin && isOriginAllowed(origin)) {
    headers.set('Access-Control-Allow-Origin', origin);
    headers.set('Access-Control-Allow-Methods', ALLOWED_METHODS.join(', '));
    headers.set('Access-Control-Allow-Headers', ALLOWED_HEADERS.join(', '));
    headers.set('Access-Control-Max-Age', '86400'); // 24 hours
    headers.set('Vary', 'Origin'); // Important for caching
  }
  
  return headers;
}

/**
 * Handle CORS preflight (OPTIONS) requests
 * 
 * @param request - The incoming request
 * @returns NextResponse for preflight, or null if not a preflight
 */
export function handleCors(request: Request | NextRequest): NextResponse | null {
  // Only handle OPTIONS requests
  if (request.method !== 'OPTIONS') return null;
  
  const origin = request.headers.get('origin');
  
  // Check if origin is allowed
  if (origin && !isOriginAllowed(origin)) {
    return new NextResponse(null, {
      status: 403,
      statusText: 'Forbidden - Origin not allowed',
    });
  }
  
  // Return preflight response
  return new NextResponse(null, {
    status: 204,
    headers: corsHeaders(request),
  });
}

/**
 * Wrap an API response with CORS headers
 * 
 * @param request - The incoming request
 * @param response - The API response
 * @returns Response with CORS headers added
 */
export function withCors(
  request: Request | NextRequest,
  response: Response | NextResponse
): Response {
  const headers = new Headers(response.headers);
  const corsHdrs = corsHeaders(request);
  
  // Merge CORS headers
  corsHdrs.forEach((value, key) => {
    headers.set(key, value);
  });
  
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

/**
 * Validate request method
 * 
 * @param request - The incoming request
 * @returns True if method is allowed
 */
export function isMethodAllowed(request: Request | NextRequest): boolean {
  return ALLOWED_METHODS.includes(request.method);
}

/**
 * Create a CORS error response
 * 
 * @param message - Error message
 * @param status - HTTP status code
 * @returns NextResponse with error
 */
export function corsError(message: string, status: number = 403): NextResponse {
  return new NextResponse(
    JSON.stringify({ error: message }),
    {
      status,
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );
}

