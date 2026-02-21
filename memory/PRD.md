# Fractal V2.1 — PRD (Product Requirements Document)

**Last Updated:** 2026-02-21  
**Status:** BLOCK A Complete + BLOCK B1-B4 Complete (REAL DATA)

---

## Original Problem Statement

Клонировать репозиторий https://github.com/solyankastayl-cyber/dddddd, поднять фронт, бэк, админку и работать только с областью Fractal. Реализовать 3-Product Architecture: BTC Final, SPX Final, Combined Terminal.

---

## Architecture Overview

### Tech Stack
- **Backend:** Node.js + TypeScript + Fastify + MongoDB (Mongoose)
- **Frontend:** React + TailwindCSS
- **Database:** MongoDB (fractal_dev)
- **Proxy:** Python FastAPI (uvicorn) → TypeScript backend on port 8002

### 3-Product Architecture

| Product | Status | API Namespace | UI Route | Data Status |
|---------|--------|---------------|----------|-------------|
| BTC Terminal | FINAL | `/api/btc/v2.1/*` | `/btc` | Production |
| SPX Terminal | DATA_READY | `/api/spx/v2.1/*` | `/spx` | **Real (19,121 candles)** |
| Combined Terminal | BUILDING | `/api/combined/v2.1/*` | `/combined` | Pending |

---

## What's Been Implemented

### Session 2026-02-21: BLOCK A — BTC Final Isolation ✅

- BTC routes at `/api/btc/v2.1/*`
- SPX routes at `/api/spx/v2.1/*`  
- Combined routes at `/api/combined/v2.1/*`
- AssetSelector component in AdminDashboard

### Session 2026-02-21: BLOCK B1-B4 — SPX Data Foundation ✅

**Backend SPX Module (`/backend/src/modules/spx/`):**
- Complete SPX data pipeline (types, models, services, routes)
- Multiple data sources: Stooq, Yahoo Finance, CSV, Mock generator
- Cohort segmentation: V1950/V1990/V2008/V2020/LIVE
- Validation + Gap audit services
- Resume-safe backfill service

**Data Ingestion Methods:**
1. **yfinance CSV** (Recommended): `python scripts/download_spx.py` → `/api/fractal/v2.1/admin/spx/ingest-csv`
2. **Stooq/Yahoo API**: `/api/fractal/v2.1/admin/spx/ingest` (may be rate-limited)
3. **Mock Generator**: `/api/fractal/v2.1/admin/spx/generate-mock`

---

## SPX Data Status (REAL DATA)

**Source:** Yahoo Finance (yfinance)  
**Total Candles:** 19,121  
**Date Range:** 1950-01-03 → 2025-12-31  

| Cohort | Records | Period | Description |
|--------|---------|--------|-------------|
| V1950 | 10,054 | 1950-1989 | Post-war era |
| V1990 | 4,538 | 1990-2007 | Dot-com + Pre-crisis |
| V2008 | 3,021 | 2008-2019 | GFC + Recovery |
| V2020 | 1,508 | 2020-2025 | COVID + Post-pandemic |
| **Total** | **19,121** | 75 years | Full history |

**Validation:**
- ✅ No NaN values
- ✅ No zero prices
- ✅ No invalid OHLC
- ⚠️ 1 outlier: Black Monday (1987-10-19, -20.5% drop) - valid extreme event

**Notable Gaps:**
- 2001-09-10 → 2001-09-17 (7 days): Post-9/11 market closure
- Holiday weekends: Various 4-5 day gaps

---

## Current System Status

```
Fractal V2.1 — 3-Product Architecture

┌──────────────────────────────────────────┐
│ BTC Terminal        FINAL               │
│   API: /api/btc/v2.1/*                  │
│   Status: Production Ready               │
├──────────────────────────────────────────┤
│ SPX Terminal        DATA_READY          │
│   API: /api/spx/v2.1/*                  │
│   Data: 19,121 REAL candles (1950-2025) │
│   Next: BLOCK B5 Fractal Core Clone     │
├──────────────────────────────────────────┤
│ Combined Terminal   BUILDING            │
│   API: /api/combined/v2.1/*             │
│   Depends on: SPX Terminal Complete     │
└──────────────────────────────────────────┘

Data Source: Yahoo Finance (yfinance)
CSV File: /app/data/spx_1950_2025.csv
```

---

## Prioritized Backlog

### P0 (Critical) ✅ DONE
- [x] BLOCK A: BTC Final Isolation
- [x] BLOCK B1-B4: SPX Data Foundation
- [x] Real SPX data via yfinance (19,121 candles)

### P1 (High) - Next
- [ ] BLOCK B5: SPX Fractal Core Clone
  - Horizons 7d/14d/30d/90d/180d/365d
  - Primary match selector
  - Divergence engine
  - Phase engine + consensus

### P2 (Medium)
- [ ] BLOCK B6: SPX Memory Layer
- [ ] BLOCK B7: SPX Intel Stack
- [ ] BLOCK C: Combined Terminal

---

## API Endpoints Summary

### SPX Terminal APIs
```
GET  /api/spx/v2.1/info              # Product info
GET  /api/spx/v2.1/stats             # Data statistics
GET  /api/spx/v2.1/status            # Build status
GET  /api/spx/v2.1/terminal          # Terminal data
GET  /api/market-data/candles        # Query candles

POST /api/fractal/v2.1/admin/spx/ingest       # Ingest from Stooq/Yahoo
POST /api/fractal/v2.1/admin/spx/ingest-csv   # Ingest from CSV file
POST /api/fractal/v2.1/admin/spx/backfill     # Run backfill
POST /api/fractal/v2.1/admin/spx/generate-mock # Generate mock data
GET  /api/fractal/v2.1/admin/spx/validate     # Data validation
GET  /api/fractal/v2.1/admin/spx/gaps         # Gap audit
GET  /api/fractal/v2.1/admin/spx/cohorts      # Cohort breakdown
POST /api/fractal/v2.1/admin/spx/indexes      # Ensure indexes
```

---

## Next Tasks

1. **BLOCK B5**: Clone BTC Fractal Core for SPX
   - Apply horizons/phases/consensus to SPX candles
   - Create `/api/spx/v2.1/terminal` full endpoint
   - Build SPX Terminal UI

2. **BLOCK B6**: SPX Memory Layer (snapshots/outcomes)

3. After SPX complete → BLOCK C for Combined Terminal
