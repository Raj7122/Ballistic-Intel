# Project Plan: CyberPatent Intelligence Platform

## 1. Project Overview

### **Application Type:** Full-Stack Web Application (Progressive Web App)
### **Target Platform:** Modern Browsers (Chrome, Firefox, Safari, Edge)
### **Motivation:** 
Provide early-stage cybersecurity deal flow intelligence by aggregating USPTO patents and industry newsletters - delivering a **12-18 month lead time** advantage over traditional platforms like PitchBook, at **zero cost**.

### **Target Audience:** 
- Primary: Venture capital analysts (intermediate technical proficiency)
- Secondary: Cybersecurity industry researchers, startup founders
- Technical Comfort: High (familiar with data dashboards, VC terminology)

### **User Journey Map:**
1. **Land on Dashboard** → See high-level metrics (companies tracked, patents, funding rounds, active VCs)
2. **Browse Market Intelligence** → Filter companies by sector, innovation score, funding status
3. **Analyze Top VCs** → Identify most active investors this month, view their portfolios
4. **Track Funding Rounds** → See recent announcements with investor networks
5. **Explore Trending Sectors** → Understand momentum in sub-sectors (Zero Trust, Cloud Security, etc.)
6. **Deep Dive Patents** → Review high-novelty patents, understand innovation trends
7. **Export/Share Insights** → (Phase 2) Generate reports, sync to CRM

---

## 2. Technical Architecture & Design

### **Technology Stack:**

#### **Frontend:**
- **Framework:** Next.js 14 (App Router) + TypeScript
- **State Management:** React Context API + TanStack Query (React Query v5) for server state
- **Styling:** Tailwind CSS + shadcn/ui components
- **Data Visualization:** Recharts + D3.js for complex charts
- **Real-time Updates:** Supabase Realtime subscriptions
- **Key Libraries:**
  - `@tanstack/react-query` - Server state, caching, real-time sync
  - `@supabase/supabase-js` - Database client
  - `recharts` - Declarative charts
  - `date-fns` - Date manipulation
  - `zod` - Runtime type validation
  - `react-hot-toast` - Notifications

#### **Backend:**
- **API Layer:** Next.js API Routes (TypeScript)
- **Background Jobs:** Separate Python pipeline (orchestrator.py) → runs via cron/scheduler
- **Database ORM:** Supabase SDK (auto-generated TypeScript types)
- **Authentication:** None (MVP) → Supabase Auth (Phase 2)
- **Validation:** Zod schemas shared between client/server

#### **Database:**
- **Type:** PostgreSQL (Supabase hosted)
- **Materialized Views:** For dashboard performance (5-minute TTL)
- **Indexes:** Optimized for hot queries (company_name, signal_date, heat_score)
- **Row-Level Security:** Disabled for MVP (public access)

#### **AI/ML Pipeline:**
- **Model:** Google Gemini 1.5 Flash (free tier: 15 RPM)
- **Use Cases:** 
  - Patent relevance filtering
  - Funding data extraction from newsletters
  - Company entity resolution
  - Sector classification
- **Caching:** Redis-compatible cache (Upstash) for AI responses (30-day TTL)

#### **Testing:**
- **Unit Testing:** Vitest (frontend) + pytest (Python agents)
- **Integration Testing:** Playwright (E2E critical paths)
- **E2E Testing:** Playwright - 3 critical flows:
  1. Dashboard loads → All tabs render data
  2. Filter companies → Results update correctly
  3. View patent details → Modal opens with full data
- **API Testing:** Supertest (Next.js API routes)

#### **Deployment:**
- **Frontend:** Vercel (Next.js native, free tier)
- **Database:** Supabase (free tier: 500MB, 50k monthly active users)
- **Background Pipeline:** Railway.app / Render.com (free tier, scheduled jobs)
- **CI/CD:** GitHub Actions → Auto-deploy on push to main

---

### **UI/UX Design System:**

#### **Component Library:** shadcn/ui (Radix UI primitives + Tailwind)
**Rationale:** 
- Accessible by default (WCAG 2.1 AA compliant)
- Customizable (copy-paste, not npm dependency)
- Beautiful, modern aesthetic
- TypeScript-first

#### **Design Methodology:** Atomic Design Pattern
- **Atoms:** Button, Input, Badge, Card
- **Molecules:** StatCard, CompanyCard, PatentCard, InvestorCard
- **Organisms:** CompanyTable, FundingTimeline, SectorHeatmap
- **Templates:** DashboardLayout, DetailsLayout
- **Pages:** Home, CompanyDetails, InvestorProfile

#### **UX Principles Applied:**

**Fitts's Law Implementation:**
- Primary CTAs: 48px minimum touch target (mobile-first)
- Filter buttons: 40px height, generously spaced
- Tab navigation: Full-width clickable areas

