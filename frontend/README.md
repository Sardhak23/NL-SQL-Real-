# NL-SQL Analytics Copilot - React Frontend

An enterprise-grade, modern SaaS web client built with React 18, Vite, TypeScript, Tailwind CSS, Recharts, and TanStack Table for autonomous natural language to SQL analytics.

## Tech Stack
- **Framework**: React 18 + Vite (SPA)
- **Language**: TypeScript 5+ (Strict Mode)
- **Styling**: Tailwind CSS with custom Linear/Vercel dark theme palette
- **Data Visualization**: Recharts (Bar, Horizontal Bar, Line, Area, Donut, Scatter)
- **Data Table**: `@tanstack/react-table` (Multi-column sorting, instant search, pagination, CSV export)
- **API Client**: Axios + TanStack React Query
- **Icons**: Lucide React

## Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Development Server
```bash
npm run dev
```
The frontend will start at `http://localhost:5173`. API calls to `/api/*` are automatically proxied to `http://localhost:8000`.

### 3. Production Build
```bash
npm run build
```

## Key Architecture & Features
- **Collapsible Schema Explorer Tree**: Searchable tree browser with table row counts, column types, and PK/FK indicators.
- **Query Composer**: Auto-expanding textarea with keyboard shortcuts (`Enter` / `Shift+Enter`), instant clear, and curated prompt suggestion pills.
- **6-Stage Lifecycle Stepper**: Live tracking of Schema Linking ➔ SQL Generation ➔ AST Safety Check ➔ SQLite Execution ➔ Self-Correction ➔ Executive Insights.
- **3-Tab Results Hub**:
  - **Executive Insights & Charts**: Structured business narrative, KPI cards with trend arrows, and interactive Recharts visualizations with dynamic chart switcher.
  - **Interactive Data Table**: TanStack Table with row count metrics and one-click CSV export.
  - **SQL Inspector & Diagnostics**: Syntax-highlighted SQL with copy button, execution timings, and clause-by-clause logic explainer.
- **Offline Resilient Mode**: Seamless fallback engine providing realistic e-commerce analytics even when backend is connecting.
