/**
 * Health Check API Route
 * 
 * Simple endpoint to verify API is running and test CORS configuration.
 * 
 * Security:
 * - CORS headers handled by middleware.ts
 * - No sensitive data exposed
 * 
 * @returns JSON with status and timestamp
 */

import { NextRequest, NextResponse } from 'next/server';
import { handleCors, corsHeaders } from '@/lib/cors';

export async function GET(request: NextRequest) {
  // Handle CORS preflight
  const corsResponse = handleCors(request);
  if (corsResponse) return corsResponse;
  
  // Health check response
  const health = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development',
    version: '1.0.0',
  };
  
  return NextResponse.json(health, {
    status: 200,
    headers: corsHeaders(request),
  });
}

export async function OPTIONS(request: NextRequest) {
  return handleCors(request) || new NextResponse(null, { status: 204 });
}