**Hick's Law Application:**
- Main navigation: 5 tabs max (Market Intel, VCs, Funding, Sectors, Patents)
- Filters: Collapsed by default, max 3 visible at once
- Company cards: Show 3 key metrics upfront, hide rest in expandable

**Miller's Rule Adherence:**
- Company list: Show 20 items per page (7±2 chunks of ~3 companies)
- Metrics: 4 summary cards at top (within working memory limit)
- Sector tags: Display max 5 tags, "+3 more" for overflow

**Jakob's Law Compliance:**
- Dashboard layout: Familiar BI tool structure (filters left, content center, details right)
- Sorting/filtering: Standard dropdown patterns
- Data tables: Conventional header sort, row hover states

**Krug's Usability Principles:**
- **Self-Evident:** Icon + label for all actions, no mystery meat navigation
- **Eliminate Ambiguity:** "Last Funding: $5M Series A (Oct 2024)" vs vague "Recent Activity"
- **Concise Copy:** "100 Companies" not "There are currently one hundred companies being tracked in the system"

#### **Accessibility Standard:** WCAG 2.1 AA
- Keyboard navigation: Full support (Tab, Enter, Escape)
- Screen readers: Semantic HTML, ARIA labels
- Color contrast: 4.5:1 minimum for text
- Focus indicators: 3px solid ring on all interactive elements

#### **Responsive Strategy:** Mobile-First Adaptive
- **Mobile (320px+):** Single column, stacked metrics, hamburger filters
- **Tablet (768px+):** Two-column layout, side-by-side metrics
- **Desktop (1024px+):** Three-column, persistent sidebar filters
- **Large Desktop (1440px+):** Four-column, expanded chart areas

#### **Information Architecture:**
```
Dashboard Home
├── Header (Logo, Last Updated timestamp)
├── Summary Metrics (4 cards: Companies, Patents, Funding Rounds, Active VCs)
├── Tab Navigation (5 tabs)
│   ├── Tab 1: Market Intelligence
│   │   ├── Filters (Sidebar: Sectors, Activity Level, Innovation Score)
│   │   ├── Company Cards (Grid/List toggle)
│   │   └── Pagination
│   ├── Tab 2: Top 5 Active VCs
│   │   ├── VC Ranking Cards
│   │   ├── Portfolio Breakdown (Expandable)
│   │   └── Activity Chart (Bar chart)
│   ├── Tab 3: Recent Funding Rounds
│   │   ├── Funding Cards (Timeline view)
│   │   ├── Summary Metrics (Total raised, Avg round)
│   │   └── Stage Distribution (Pie chart)
│   ├── Tab 4: Trending Sub-Sectors
│   │   ├── Sector Cards (With momentum %)
│   │   ├── Activity Heatmap (Bar chart)
│   │   └── MoM Comparison (Grouped bar chart)
│   └── Tab 5: Patent Deep Dive
│       ├── Patent Cards (With novelty scores)
│       ├── Filters (Date range, Sector)
│       └── Filing Timeline (Line chart)
└── Footer (Data sources, Last sync time)
```

#### **Color System:**
- **Primary:** `#667EEA` (Purple-blue, trust & innovation)
- **Secondary:** `#764BA2` (Deep purple, premium feel)
- **Success:** `#10B981` (Green, positive signals)
- **Warning:** `#F59E0B` (Amber, funding alerts)
- **Danger:** `#EF4444` (Red, declined trends)
- **Neutral:** `#64748B` (Slate, text/borders)
- **Background:** `#F8FAFC` (Light gray, reduced eye strain)

#### **Typography:**
- **Heading Font:** `Inter` (system fallback: `-apple-system, BlinkMacSystemFont`)
- **Body Font:** `Inter` (optimized for data-heavy interfaces)
- **Monospace:** `JetBrains Mono` (for numeric data, patent numbers)
- **Sizes:**
  - H1: 2.5rem / 40px (Dashboard title)
  - H2: 1.875rem / 30px (Tab headers)
  - H3: 1.5rem / 24px (Card titles)
  - Body: 1rem / 16px (Standard text)
  - Small: 0.875rem / 14px (Metadata, labels)

---

### **Security & Threat Model:**

#### **Authentication:** 
- **MVP:** None (public demo, no sensitive user data)
- **Phase 2:** Supabase Auth (Magic Link + OAuth Google)

#### **Authorization:** 
- **MVP:** Public read-only access
- **Phase 2:** RBAC (Admin, Analyst, Viewer roles)

#### **Data Protection:**
- **Encryption at Rest:** Supabase default (AES-256)
- **Encryption in Transit:** TLS 1.3 (enforced by Vercel/Supabase)
- **Key Management:** Environment variables (Vercel secrets, never committed)

#### **OWASP Top 10 Mitigations:**

