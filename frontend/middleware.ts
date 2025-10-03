import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Middleware - Security Headers & CSP with Nonce (Task 1.5)
 * 
 * Responsibilities:
 * 1. Generate per-request nonce for CSP
 * 2. Set strict Content-Security-Policy header
 * 3. Handle CORS preflight for API routes
 * 
 * Security Features:
 * - Nonce-based CSP (no unsafe-inline for scripts)
 * - CORS policy for API routes
 * - Development vs Production CSP variants
 * 
 * @see https://nextjs.org/docs/app/building-your-application/routing/middleware
 */

// Generate cryptographically secure nonce
function generateNonce(): string {
  // Use Web Crypto API for secure random bytes
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  return Buffer.from(array).toString('base64');
}

// Build Content Security Policy
function buildCSP(nonce: string, isDevelopment: boolean): string {
  // Supabase project URL (replace with your actual project URL or env var)
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const supabaseDomain = supabaseUrl.replace('https://', '').replace('http://', '');
  
  // Base CSP directives
  const cspDirectives = [
    // Default: only same-origin
    "default-src 'self'",
    
    // Scripts: nonce-based (strict), allow Next.js chunks
    // 'strict-dynamic' allows scripts loaded by nonce'd scripts
    isDevelopment
      ? "script-src 'self' 'unsafe-eval' 'unsafe-inline'" // Dev mode needs eval for HMR
      : `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`,
    
    // Styles: allow inline for Tailwind CSS (future: migrate to hashed styles)
    "style-src 'self' 'unsafe-inline'",
    
    // Images: self, data URIs, blob (for charts), HTTPS
    "img-src 'self' data: blob: https:",
    
    // Fonts: self and data URIs
    "font-src 'self' data:",
    
    // Connect (fetch/XHR/WebSocket): self, Supabase, Vercel Analytics
    supabaseDomain
      ? `connect-src 'self' https://${supabaseDomain} wss://${supabaseDomain} https://vitals.vercel-insights.com`
      : "connect-src 'self' https://*.supabase.co wss://*.supabase.co https://vitals.vercel-insights.com",
    
    // Object/Embed: block all
    "object-src 'none'",
    
    // Base URI: only self (prevents base tag injection)
    "base-uri 'self'",
    
    // Form actions: only self
    "form-action 'self'",
    
    // Frame ancestors: none (already set X-Frame-Options: DENY)
    "frame-ancestors 'none'",
    
    // Upgrade insecure requests (HTTP -> HTTPS)
    isDevelopment ? '' : 'upgrade-insecure-requests',
  ];
  
  return cspDirectives.filter(Boolean).join('; ');
}

// CORS configuration
const CORS_CONFIG = {
  allowedOrigins: [
    'http://localhost:3000',
    'https://localhost:3000',
    // Vercel preview/production domains (wildcard for deployments)
    ...(process.env.VERCEL_URL ? [`https://${process.env.VERCEL_URL}`] : []),
    ...(process.env.NEXT_PUBLIC_VERCEL_URL ? [`https://${process.env.NEXT_PUBLIC_VERCEL_URL}`] : []),
  ],
  allowedMethods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With', 'X-CSRF-Token'],
  credentials: false, // Stateless API for MVP
};

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isDevelopment = process.env.NODE_ENV !== 'production';
  
  // Generate nonce for this request
  const nonce = generateNonce();
  
  // Build CSP with nonce
  const csp = buildCSP(nonce, isDevelopment);
  
  // Start with base response
  const response = NextResponse.next();
  
  // Set Content-Security-Policy header
  response.headers.set('Content-Security-Policy', csp);
  
  // Pass nonce to the request for use in layout/components
  // This is accessible via headers() in server components
  response.headers.set('x-nonce', nonce);
  
  // Handle CORS for API routes
  if (pathname.startsWith('/api/')) {
    const origin = request.headers.get('origin') || '';
    
    // Check if origin is allowed
    const isAllowedOrigin = 
      !origin || // Same-origin requests don't send Origin header
      CORS_CONFIG.allowedOrigins.includes(origin) ||
      origin.endsWith('.vercel.app'); // Allow all Vercel deployments
    
    if (isAllowedOrigin && origin) {
      response.headers.set('Access-Control-Allow-Origin', origin);
    }
    
    // Handle preflight OPTIONS requests
    if (request.method === 'OPTIONS') {
      const preflightResponse = new NextResponse(null, { status: 204 });
      
      if (isAllowedOrigin && origin) {
        preflightResponse.headers.set('Access-Control-Allow-Origin', origin);
      }
      
      preflightResponse.headers.set(
        'Access-Control-Allow-Methods',
        CORS_CONFIG.allowedMethods.join(', ')
      );
      
      preflightResponse.headers.set(
        'Access-Control-Allow-Headers',
        CORS_CONFIG.allowedHeaders.join(', ')
      );
      
      preflightResponse.headers.set('Access-Control-Max-Age', '86400'); // 24 hours
      
      return preflightResponse;
    }
    
    // Set CORS headers for actual API requests
    if (origin) {
      response.headers.set('Access-Control-Allow-Credentials', String(CORS_CONFIG.credentials));
    }
  }
  
  return response;
}

// Configure middleware matcher
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization)
     * - favicon.ico, robots.txt, sitemap.xml
     */
    {
      source: '/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml).*)',
      missing: [
        { type: 'header', key: 'next-router-prefetch' },
        { type: 'header', key: 'purpose', value: 'prefetch' },
      ],
    },
  ],
};

