# Finlytics AI — Investment Research Dashboard

> **Klypup Applied AI Intern Assessment — Option A: Investment Research Dashboard**

An AI-powered investment research platform for Indian stock markets (NSE/BSE). Analysts type natural language queries like *"Analyse Reliance Industries Q4 FY26 earnings and key risks"* and get back structured, source-attributed reports with financial metrics, news sentiment, and document insights — all within a multi-tenant SaaS architecture.

---

## Why Option A?

Option A matched the intersection of what I wanted to build and what demonstrates real AI engineering depth:

- **Agentic AI** — not just a chatbot, but an agent that decides which tools to call (market data vs news vs documents) based on the query
- **Multi-tenancy** — real SaaS architecture where multiple organizations share the platform with strict data isolation
- **Indian market focus** — yfinance supports NSE/BSE via `.NS`/`.BO` suffixes, making it practical to build for Indian investors without proprietary data feeds
- **Structured output** — the AI returns typed JSON sections (company overview, metrics table, price chart data, news sentiment) that the frontend renders as actual UI components, not a wall of text

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | FastAPI + Python 3.12 | Async-first, excellent type hints, auto-generates OpenAPI docs |
| Database | PostgreSQL 16 | ACID transactions, JSON columns for AI results, mature async driver (asyncpg) |
| ORM | SQLAlchemy 2.0 (async) | Non-blocking DB calls so AI agent tool execution doesn't block the event loop |
| Auth | JWT (python-jose) + bcrypt | Stateless, scales horizontally; bcrypt for secure password hashing |
| AI Agent | LangChain + Groq (Llama 3.3 70B) | `create_tool_calling_agent` with native tool calling; Groq for fast, free inference |
| Vector Store | ChromaDB | Local, zero-infra vector DB for semantic search over financial documents |
| Market Data | Zerodha Kite Connect | Real-time NSE/BSE prices, OHLCV, historical data via official broker API |
| News | NewsAPI | Real-time financial news with keyword-based sentiment classification |
| Frontend | React 18 + Vite + Tailwind CSS | Fast builds, utility-first styling, component-based architecture |
| Container | Docker + Docker Compose | One-command setup; no local Postgres or Python required |

---

## Screenshots

> **Add 4–6 screenshots here before submission**
>
> Suggested screens to capture:
> 1. Login / Signup page
> 2. Dashboard home (recent reports, watchlist summary)
> 3. Research query input page
> 4. Research results page (company card + metrics table + chart)
> 5. Watchlist page
> 6. Organization settings (invite code, members list)

---

## Setup Instructions

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A [Groq API key](https://console.groq.com) (free)
- A [NewsAPI key](https://newsapi.org) (free — optional, falls back to mock data)

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd Finlytics-AI-Terminal
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```env
GROQ_API_KEY=your_groq_api_key_here
NEWS_API_KEY=your_newsapi_key_here
SECRET_KEY=any-long-random-string
```

### 3. Start all services

```bash
docker-compose up --build
```

This starts PostgreSQL, the FastAPI backend, and the React frontend together. First build takes ~5 minutes (downloading images and installing packages).

Wait until you see:
```
backend-1  | INFO:     Application startup complete.
```

### 4. Seed demo data

Open a second terminal in the same directory:

```bash
docker-compose exec backend python -m scripts.seed
```

This creates 2 demo organizations with users and sample research reports.

### 5. Open the app

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8002 |
| API Docs (Swagger) | http://localhost:8002/docs |

### Demo Accounts

| Organization | Email | Password | Role |
|---|---|---|---|
| Alpha Capital Research | admin@alpha.com | password123 | Admin |
| Alpha Capital Research | analyst@alpha.com | password123 | Analyst |
| Beta Ventures | admin@beta.com | password123 | Admin |

> **Multi-tenant isolation test:** Log in as Alpha Capital, run a research query. Then log in as Beta Ventures — you will not see Alpha's data.

### Stopping the app

```bash
docker-compose down
```

Your database data is preserved in a Docker volume. Run `docker-compose up` next time (no `--build` needed).

### Full reset (wipe database)

```bash
docker-compose down -v
docker-compose up --build
docker-compose exec backend python -m scripts.seed
```

---

## API Quick Reference

All endpoints are under `/api/v1`. Full interactive docs at `/docs`.

```
POST  /api/v1/auth/signup          Create account (new org or join via invite code)
POST  /api/v1/auth/login           Login, returns JWT
GET   /api/v1/auth/me              Current user profile

GET   /api/v1/org/                 My organization details
PUT   /api/v1/org/                 Update org (Admin only)
GET   /api/v1/org/members          List org members
GET   /api/v1/org/invite-code      Get invite code (Admin only)

POST  /api/v1/research/query       Submit AI research query
GET   /api/v1/research/            List past reports (search + pagination)
GET   /api/v1/research/{id}        Get single report
PUT   /api/v1/research/{id}        Update title/tags
DELETE /api/v1/research/{id}       Delete report

GET   /api/v1/watchlist/           List watchlist
POST  /api/v1/watchlist/           Add company
DELETE /api/v1/watchlist/{id}      Remove company
```

---

## Project Structure

```
Finlytics-AI-Terminal/
├── backend/
│   ├── app/
│   │   ├── api/          ← Route handlers (auth, org, research, watchlist)
│   │   ├── ai/
│   │   │   ├── agent.py  ← LangChain AgentExecutor orchestrator
│   │   │   └── tools/    ← market_data, news_search, document_search
│   │   ├── models/       ← SQLAlchemy ORM models
│   │   ├── schemas/      ← Pydantic request/response validation
│   │   ├── middleware/   ← TenantMiddleware (JWT → org_id)
│   │   └── utils/        ← JWT + bcrypt security utils
│   ├── scripts/
│   │   ├── seed.py             ← Demo data (orgs, users, reports, watchlist)
│   │   └── ingest_documents.py ← PDF → ChromaDB ingestion pipeline
│   └── data/filings/     ← Drop PDF annual reports here
├── frontend/             ← React 18 + Vite + Tailwind
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Known Limitations

- **No real-time streaming UI** — the research query runs synchronously; the SSE streaming endpoint exists in the backend but the frontend polls rather than streams progress
- **ChromaDB document search** — requires running `python -m scripts.ingest_documents` after dropping PDFs into `backend/data/filings/`. Without this step, the document search tool returns no results (other tools still work)
- **NewsAPI free tier** — limited to 100 requests/day and no articles older than 1 month. The app falls back to mock news data when the API key is missing or the limit is hit
- **Kite access token expires daily** — you must run `python scripts/kite_auth.py` each morning to refresh the token, then restart the backend container
- **No email verification** — signup is immediate, no email confirmation step
- **Single region** — no CDN or multi-region deployment; designed for a single Docker host
- **Indian stocks only** — the system prompt, tools, and seed data are optimised for NSE/BSE. US stocks technically work (via yfinance) but context may be inaccurate