**1. Injection (SQL, NoSQL):**
- ✅ **Parameterized Queries:** Supabase client uses prepared statements
- ✅ **Input Validation:** Zod schemas on all API inputs
- ✅ **ORM:** Supabase PostgREST (prevents raw SQL in frontend)

**2. Broken Authentication:**
- ✅ **No Authentication in MVP** (deferred risk)
- 🔄 **Phase 2:** MFA via Supabase, session management with httpOnly cookies

**3. Sensitive Data Exposure:**
- ✅ **No PII Stored:** Public company data only
- ✅ **API Keys:** Stored in environment variables, rotated quarterly
- ✅ **HTTPS Enforced:** Vercel auto-redirects HTTP → HTTPS

**4. XML External Entities (XXE):**
- ✅ **No XML Parsing:** JSON-only API responses
- ✅ **RSS Feeds:** Parsed server-side with sanitization (feedparser library)

**5. Broken Access Control:**
- ✅ **MVP:** All data public (no access control needed)
- 🔄 **Phase 2:** Row-Level Security (RLS) in Supabase

**6. Security Misconfiguration:**
- ✅ **CSP Headers:** Next.js security headers configured
- ✅ **CORS:** Restricted to Vercel domain + localhost
- ✅ **Error Handling:** Generic messages to client, detailed logs server-side

**7. Cross-Site Scripting (XSS):**
- ✅ **React Auto-Escaping:** JSX prevents XSS by default
- ✅ **DOMPurify:** Sanitize any user-generated content (Phase 2 comments)
- ✅ **CSP:** `script-src 'self'` prevents inline scripts

**8. Insecure Deserialization:**
- ✅ **JSON Only:** No binary serialization formats
- ✅ **Schema Validation:** Zod validates all incoming data

**9. Using Components with Known Vulnerabilities:**
- ✅ **Dependabot:** GitHub auto-PRs for security updates
- ✅ **npm audit:** Run on every CI build
- ✅ **Snyk:** Free tier scanning for vulnerabilities

**10. Insufficient Logging & Monitoring:**
- ✅ **Vercel Analytics:** Built-in performance monitoring
- ✅ **Supabase Logs:** Database query logs (7-day retention)
- ✅ **Error Tracking:** Sentry (free tier, 5k events/month)
- ✅ **Pipeline Logs:** Python logging to file + stdout

#### **CIS Benchmark Compliance:**
- **CIS Docker Benchmark v1.5.0** (for Railway/Render containers)
  - ✅ Principle of least privilege (non-root user in containers)
  - ✅ Immutable infrastructure (containers rebuilt on each deploy)
  - ✅ Image scanning (Docker Scout in CI/CD)

---

## 3. High-Level Task Breakdown

### **Phase 1: Environment Setup & Security Hardening**
- [ ] **Task 1.1: Initialize Next.js Project**
  - **Description:** Create Next.js 14 app with TypeScript, Tailwind, ESLint
  - **Success Criteria:** `npm run dev` starts without errors, TypeScript strict mode enabled
  - **Testing Strategy:** Build succeeds, no type errors

- [ ] **Task 1.2: Configure Supabase Database**
  - **Description:** Create Supabase project, run schema SQL, seed intelligence sources
  - **Success Criteria:** All 9 tables created, indexes applied, materialized views working
  - **Testing Strategy:** Run test queries, verify view refresh performance (<2s)

- [x] **Task 1.3: Set Up Google Cloud & BigQuery**
  - **Description:** Create GCP project, enable BigQuery API, configure service account
  - **Success Criteria:** Test query to `patents-public-data` succeeds
  - **Testing Strategy:** Fetch 10 sample patents via Python script
  - **Artifacts:** `pipeline/test_bigquery.py`, `pipeline/README.md`, credentials at `credentials/planar-door-474015-u3-6040c3948b61.json`
  - **Project ID:** `planar-door-474015-u3` (from BigQuery client)
  - **Result:** Test query succeeded (10 rows). Reported processed: ~33,386.02 MB. Mitigation for pipeline: restrict date windows (e.g., last 14–30 days), select minimal columns, and leverage query cache.

- [x] **Task 1.4: Configure Gemini API**
  - **Description:** Get API key, test prompt with sample article
  - **Success Criteria:** Extract funding data from test article with 80%+ accuracy
  - **Testing Strategy:** Unit test with 5 known funding announcements
  - **Result:** ✅ 100% extraction accuracy (5/5 test cases). 19/19 unit tests passing. Model: `gemini-2.5-flash`
  - **Artifacts:** `pipeline/clients/gemini_client.py`, `pipeline/utils/funding_extractor.py`, `pipeline/tests/test_gemini_client.py`
  - **Documentation:** `pipeline/docs/GEMINI_API.md`, `pipeline/docs/SECURITY.md`

