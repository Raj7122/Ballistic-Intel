# CyberPatent Intelligence Platform - Frontend

Next.js 14 web application for early-stage cybersecurity deal flow intelligence.

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS v4
- **UI Components:** shadcn/ui (Radix UI primitives)
- **State Management:** TanStack Query (React Query v5)
- **Database:** Supabase (PostgreSQL)
- **Charts:** Recharts
- **Fonts:** Inter (UI), JetBrains Mono (data)

## Getting Started

### Prerequisites

- Node.js 20.x or higher
- npm or pnpm

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Add your Supabase credentials to .env.local
# NEXT_PUBLIC_SUPABASE_URL=...
# NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

### Development

```bash
# Run development server
npm run dev

# Open http://localhost:3000
```

### Build

```bash
# Create production build
npm run build

# Start production server
npm start
```

### Testing

```bash
# Run unit tests (Vitest)
npm test

# Run E2E tests (Playwright)
npm run test:e2e

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix
```

## Project Structure

```
frontend/
├── app/                  # Next.js App Router pages
│   ├── api/              # API routes
│   ├── layout.tsx        # Root layout with providers
│   └── page.tsx          # Dashboard home
├── components/
│   ├── ui/               # shadcn/ui base components
│   ├── molecules/        # Composite components
│   ├── organisms/        # Complex components
│   └── layout/           # Layout components
├── lib/
│   ├── supabase.ts       # Supabase client
│   ├── providers.tsx     # React Query provider
│   ├── queries.ts        # React Query hooks
│   └── utils.ts          # Utility functions
├── hooks/                # Custom React hooks
├── types/                # TypeScript types
│   └── database.types.ts # Supabase generated types
└── tests/                # Test files
    ├── unit/             # Vitest component tests
    └── e2e/              # Playwright tests
```

## Environment Variables

Required environment variables:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
```

## Security Features

- ✅ Content Security Policy (CSP)
- ✅ HSTS (HTTP Strict Transport Security)
- ✅ X-Frame-Options (Clickjacking protection)
- ✅ X-Content-Type-Options (MIME sniffing protection)
- ✅ Referrer-Policy
- ✅ Permissions-Policy

## Performance Targets

- Lighthouse Performance: 90+
- First Contentful Paint (FCP): <1.8s
- Time to Interactive (TTI): <3.5s
- Total Blocking Time (TBT): <200ms

## License

Proprietary - Ballistic Ventures
