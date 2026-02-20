# Fractal V2.1 — PRD (Product Requirements Document)

**Last Updated:** 2026-02-20  
**Status:** BLOCK 82-85 Complete, Scheduler ENABLED

---

## Original Problem Statement

Клонировать репозиторий https://github.com/solyankastayl-cyber/ddd5555, поднять фронт, бэк, админку и работать только с областью Fractal. Реализовать BLOCK 82-85.

---

## Architecture Overview

### Tech Stack
- **Backend:** Node.js + TypeScript + Fastify + MongoDB (Mongoose)
- **Frontend:** React + TailwindCSS
- **Database:** MongoDB (fractal_db)

### Core Modules
- `/backend/src/modules/fractal/` — Main Fractal module
- `/frontend/src/components/fractal/admin/` — Admin Dashboard

---

## What's Been Implemented

### BLOCK 82 — Intel Timeline (Phase Strength + Dominance History)
**Date:** 2026-02-20

- MongoDB collection `intel_timeline_daily` with phase/dominance snapshots
- API: timeline, latest, counts, snapshot, backfill
- Frontend: Phase Strength graph, Dominance History bar, KPI Summary

### BLOCK 83 — Intel Alerts Engine (Event-based Alerts)
**Date:** 2026-02-20

- Event detection: LOCK_ENTER, LOCK_EXIT, DOMINANCE_SHIFT, PHASE_DOWNGRADE
- Telegram integration with rate limiting (3/24h, CRITICAL bypass)
- Frontend: Intelligence Event Alerts table

### BLOCK 84 — Visual Event Markers
**Date:** 2026-02-20

- Event markers (🔒🔓▲▼) on Phase Strength Timeline
- Event markers (▲●) on Dominance History bar
- Hover tooltips for event details

### BLOCK 85 — Model Health Composite Score
**Date:** 2026-02-20

- Composite score (0-100) from 5 components:
  - Performance (LIVE vs Bootstrap): 30%
  - Drift Penalty: 20%
  - Phase Score: 20%
  - Divergence Score: 15%
  - Stability Score: 15%
- Bands: STRONG (≥80), STABLE (≥65), MODERATE (≥50), WEAK (<50)
- API: `/api/fractal/v2.1/admin/model-health`
- Frontend: Model Health Badge in Intel Tab header

### Daily Run Pipeline
**Steps:**
1. SNAPSHOT_WRITE
2. OUTCOME_RESOLVE
3. EQUITY_REBUILD
4. ALERTS
5. AUDIT_LOG
6. MEMORY_SNAPSHOTS
7. INTEL_TIMELINE_WRITE (BLOCK 82)
8. INTEL_EVENT_ALERTS (BLOCK 83)

### Scheduler
- **Status:** ENABLED
- **Schedule:** 00:10 UTC daily
- **Next Run:** 2026-02-21 00:10 UTC

---

## Current Data Status

| Source | Records | Description |
|--------|---------|-------------|
| LIVE | 1 | Today's snapshot |
| V2020 | 2192 | 2020-2025 backfill |
| V2014 | 2191 | 2014-2019 backfill |

### Current Model Health
- **Score:** 77%
- **Band:** STABLE
- **Components:** Perf=96, Drift=80, Phase=50, Div=50, Stability=100

---

## Prioritized Backlog

### P0 (Critical) ✅
- [x] BLOCK 82: Intel Timeline
- [x] BLOCK 83: Intel Alerts Engine
- [x] BLOCK 84: Visual Event Markers
- [x] BLOCK 85: Model Health Composite Score
- [x] Scheduler enabled

### P1 (High)
- [ ] Telegram alerts testing with real credentials
- [ ] Accumulate LIVE samples (≥15 for alerts, ≥30 for governance)

### P2 (Medium)
- [ ] BLOCK 86: Multi-Asset Expansion (ETH)
- [ ] BLOCK 87: Adaptive Weight Learning v2
- [ ] Historical query for V2014/V2020 (custom date range)

### P3 (Future)
- [ ] WebSocket real-time updates
- [ ] Phase Strength/Dominance Timeline export
- [ ] Dashboard customization

---

## Next Tasks

1. **Monitor LIVE accumulation** — Wait 7-15 days for alerts activation
2. **Test Telegram** — Verify alerts reach @F_FOMO_bot when samples ≥15
3. **Governance unlock** — After 30 LIVE days, APPLY becomes available

---

## System Status Summary

```
Fractal V2.1 — Institutional Panel

┌─────────────────────────────────────┐
│ Model Health: 77% STABLE            │
│ Phase: NEUTRAL (C) → Trend: FLAT    │
│ Dominance: STRUCTURE (100%)         │
│ Lock: OFF | Conflict: LOW           │
│ Drift: WATCH | Confidence: LOW      │
│ LIVE Samples: 1 (need ≥15 for alerts)│
│ Scheduler: ENABLED (00:10 UTC)      │
└─────────────────────────────────────┘
```