- [x] **Task 1.5: Security Baseline**
  - **Description:** Configure Next.js security headers, CSP with nonce, CORS policies
  - **Success Criteria:** Security headers present in all responses, CSP score A+ (securityheaders.com), no CSP violations
  - **Testing Strategy:** Manual header verification, browser console checks, automated OWASP ZAP scan (future)
  - **Implementation:**
    - Strict security headers in `next.config.ts`: HSTS (preload), X-Frame-Options (DENY), X-Content-Type-Options, Referrer-Policy, Permissions-Policy, COOP, COEP, CORP
    - Nonce-based CSP in `middleware.ts`: No `unsafe-inline` for scripts (production), `strict-dynamic` policy
    - CORS utility in `lib/cors.ts`: Origin validation, preflight handling, method/header restrictions
    - Nonce propagation in `app/layout.tsx`: Per-request nonce from middleware
  - **Artifacts:** `frontend/middleware.ts`, `frontend/lib/cors.ts`, `frontend/app/api/health/route.ts`
  - **Security Features:**
    - ✅ HSTS with preload (2 years)
    - ✅ X-Frame-Options: DENY (prevents clickjacking)
    - ✅ Nonce-based CSP (prevents XSS)
    - ✅ CORS origin validation
    - ✅ Permissions-Policy deny-by-default
    - ✅ Cross-origin isolation (COOP, COEP, CORP)

---

### **Phase 2: Backend Data Pipeline (Python Agents)**
- [ ] **Task 2.1: Agent P1a - Patent Ingestion**
  - **Description:** Fetch cybersecurity patents from BigQuery, parse metadata
  - **Success Criteria:** Retrieve 50+ patents from last 7 days, extract title/abstract/CPC codes
  - **Testing Strategy:** Unit tests (pytest) - verify data structure, mock BigQuery
  - **Implementation:**
    - Patent model with parsing/validation (`pipeline/models/patent.py`)
    - BigQuery client with retries and cost tracking (`pipeline/clients/bigquery_client.py`)
    - Optimized query builder with CPC/date filters (`pipeline/agents/query_builder.py`)
    - Ingestion agent with 7-day window and 30-day fallback (`pipeline/agents/p1a_patent_ingestion.py`)
  - **Artifacts:**
    - Tests and fixtures: `pipeline/tests/test_p1a_patent_ingestion.py`, `pipeline/tests/fixtures/patents.json`
    - Updated dependencies: `tenacity`, `pytest-mock` in `pipeline/requirements.txt`
  - **Result (current):** ✅ 6 unit tests passing (parsing, query builder, fallback, error handling)
  - **Notes:** Integration against live BigQuery deferred to Task 2.7 (Orchestrator) to minimize quota (S.A.F.E: Strategic).

- [x] **Task 2.2: Agent P1b - Newsletter Ingestion**
  - **Description:** Parse RSS feeds (TheCyberwire, DarkReading, etc.), extract articles
  - **Success Criteria:** Fetch 100+ articles from last 7 days, identify funding announcements
  - **Testing Strategy:** Unit tests - mock feedparser, validate article schema

  - **Implementation:**
    - NewsArticle model with stable ID and serialization (models/news_article.py)
    - RSSClient with retry logic and rate limiting (clients/rss_client.py)
    - FeedParser with date filtering (parsers/feed_parser.py)
    - ArticleFetcher for HTML extraction via BeautifulSoup (clients/article_fetcher.py)
    - FundingDetector with multi-signal heuristics (logic/funding_detector.py)
    - NewsletterIngestionAgent orchestrator (agents/p1b_newsletter_ingestion.py)
    - Configuration for 4 RSS feeds (config/p1b_config.py)
  - **Artifacts:**
    - Tests and fixtures: tests/test_p1b_newsletter_ingestion.py, tests/fixtures/rss/sample_feed.xml
    - Dependencies: feedparser, beautifulsoup4, lxml added to requirements.txt
  - **Result:** ✅ 8 unit tests passing (model, detector, parser, agent end-to-end)
  - **Funding Detection:** Requires ≥2 signals (action + money/stage/investor/valuation) for high precision

- [ ] **Task 2.3: Agent P2 - Universal Relevance Filter**
  - **Description:** Use Gemini to filter cybersecurity-relevant signals
  - **Success Criteria:** 70%+ precision on test set (20 signals)
  - **Testing Strategy:** Integration test with labeled dataset

- [ ] **Task 2.4: Agent P3 - Extraction & Classification**
  - **Description:** Extract company names, sectors, novelty scores using Gemini
  - **Success Criteria:** Classify patents into 12 sectors with 80%+ accuracy
  - **Testing Strategy:** Unit tests with ground truth labels

- [ ] **Task 2.5: Agent P4 - Entity Resolution**
  - **Description:** Deduplicate company names (fuzzy matching + normalization)
  - **Success Criteria:** "Palo Alto Networks" = "Palo Alto" = "PAN Inc"
  - **Testing Strategy:** Unit tests with known duplicates

