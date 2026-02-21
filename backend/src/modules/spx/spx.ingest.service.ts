/**
 * SPX TERMINAL — Ingestion Service
 * 
 * BLOCK B4 — Idempotent upsert ingestion from Stooq
 */

import { SpxCandleModel, SpxIngestionLogModel } from './spx.mongo.js';
import { fetchStooqCsv, parseStooqDailyCsv } from './spx.stooq.client.js';
import { toCanonicalSpxCandles } from './spx.normalizer.js';
import type { SpxIngestResult } from './spx.types.js';
import { randomUUID } from 'crypto';

/**
 * Ingest SPX candles from Stooq (idempotent)
 */
export async function ingestSpxFromStooq(): Promise<SpxIngestResult & { runId: string }> {
  const runId = randomUUID();
  const startTime = Date.now();
  const errors: string[] = [];

  try {
    // Fetch CSV
    const csv = await fetchStooqCsv();
    const rows = parseStooqDailyCsv(csv);
    const candles = toCanonicalSpxCandles(rows);

    if (candles.length === 0) {
      const result = {
        runId,
        fetchedRows: rows.length,
        canonicalRows: 0,
        written: 0,
        skipped: 0,
      };

      // Log the run
      await SpxIngestionLogModel.create({
        runId,
        source: 'STOOQ',
        status: 'success',
        fetchedRows: rows.length,
        insertedRows: 0,
        skippedRows: 0,
        errors: [],
        durationMs: Date.now() - startTime,
      });

      return result;
    }

    // Bulk upsert by ts (unique)
    const ops = candles.map((c) => ({
      updateOne: {
        filter: { ts: c.ts },
        update: { $setOnInsert: c },
        upsert: true,
      },
    }));

    const bulk = await SpxCandleModel.bulkWrite(ops, { ordered: false });
    const written = bulk.upsertedCount ?? 0;
    const skipped = candles.length - written;

    const from = candles[0]?.date;
    const to = candles[candles.length - 1]?.date;

    // Log the run
    await SpxIngestionLogModel.create({
      runId,
      source: 'STOOQ',
      status: 'success',
      fetchedRows: rows.length,
      insertedRows: written,
      skippedRows: skipped,
      errors,
      rangeFrom: from,
      rangeTo: to,
      durationMs: Date.now() - startTime,
    });

    return {
      runId,
      fetchedRows: rows.length,
      canonicalRows: candles.length,
      written,
      skipped,
      from,
      to,
    };
  } catch (e: any) {
    errors.push(e.message || String(e));

    // Log the failure
    await SpxIngestionLogModel.create({
      runId,
      source: 'STOOQ',
      status: 'failed',
      fetchedRows: 0,
      insertedRows: 0,
      skippedRows: 0,
      errors,
      durationMs: Date.now() - startTime,
    });

    throw e;
  }
}

/**
 * Get recent ingestion logs
 */
export async function getIngestionLogs(limit = 10) {
  return await SpxIngestionLogModel
    .find({})
    .sort({ createdAt: -1 })
    .limit(limit)
    .lean();
}
