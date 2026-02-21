# Fractal V2.1 — PRD (Product Requirements Document)

**Last Updated:** 2026-02-21  
**Status:** BLOCK A Complete + BLOCK B1-B4 Complete

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

| Product | Status | API Namespace | UI Route | Data |
|---------|--------|---------------|----------|------|
| BTC Terminal | FINAL | `/api/btc/v2.1/*` | `/btc` | Production |
| SPX Terminal | BUILDING | `/api/spx/v2.1/*` | `/spx` | Mock (19,828 candles) |
| Combined Terminal | BUILDING | `/api/combined/v2.1/*` | `/combined` | Pending |

### Module Isolation
- `modules/btc/**` → imports only `core/**`
- `modules/spx/**` → imports only `core/**`
- `modules/combined/**` → can read from btc/spx (read-only)

---

## What's Been Implemented

### Session 2026-02-21: BLOCK A — BTC Final Isolation ✅

**Backend:**
- BTC, SPX, Combined route registration in `app.fractal.ts`
- BTC routes at `/api/btc/v2.1/*`
- SPX routes at `/api/spx/v2.1/*`
- Combined routes at `/api/combined/v2.1/*`

**Frontend:**
- AssetSelector component with 3 product buttons
- Dynamic tabs based on selected asset
- BTC = active, SPX = available, COMBINED = coming soon

### Session 2026-02-21: BLOCK B1-B4 — SPX Data Foundation ✅

**Backend SPX Module (`/backend/src/modules/spx/`):**
- `spx.constants.ts` - Configuration
- `spx.types.ts` - Type definitions
- `spx.mongo.ts` - MongoDB models (spx_candles, spx_backfill_progress, spx_ingestion_log)
- `spx.cohorts.ts` - Cohort segmentation (V1950/V1990/V2008/V2020/LIVE)
- `spx.stooq.client.ts` - Stooq CSV fetcher/parser
- `spx.yahoo.client.ts` - Yahoo Finance fallback
- `spx.mock.generator.ts` - Mock data generator
- `spx.normalizer.ts` - Data normalization
- `spx.ingest.service.ts` - Idempotent ingestion
- `spx.backfill.service.ts` - Resume-safe backfill
- `spx.validation.service.ts` - Data integrity checks
- `spx.candles.service.ts` - Query service
- `spx.routes.ts` - Full API routes

**SPX API Endpoints:**
- `GET /api/spx/v2.1/info` - Product info
- `GET /api/spx/v2.1/stats` - Data statistics
- `GET /api/spx/v2.1/status` - Build status
- `GET /api/market-data/candles?symbol=SPX` - Query candles
- `POST /api/fractal/v2.1/admin/spx/ingest` - Ingest from Stooq/Yahoo
- `POST /api/fractal/v2.1/admin/spx/backfill` - Run backfill
- `POST /api/fractal/v2.1/admin/spx/generate-mock` - Generate mock data
- `GET /api/fractal/v2.1/admin/spx/validate` - Data validation
- `GET /api/fractal/v2.1/admin/spx/gaps` - Gap audit
- `GET /api/fractal/v2.1/admin/spx/cohorts` - Cohort breakdown

**Frontend:**
- `SpxAdminTab.js` - SPX Data Foundation UI
- Dynamic tab switching based on asset
- Cohort distribution visualization
- Data actions (Ingest, Generate Mock, Ensure Indexes)

**SPX Data Status:**
| Cohort | Records | Period |
|--------|---------|--------|
| V1950 | 10,435 | 1950-1989 |
| V1990 | 4,696 | 1990-2007 |
| V2008 | 3,131 | 2008-2019 |
| V2020 | 1,566 | 2020-2025 |
| **Total** | **19,828** | 1950-2025 |

---

## Current System Status

```
Fractal V2.1 — 3-Product Architecture

┌──────────────────────────────────────────┐
│ BTC Terminal        FINAL               │
│   API: /api/btc/v2.1/*                  │
│   Status: Production Ready               │
│   Data: 4,383+ candles (BTC)            │
├──────────────────────────────────────────┤
│ SPX Terminal        DATA_READY          │
│   API: /api/spx/v2.1/*                  │
│   Data: 19,828 candles (1950-2025)      │
│   Next: BLOCK B5 Fractal Core Clone     │
├──────────────────────────────────────────┤
│ Combined Terminal   BUILDING            │
│   API: /api/combined/v2.1/*             │
│   Depends on: SPX Terminal Complete     │
└──────────────────────────────────────────┘

AdminDashboard: Asset Selector integrated
SPX Admin: Data Foundation tab active
Scheduler: ENABLED (00:10 UTC daily)
```

---

## Prioritized Backlog

### P0 (Critical) ✅ DONE
- [x] BLOCK A: BTC Final Isolation
- [x] BLOCK B1: SPX Data Adapter (Stooq/Yahoo)
- [x] BLOCK B2: SPX Backfill Service (Resume-safe)
- [x] BLOCK B3: SPX Index Hardening + Validation
- [x] BLOCK B4: SPX Ingestion Service + Mock Generator

### P1 (High) - Next
- [ ] BLOCK B5: SPX Fractal Core Clone
  - Horizons 7d/14d/30d/90d/180d/365d
  - Primary match selector
  - Replay/Synthetic builder
  - Divergence engine
  - Phase engine
  - Volatility regime
  - Consensus74 + structuralLock

### P2 (Medium)
- [ ] BLOCK B6: SPX Memory Layer (snapshots/outcomes)
- [ ] BLOCK B7: SPX Intel Stack (timeline/alerts)
- [ ] BLOCK C1-C3: Combined Terminal

### P3 (Future)
- [ ] Real-time WebSocket for SPX
- [ ] Real SPX data integration (when APIs available)
- [ ] Cross-Asset Learning Layer

---

## Next Tasks

1. **BLOCK B5**: Clone BTC Fractal Core for SPX
   - Apply horizons/phases/consensus to SPX candles
   - Create `/api/spx/v2.1/terminal` full endpoint
   - Build SPX Terminal UI

2. **BLOCK B6**: SPX Memory Layer
   - spx_snapshots collection
   - Forward truth resolver
   - Attribution service

3. After SPX complete → BLOCK C for Combined Terminal

---

## Notes

- SPX data is currently MOCK generated due to Stooq/Yahoo API rate limits
- Mock data follows realistic historical patterns (based on actual SPX anchors)
- Real data can be ingested via admin when APIs are available
- All SPX code is isolated from BTC - no cross-contamination