- [ ] **Task 2.6: Agent P5 - Database Ingestion**
  - **Description:** Insert signals into Supabase, update company metrics, refresh views
  - **Success Criteria:** 100% of filtered signals ingested, no duplicates
  - **Testing Strategy:** Integration test - full pipeline → database populated

- [ ] **Task 2.7: Orchestrator Pipeline**
  - **Description:** Coordinate all agents, handle errors, log statistics
  - **Success Criteria:** Complete pipeline runs in <15 minutes for 7 days of data
  - **Testing Strategy:** E2E test - verify all tables populated correctly

---

### **Phase 3: Frontend - Component Library**
- [ ] **Task 3.1: Install shadcn/ui + Base Components**
  - **Description:** Set up Tailwind, install Button, Card, Badge, Input components
  - **Success Criteria:** Storybook renders all base components
  - **Testing Strategy:** Visual regression tests (Chromatic)

- [ ] **Task 3.2: Build Molecules - StatCard**
  - **Description:** Metric card with value, label, icon, optional trend indicator
  - **Success Criteria:** Renders correctly on mobile/desktop, accessible
  - **Testing Strategy:** Vitest component tests, Playwright visual tests

- [ ] **Task 3.3: Build Molecules - CompanyCard**
  - **Description:** Company name, sector, metrics (patents, mentions), expandable details
  - **Success Criteria:** Smooth expand/collapse, keyboard accessible
  - **Testing Strategy:** Vitest interaction tests, Playwright E2E

- [ ] **Task 3.4: Build Molecules - PatentCard, InvestorCard, FundingCard**
  - **Description:** Specialized cards for each data type
  - **Success Criteria:** Consistent styling, all edge cases handled (missing data)
  - **Testing Strategy:** Vitest with mock data

- [ ] **Task 3.5: Build Organisms - CompanyTable**
  - **Description:** Sortable, filterable table with pagination
  - **Success Criteria:** Handles 100+ rows, sorts in <100ms
  - **Testing Strategy:** Performance tests, Playwright E2E sorting

- [ ] **Task 3.6: Build Organisms - Charts (Recharts)**
  - **Description:** Bar chart (VC activity), Pie chart (funding stages), Line chart (patent timeline)
  - **Success Criteria:** Responsive, tooltips work, accessible (screen reader announces values)
  - **Testing Strategy:** Visual tests, accessibility audit (axe-core)

---

### **Phase 4: Frontend - Pages & Data Fetching**
- [ ] **Task 4.1: Set Up TanStack Query**
  - **Description:** Configure React Query client, cache settings, refetch strategies
  - **Success Criteria:** Queries cached for 5 minutes, auto-refetch on window focus
  - **Testing Strategy:** Verify cache behavior in DevTools

- [ ] **Task 4.2: Create API Routes (Next.js)**
  - **Description:** 
    - `/api/companies` - Get filtered companies
    - `/api/vcs` - Get top active VCs
    - `/api/funding` - Get recent funding rounds
    - `/api/sectors` - Get trending sectors
    - `/api/patents` - Get recent patents
  - **Success Criteria:** All routes return JSON, handle errors gracefully
  - **Testing Strategy:** Supertest integration tests

- [ ] **Task 4.3: Set Up Supabase Realtime**
  - **Description:** Subscribe to `intelligence_signal` table changes, invalidate queries
  - **Success Criteria:** Dashboard updates within 5 seconds of new signal
  - **Testing Strategy:** Insert test signal, verify UI updates

- [ ] **Task 4.4: Dashboard Home Page**
  - **Description:** 4 summary stat cards, tab navigation
  - **Success Criteria:** Loads in <2 seconds, all data accurate
  - **Testing Strategy:** Playwright E2E - verify stats match database

- [ ] **Task 4.5: Tab 1 - Market Intelligence**
  - **Description:** Company list with filters (sector, activity, innovation score)
  - **Success Criteria:** Filter updates URL params, shareable links work
  - **Testing Strategy:** Playwright E2E - apply filters, verify results

- [ ] **Task 4.6: Tab 2 - Top 5 Active VCs**
  - **Description:** VC cards with investment counts, portfolio breakdown, bar chart
  - **Success Criteria:** Chart renders correctly, portfolio expands/collapses
  - **Testing Strategy:** Playwright visual tests

- [ ] **Task 4.7: Tab 3 - Recent Funding Rounds**
  - **Description:** Funding cards with metrics, pie chart (stage distribution)
  - **Success Criteria:** Timeline view scrollable, links to articles work
  - **Testing Strategy:** Playwright E2E - click article link, verify new tab

- [ ] **Task 4.8: Tab 4 - Trending Sub-Sectors**
  - **Description:** Sector cards with momentum %, heatmap, MoM comparison chart
  - **Success Criteria:** Charts update on data refresh, trend icons correct
  - **Testing Strategy:** Vitest - verify momentum calculation logic

