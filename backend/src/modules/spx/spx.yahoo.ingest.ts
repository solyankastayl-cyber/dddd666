/**
 * SPX TERMINAL — Yahoo CSV Ingestion
 * 
 * Imports SPX data from yfinance CSV file into MongoDB
 * with proper cohort segmentation.
 */

import { SpxCandleModel } from './spx.mongo.js';
import { pickSpxCohort } from './spx.cohorts.js';
import type { SpxCandle } from './spx.types.js';
import * as fs from 'fs';
import * as path from 'path';

// Default CSV path - updated to merged file with 2026 data
const DEFAULT_CSV_PATH = '/app/data/spx_1950_2026.csv';

interface YahooCsvRow {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  adjClose: number;
  volume: number;
}

/**
 * Parse Yahoo Finance CSV format
 * 
 * Format:
 * Price,Adj Close,Close,High,Low,Open,Volume
 * Ticker,^GSPC,^GSPC,^GSPC,^GSPC,^GSPC,^GSPC
 * Date,...
 */
export function parseYahooCsv(csvText: string): YahooCsvRow[] {
  const lines = csvText.trim().split(/\r?\n/);
  
  // Find the data start (skip multi-level header)
  let dataStartIdx = 0;
  for (let i = 0; i < lines.length; i++) {
    const firstCol = lines[i].split(',')[0]?.trim();
    // Data rows start with a date like "1950-01-03"
    if (/^\d{4}-\d{2}-\d{2}/.test(firstCol)) {
      dataStartIdx = i;
      break;
    }
  }

  const rows: YahooCsvRow[] = [];
  
  for (let i = dataStartIdx; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    
    const parts = line.split(',');
    const date = parts[0]?.trim();
    
    // Skip invalid dates
    if (!date || !/^\d{4}-\d{2}-\d{2}/.test(date)) continue;
    
    // Yahoo format: Date, Adj Close, Close, High, Low, Open, Volume
    const adjClose = parseFloat(parts[1]);
    const close = parseFloat(parts[2]);
    const high = parseFloat(parts[3]);
    const low = parseFloat(parts[4]);
    const open = parseFloat(parts[5]);
    const volume = parseInt(parts[6]) || 0;
    
    // Validate OHLC
    if (!Number.isFinite(open) || !Number.isFinite(high) || 
        !Number.isFinite(low) || !Number.isFinite(close)) {
      console.warn(`[Yahoo CSV] Invalid OHLC at ${date}, skipping`);
      continue;
    }
    
    if (open <= 0 || high <= 0 || low <= 0 || close <= 0) {
      console.warn(`[Yahoo CSV] Non-positive OHLC at ${date}, skipping`);
      continue;
    }
    
    if (low > high) {
      console.warn(`[Yahoo CSV] Low > High at ${date}, skipping`);
      continue;
    }
    
    rows.push({
      date,
      open,
      high,
      low,
      close,
      adjClose,
      volume,
    });
  }
  
  // Sort chronologically
  rows.sort((a, b) => a.date.localeCompare(b.date));
  
  return rows;
}

/**
 * Convert Yahoo CSV rows to SpxCandle documents
 */
function toSpxCandles(rows: YahooCsvRow[]): SpxCandle[] {
  return rows.map(r => {
    const [y, m, d] = r.date.split('-').map(Number);
    const ts = Date.UTC(y, m - 1, d, 0, 0, 0, 0);
    
    return {
      ts,
      date: r.date,
      open: r.open,
      high: r.high,
      low: r.low,
      close: r.close,
      volume: r.volume || null,
      symbol: 'SPX' as const,
      source: 'STOOQ' as const, // Mark as real data source
      cohort: pickSpxCohort(r.date),
    };
  });
}

/**
 * Ingest SPX data from Yahoo CSV file
 */
export async function ingestFromYahooCsv(csvPath: string = DEFAULT_CSV_PATH) {
  console.log(`[SPX Ingest] Reading CSV from: ${csvPath}`);
  
  // Read CSV file
  if (!fs.existsSync(csvPath)) {
    throw new Error(`CSV file not found: ${csvPath}`);
  }
  
  const csvText = fs.readFileSync(csvPath, 'utf-8');
  console.log(`[SPX Ingest] CSV size: ${(csvText.length / 1024).toFixed(1)} KB`);
  
  // Parse CSV
  const rows = parseYahooCsv(csvText);
  console.log(`[SPX Ingest] Parsed ${rows.length} valid rows`);
  
  if (rows.length === 0) {
    throw new Error('No valid rows found in CSV');
  }
  
  // Convert to candles
  const candles = toSpxCandles(rows);
  
  // Cohort summary before insert
  const cohortCounts: Record<string, number> = {};
  for (const c of candles) {
    cohortCounts[c.cohort] = (cohortCounts[c.cohort] || 0) + 1;
  }
  console.log(`[SPX Ingest] Cohort distribution:`, cohortCounts);
  
  // Bulk upsert
  console.log(`[SPX Ingest] Upserting ${candles.length} candles...`);
  
  const ops = candles.map(c => ({
    updateOne: {
      filter: { ts: c.ts },
      update: { $set: c },
      upsert: true,
    },
  }));
  
  const result = await SpxCandleModel.bulkWrite(ops, { ordered: false });
  
  const written = result.upsertedCount ?? 0;
  const updated = result.modifiedCount ?? 0;
  const matched = result.matchedCount ?? 0;
  
  console.log(`[SPX Ingest] Complete!`);
  console.log(`  - Upserted: ${written}`);
  console.log(`  - Updated: ${updated}`);
  console.log(`  - Already existed: ${matched - updated}`);
  
  return {
    ok: true,
    source: 'YAHOO_CSV',
    csvPath,
    parsed: rows.length,
    upserted: written,
    updated,
    matched,
    cohorts: cohortCounts,
    range: {
      from: candles[0]?.date,
      to: candles[candles.length - 1]?.date,
    },
  };
}

/**
 * Replace all SPX data with Yahoo CSV
 */
export async function replaceWithYahooCsv(csvPath: string = DEFAULT_CSV_PATH) {
  console.log(`[SPX Ingest] Clearing existing SPX data...`);
  
  const deleteResult = await SpxCandleModel.deleteMany({});
  console.log(`[SPX Ingest] Deleted ${deleteResult.deletedCount} existing candles`);
  
  return await ingestFromYahooCsv(csvPath);
}
