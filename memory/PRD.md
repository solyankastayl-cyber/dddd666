# Fractal V2.1 — PRD (Product Requirements Document)

**Last Updated:** 2026-02-20  
**Status:** BLOCK 82-83 Complete

---

## Original Problem Statement

Клонировать репозиторий https://github.com/solyankastayl-cyber/ddd5555, поднять фронт, бэк, админку и работать только с областью Fractal. Реализовать BLOCK 82-83.

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

**Backend:**
- `intel-timeline/intel-timeline.model.ts` — MongoDB schema for `intel_timeline_daily` collection
- `intel-timeline/intel-timeline.service.ts` — Timeline read service with stats computation
- `intel-timeline/intel-timeline.writer.ts` — Idempotent upsert writer
- `intel-timeline/intel-timeline.routes.ts` — API endpoints

**API Endpoints:**
- `GET /api/fractal/v2.1/admin/intel/timeline` — Get timeline with stats
- `GET /api/fractal/v2.1/admin/intel/latest` — Get latest snapshot
- `GET /api/fractal/v2.1/admin/intel/counts` — Get counts by source
- `POST /api/fractal/v2.1/admin/intel/snapshot` — Manual snapshot write
- `POST /api/fractal/v2.1/admin/intel/backfill` — Backfill V2014/V2020

**Frontend:**
- `IntelTab.jsx` — Admin tab with:
  - Phase Strength Timeline (SVG graph with grade colors A-F)
  - Dominance History (color-coded bar: Structure/Tactical/Timing)
  - KPI Summary (Lock Days, Dominance %, Switch Count, Avg Score, Trend)
  - Backfill Panel

---

### BLOCK 83 — Intel Alerts (Event-based Alerts)
**Date:** 2026-02-20

**Backend:**
- `intel-alerts/intel-alerts.model.ts` — MongoDB schema for `intel_event_alerts`
- `intel-alerts/intel-alerts.detector.ts` — State-change event detector
- `intel-alerts/intel-alerts.service.ts` — Telegram sender + rate limiting
- `intel-alerts/intel-alerts.routes.ts` — API endpoints

**Events Detected:**
- `LOCK_ENTER` — Structural lock entered
- `LOCK_EXIT` — Structural lock exited  
- `DOMINANCE_SHIFT` — Tier dominance changed
- `PHASE_DOWNGRADE` — Phase grade dropped ≥2 levels

**Rate Limiting:**
- Max 3 non-critical alerts per 24h
- CRITICAL alerts bypass limit
- Only sent when source=LIVE and liveSamples≥15

**Frontend:**
- Intelligence Event Alerts table in IntelTab

---

### Daily Run Pipeline Integration
**Steps:**
1. SNAPSHOT_WRITE
2. OUTCOME_RESOLVE
3. EQUITY_REBUILD
4. ALERTS
5. AUDIT_LOG
6. MEMORY_SNAPSHOTS
7. **INTEL_TIMELINE_WRITE** ← NEW (BLOCK 82)
8. **INTEL_EVENT_ALERTS** ← NEW (BLOCK 83)

---

## Current Data Status

| Source | Records | Date Range |
|--------|---------|------------|
| LIVE | 1 | 2026-02-20 |
| V2020 | 2192 | 2020-01-01 to 2025-12-31 |
| V2014 | 2191 | 2014-01-01 to 2019-12-31 |

---

## Telegram Configuration

**Encrypted Token:** `/backend/telegram_encrypted.txt`  
**Decryption Key:** `OEcd5DNtFaxDjYEF9aqk4hskCyUYsDiYZGYh0XfPyIw=`

Environment Variables:
```
TG_BOT_TOKEN=<encrypted>
TG_ADMIN_CHAT_ID=@F_FOMO_bot
```

---

## Prioritized Backlog

### P0 (Critical)
- [x] BLOCK 82: Intel Timeline
- [x] BLOCK 83: Intel Alerts Engine
- [x] Daily run pipeline integration

### P1 (High)
- [ ] Enable Scheduler (00:10 UTC daily)
- [ ] Telegram alerts testing with real credentials

### P2 (Medium)
- [ ] BLOCK 84: Dominance Event Markers in Timeline
- [ ] BLOCK 85: LIVE Confidence Meter
- [ ] Historical query for V2014/V2020 (custom date range)

### P3 (Future)
- [ ] Multi-Asset (ETH) support
- [ ] Adaptive Learning v2
- [ ] Phase Strength/Dominance Timeline export

---

## Next Tasks

1. **Enable Scheduler** — Admin → Ops → Enable scheduler
2. **Test Telegram** — Verify alerts reach @F_FOMO_bot
3. **Accumulate LIVE data** — After 15 days, alerts will activate
4. **BLOCK 84** — Visual event markers on timeline

---

## User Personas

1. **Institutional Analyst** — Monitors phase strength, dominance shifts, governance locks
2. **Risk Manager** — Receives Telegram alerts for critical events
3. **Quant Developer** — Uses API for backtesting and analysis
