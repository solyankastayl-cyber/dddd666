# Fractal V2.1 — PRD (Product Requirements Document)

**Last Updated:** 2026-02-21  
**Status:** BLOCK A Complete, 3-Product Architecture Implemented

---

## Original Problem Statement

Клонировать репозиторий https://github.com/solyankastayl-cyber/dddddd, поднять фронт, бэк, админку и работать только с областью Fractal. Реализовать BLOCK A - BTC Final isolation и логику обновления по фронту с Asset Selector.

---

## Architecture Overview

### Tech Stack
- **Backend:** Node.js + TypeScript + Fastify + MongoDB (Mongoose)
- **Frontend:** React + TailwindCSS
- **Database:** MongoDB (fractal_dev)
- **Proxy:** Python FastAPI (uvicorn) → TypeScript backend on port 8002

### 3-Product Architecture (BLOCK A/B/C)

| Product | Status | API Namespace | UI Route |
|---------|--------|---------------|----------|
| BTC Terminal | FINAL | `/api/btc/v2.1/*` | `/btc` |
| SPX Terminal | BUILDING | `/api/spx/v2.1/*` | `/spx` |
| Combined Terminal | BUILDING | `/api/combined/v2.1/*` | `/combined` |

### Module Isolation Rules
- `modules/btc/**` → imports only `core/**`
- `modules/spx/**` → imports only `core/**`
- `modules/combined/**` → can read from btc/spx (read-only)

---

## What's Been Implemented

### Session 2026-02-21: BLOCK A — BTC Final Isolation

**Backend Changes:**
- Added BTC, SPX, Combined route registration to `app.fractal.ts`
- BTC routes proxy to Fractal core with `symbol=BTC` forced
- SPX/Combined return status placeholders (BUILDING)

**Frontend Changes:**
- Created `AssetSelector.jsx` component with 3 product buttons
- Integrated AssetSelector into AdminDashboard header
- Header now shows dynamic product name with FINAL/BUILDING badge
- BTC button active (orange), SPX/COMBINED disabled with "(soon)"
- Dashboard fetches asset-specific API based on selection

**API Endpoints Working:**
- `GET /api/btc/v2.1/info` → BTC Terminal info (FINAL)
- `GET /api/spx/v2.1/status` → SPX build progress
- `GET /api/combined/v2.1/info` → Combined Terminal config
- All Fractal admin APIs under `/api/fractal/v2.1/*`

### Previous Implementation (BLOCK 82-85)
- Intel Timeline (Phase Strength + Dominance History)
- Intel Alerts Engine (Event-based Alerts)
- Visual Event Markers
- Model Health Composite Score
- Daily Run Pipeline + Scheduler

---

## Current Data Status

| Source | Records | Description |
|--------|---------|-------------|
| LIVE | 1+ | Today's snapshots |
| V2020 | 2192 | 2020-2025 backfill |
| V2014 | 2191 | 2014-2019 backfill |

---

## Prioritized Backlog

### P0 (Critical) ✅
- [x] BLOCK A1: BTC API namespace `/api/btc/v2.1/*`
- [x] BLOCK A2: Storage isolation config (btc_* collections)
- [x] BLOCK A3: Code isolation (import boundaries)
- [x] BLOCK A4: UI asset selector in AdminDashboard

### P1 (High) - Next
- [ ] BLOCK B1: SPX data adapter (fetch SPX index candles)
- [ ] BLOCK B2: SPX backfill cohorts (V2014/V2020 equivalent)
- [ ] BLOCK B3: SPX Terminal full pipeline (horizons, consensus, etc.)
- [ ] BLOCK B4: SPX admin dashboard integration

### P2 (Medium)
- [ ] BLOCK C1: Combined Terminal API (aggregates BTC + SPX)
- [ ] BLOCK C2: Combined Decision Kernel
- [ ] BLOCK C3: Integration layers L1-L4
- [ ] BLOCK C4: SPX influence toggle (ON/OFF)

### P3 (Future)
- [ ] Real-time WebSocket updates
- [ ] Telegram alerts with live credentials
- [ ] Governance APPLY when LIVE samples ≥30

---

## Next Tasks

1. **BLOCK B1**: Implement SPX data adapter to fetch S&P 500 daily candles
2. **BLOCK B2**: Create SPX backfill service for historical data (2014-2025)
3. **BLOCK B3**: Apply full Fractal pipeline to SPX (horizons, phases, consensus)
4. After SPX complete → BLOCK C for Combined Terminal

---

## System Status Summary

```
Fractal V2.1 — 3-Product Architecture

┌──────────────────────────────────────────┐
│ BTC Terminal        FINAL               │
│   API: /api/btc/v2.1/*                  │
│   Status: Production Ready               │
├──────────────────────────────────────────┤
│ SPX Terminal        BUILDING            │
│   API: /api/spx/v2.1/*                  │
│   Next: Data Adapter + Backfill         │
├──────────────────────────────────────────┤
│ Combined Terminal   BUILDING            │
│   API: /api/combined/v2.1/*             │
│   Depends on: SPX Terminal              │
└──────────────────────────────────────────┘

AdminDashboard: AssetSelector integrated
Scheduler: ENABLED (00:10 UTC daily)
```