- [ ] **Task 4.9: Tab 5 - Patent Deep Dive**
  - **Description:** Patent cards with abstracts, novelty scores, timeline chart
  - **Success Criteria:** Abstract expands/collapses, Google Patents links work
  - **Testing Strategy:** Playwright E2E - expand abstract, click link

---

### **Phase 5: Testing & Quality Assurance**
- [ ] **Task 5.1: Unit Tests - Frontend Components**
  - **Description:** Vitest tests for all molecules/organisms
  - **Success Criteria:** 80%+ coverage, all edge cases tested
  - **Testing Strategy:** Run `npm test` in CI

- [ ] **Task 5.2: Unit Tests - Python Agents**
  - **Description:** pytest for all 5 agents (P1a-P5)
  - **Success Criteria:** 80%+ coverage, mock external APIs
  - **Testing Strategy:** Run `pytest --cov` in CI

- [ ] **Task 5.3: Integration Tests - API Routes**
  - **Description:** Supertest for all Next.js API routes
  - **Success Criteria:** All routes tested (happy path + error cases)
  - **Testing Strategy:** Run in CI after database setup

- [ ] **Task 5.4: E2E Tests - Critical Paths (Playwright)**
  - **Description:** 
    1. Dashboard loads → All tabs render
    2. Filter companies → Results update
    3. View patent → Modal opens
  - **Success Criteria:** All flows complete in <30 seconds
  - **Testing Strategy:** Run on every PR, record videos on failure

- [ ] **Task 5.5: Performance Testing**
  - **Description:** Lighthouse audit (target: 90+ performance score)
  - **Success Criteria:** Dashboard loads in <3s on 3G, FCP <1.8s
  - **Testing Strategy:** Automated Lighthouse in CI

- [ ] **Task 5.6: Accessibility Audit**
  - **Description:** axe-core scan, keyboard navigation test
  - **Success Criteria:** 0 accessibility violations, all features keyboard-accessible
  - **Testing Strategy:** Playwright with axe-playwright plugin

- [ ] **Task 5.7: Security Scan**
  - **Description:** OWASP ZAP baseline scan, npm audit
  - **Success Criteria:** 0 high/critical vulnerabilities
  - **Testing Strategy:** Run in CI, fail build on critical issues

---

### **Phase 6: Deployment & Optimization**
- [ ] **Task 6.1: Deploy Database (Supabase)**
  - **Description:** Provision production instance, apply schema
  - **Success Criteria:** Database accessible via public URL, RLS disabled (MVP)
  - **Testing Strategy:** Run test queries from Postman

- [ ] **Task 6.2: Deploy Frontend (Vercel)**
  - **Description:** Connect GitHub repo, configure environment variables
  - **Success Criteria:** Live URL accessible, environment secrets loaded
  - **Testing Strategy:** Smoke test - load dashboard, verify data appears

- [ ] **Task 6.3: Deploy Pipeline (Railway/Render)**
  - **Description:** Containerize Python app, set up cron job (daily 6 AM UTC)
  - **Success Criteria:** Pipeline runs on schedule, logs accessible
  - **Testing Strategy:** Trigger manual run, verify database updated

- [ ] **Task 6.4: Configure CI/CD (GitHub Actions)**
  - **Description:** 
    - Workflow 1: Run tests on PR
    - Workflow 2: Deploy to Vercel on merge to main
    - Workflow 3: Security scan weekly
  - **Success Criteria:** All workflows pass, auto-deploy works
  - **Testing Strategy:** Create test PR, verify checks run

- [ ] **Task 6.5: Performance Optimization**
  - **Description:** 
    - Enable Next.js Image Optimization
    - Implement code splitting (dynamic imports)
    - Add service worker for offline support
  - **Success Criteria:** Lighthouse score 90+, TTI <3.5s
  - **Testing Strategy:** Lighthouse CI

- [ ] **Task 6.6: Caching Strategy**
  - **Description:** 
    - Supabase PostgREST cache headers (5 min)
    - React Query stale time (5 min)
    - CDN caching (Vercel Edge Network)
  - **Success Criteria:** Repeat visits load in <500ms
  - **Testing Strategy:** Network waterfall analysis

- [ ] **Task 6.7: Error Monitoring (Sentry)**
  - **Description:** Install Sentry SDK, configure source maps upload
  - **Success Criteria:** Errors logged with stack traces, user context
  - **Testing Strategy:** Trigger test error, verify Sentry dashboard

- [ ] **Task 6.8: Analytics (Vercel Analytics)**
  - **Description:** Enable Web Analytics, track page views
  - **Success Criteria:** Dashboard shows real-time visitors
  - **Testing Strategy:** Visit dashboard, verify event logged

---

## 4. File Structure

