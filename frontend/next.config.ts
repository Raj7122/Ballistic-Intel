import type { NextConfig } from "next";

/**
 * Next.js Configuration - Security Hardened (Task 1.5)
 * 
 * Security headers follow OWASP recommendations and aim for A+ on securityheaders.com:
 * - HSTS: Forces HTTPS with preload
 * - X-Frame-Options: Prevents clickjacking
 * - X-Content-Type-Options: Prevents MIME sniffing
 * - Referrer-Policy: Minimizes information leakage
 * - Permissions-Policy: Deny-by-default for sensitive features
 * - COOP/COEP/CORP: Cross-origin isolation
 * 
 * CSP is handled dynamically in middleware.ts with nonce-based script execution.
 */

const nextConfig: NextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,

  // Static security headers (CSP is dynamic in middleware.ts)
  async headers() {
    return [
      {
        // Apply to all routes
        source: '/(.*)',
        headers: [
          // HSTS - Force HTTPS for 2 years with subdomains and preload
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
          // Prevent MIME type sniffing
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          // Prevent clickjacking - deny all framing
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          // Minimize referrer information leakage
          {
            key: 'Referrer-Policy',
            value: 'no-referrer',
          },
          // Permissions Policy - deny all by default
          // Enable only what's needed (none for MVP)
          {
            key: 'Permissions-Policy',
            value: [
              'camera=()',
              'microphone=()',
              'geolocation=()',
              'interest-cohort=()', // Disable FLoC
              'payment=()',
              'usb=()',
              'magnetometer=()',
              'gyroscope=()',
              'accelerometer=()',
            ].join(', '),
          },
          // Cross-Origin-Opener-Policy - isolate browsing context
          {
            key: 'Cross-Origin-Opener-Policy',
            value: 'same-origin',
          },
          // Cross-Origin-Embedder-Policy - require CORP for subresources
          // Using unsafe-none to avoid breaking third-party resources
          {
            key: 'Cross-Origin-Embedder-Policy',
            value: 'unsafe-none', // Can upgrade to 'require-corp' after testing
          },
          // Cross-Origin-Resource-Policy - same origin only
          {
            key: 'Cross-Origin-Resource-Policy',
            value: 'same-origin',
          },
          // DNS prefetch control (performance)
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
        ],
      },
    ];
  },

  // Image optimization (for future logo/icons)
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '*.supabase.co',
        pathname: '/storage/**',
      },
    ],
  },

  // Experimental features
  experimental: {
    // Enable server actions for future forms
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
};

export default nextConfig;