```
ballistic-intel/
├── frontend/                      # Next.js application
│   ├── app/                       # App Router (Next.js 14)
│   │   ├── layout.tsx             # Root layout
│   │   ├── page.tsx               # Dashboard home
│   │   ├── api/                   # API routes
│   │   │   ├── companies/route.ts
│   │   │   ├── vcs/route.ts
│   │   │   ├── funding/route.ts
│   │   │   ├── sectors/route.ts
│   │   │   └── patents/route.ts
│   │   └── globals.css            # Tailwind imports
│   ├── components/                # React components
│   │   ├── ui/                    # shadcn/ui base components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   └── ...
│   │   ├── molecules/             # Composite components
│   │   │   ├── StatCard.tsx
│   │   │   ├── CompanyCard.tsx
│   │   │   ├── PatentCard.tsx
│   │   │   ├── InvestorCard.tsx
│   │   │   └── FundingCard.tsx
│   │   ├── organisms/             # Complex components
│   │   │   ├── CompanyTable.tsx
│   │   │   ├── VCRanking.tsx
│   │   │   ├── FundingTimeline.tsx
│   │   │   ├── SectorHeatmap.tsx
│   │   │   └── PatentList.tsx
│   │   └── layout/                # Layout components
│   │       ├── DashboardLayout.tsx
│   │       ├── Header.tsx
│   │       └── Footer.tsx
│   ├── lib/                       # Utilities
│   │   ├── supabase.ts            # Supabase client
│   │   ├── queries.ts             # React Query hooks
│   │   ├── schemas.ts             # Zod validation schemas
│   │   └── utils.ts               # Helper functions
│   ├── hooks/                     # Custom React hooks
│   │   ├── useCompanies.ts
│   │   ├── useVCs.ts
│   │   ├── useFunding.ts
│   │   └── useRealtime.ts
│   ├── types/                     # TypeScript types
│   │   ├── database.types.ts      # Supabase generated types
│   │   └── index.ts
│   ├── public/                    # Static assets
│   │   └── logo.svg
│   ├── tests/                     # Frontend tests
│   │   ├── unit/                  # Vitest component tests
│   │   └── e2e/                   # Playwright tests
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── package.json
│   └── .env.local                 # Local environment variables
│
├── pipeline/                      # Python data pipeline
│   ├── agents/
│   │   ├── p1a_patent_ingestion.py
│   │   ├── p1b_newsletter_ingestion.py
│   │   ├── p2_universal_filter.py
│   │   ├── p3_extraction_classification.py
│   │   ├── p4_entity_resolution.py
│   │   └── p5_database_ingestion.py
│   ├── orchestrator.py            # Main pipeline coordinator
│   ├── config.py                  # Configuration
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/                     # Python tests
│       ├── test_patent_agent.py
│       ├── test_newsletter_agent.py
│       └── test_orchestrator.py
│
├── database/
│   ├── schema.sql                 # Supabase schema
│   ├── seed.sql                   # Seed data
│   └── migrations/                # Schema migrations
│
├── docs/
│   ├── plan.md                    # This file
│   ├── log.md                     # Error tracking
│   └── API.md                     # API documentation
│
├── .github/
│   └── workflows/
│       ├── test.yml               # CI tests
│       ├── deploy.yml             # CD deployment
│       └── security.yml           # Weekly security scan
│
├── .gitignore
├── README.md
└── LICENSE
```

---

## 5. Development Phases & Timeline

### **Day 1: Foundation (6-8 hours)**
- [x] Initialize Next.js + TypeScript project
- [x] Set up Supabase database (schema + seed data)
- [x] Configure Google Cloud + BigQuery access
- [x] Test Gemini API with sample prompts
- [x] Install shadcn/ui components
- **Deliverable:** Project scaffolded, all services accessible

### **Day 2-3: Backend Pipeline (12-16 hours)**
- [ ] Implement Agent P1a (Patents)
- [ ] Implement Agent P1b (Newsletters)
- [ ] Implement Agent P2 (Filter)
- [ ] Implement Agent P3 (Extract/Classify)
- [ ] Implement Agent P4 (Entity Resolution)
- [ ] Implement Agent P5 (Database Ingestion)
- [ ] Build Orchestrator
- [ ] Test full pipeline end-to-end
- **Deliverable:** Pipeline ingests 100+ companies, 50+ patents, 10+ funding rounds

### **Day 4-5: Frontend Components (12-16 hours)**
- [ ] Build base components (shadcn/ui)
- [ ] Build molecules (StatCard, CompanyCard, etc.)
- [ ] Build organisms (Tables, Charts)
- [ ] Create API routes
- [ ] Set up React Query
- **Deliverable:** Component library complete, Storybook functional

### **Day 6-7: Frontend Pages (12-16 hours)**
- [ ] Dashboard home page
- [ ] Tab 1: Market Intelligence
- [ ] Tab 2: Top 5 Active VCs
- [ ] Tab 3: Recent Funding Rounds
- [ ] Tab 4: Trending Sub-Sectors
- [ ] Tab 5: Patent Deep Dive
- [ ] Implement real-time updates
- **Deliverable:** All 5 tabs functional with live data

### **Day 8: Testing & Polish (6-8 hours)**
- [ ] Write E2E tests (Playwright)
- [ ] Performance optimization (Lighthouse 90+)
- [ ] Accessibility audit (0 violations)
- [ ] Security scan (OWASP ZAP)
- **Deliverable:** Production-ready application

### **Day 9: Deployment (4-6 hours)**
- [ ] Deploy to Vercel
- [ ] Deploy pipeline to Railway/Render
- [ ] Configure CI/CD (GitHub Actions)
- [ ] Set up monitoring (Sentry)
- **Deliverable:** Live public URL, automated deployments

### **Day 10: Buffer & Demo Prep (4-6 hours)**
- [ ] Final bug fixes
- [ ] Prepare demo script
- [ ] Record demo video (backup)
- [ ] Create presentation slides
- **Deliverable:** Polished demo, presentation ready

---

## 6. Success Metrics

### **MVP Delivery Criteria**
| Metric | Target | Validation Method |
|--------|--------|-------------------|
| **Companies Tracked** | 100+ startups | `SELECT COUNT(*) FROM company WHERE company_type='STARTUP'` |
| **Patents Ingested** | 50+ relevant | `SELECT COUNT(*) FROM patent_application` |
| **Funding Rounds** | 10+ rounds | `SELECT COUNT(*) FROM newsletter_mention WHERE article_category='FUNDING_ANNOUNCEMENT'` |
| **Investors Tracked** | 20+ VCs | `SELECT COUNT(*) FROM investor` |
| **Dashboard Load Time** | <3 seconds | Lighthouse Performance Score |
| **Real-time Updates** | <5 seconds | Insert test signal, measure UI update latency |
| **Mobile Responsive** | 100% features | Test on iPhone 12, Pixel 5 viewports |
| **Accessibility** | 0 violations | axe-core scan |
| **Zero Cost** | $0.00 spent | Check Vercel, Supabase, GCP billing |

### **Testing Coverage Targets**
- **Frontend Unit Tests:** 80%+ coverage (Vitest)
- **Backend Unit Tests:** 80%+ coverage (pytest)
- **E2E Tests:** 3 critical paths (Playwright)
- **Performance:** Lighthouse 90+ (Performance, Accessibility, Best Practices, SEO)

---

## 7. Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Gemini Rate Limits** | High | Medium | Implement exponential backoff, cache responses in Upstash Redis |
| **BigQuery Quota** | Medium | Low | Optimize queries, limit to 1TB/month (free tier), use query cache |
| **Supabase 500MB Limit** | Medium | Low | Archive old signals after 6 months, compress text fields |
| **VC Extraction Accuracy** | High | Medium | Test with 20 known funding announcements, iterate prompts |
| **Real-time Performance** | Medium | Low | Use Supabase Realtime, debounce updates, limit to 100 concurrent connections |
| **Deployment Failures** | Low | Low | GitHub Actions retries, Vercel auto-rollback on errors |

---

## 8. Post-MVP Roadmap (Phase 2+)

### **Phase 2: Source Expansion (Week 2-3)**
- OpenVC integration (ground truth funding data)
- Conference speaker tracking (Black Hat, RSA, etc.)
- CISA Threat Intelligence correlation

### **Phase 3: Advanced Features (Week 4-6)**
- User authentication (Supabase Auth)
- Personalized dashboards (save filters, favorite companies)
- Export to CSV/PDF
- Slack/Email alerts
- LinkedIn founder enrichment
- GitHub activity tracking

### **Phase 4: Production Hardening (Week 7-8)**
- Multi-tenant architecture (VC firm accounts)
- Advanced analytics (predictive funding models)
- API rate limiting (Upstash Rate Limit)
- SOC 2 compliance (audit logs, encryption key rotation)

---

## 9. Notes & Assumptions

- **Free Tier Limits:**
  - Vercel: 100GB bandwidth/month (sufficient for 1,000 monthly users)
  - Supabase: 500MB storage, 50k MAUs (sufficient for MVP)
  - BigQuery: 1TB queries/month (pipeline uses ~100GB)
  - Gemini: 15 RPM (rate-limited but cacheable)

- **Development Environment:**
  - Node.js 20.x
  - Python 3.11
  - pnpm (faster than npm)

- **Browser Support:**
  - Chrome/Edge 90+
  - Firefox 88+
  - Safari 14+
  - No IE11 support

---

**Next Step:** Create `log.md` for error tracking, then activate **Executor Mode** to begin implementation.

