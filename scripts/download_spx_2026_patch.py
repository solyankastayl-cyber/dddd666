#!/usr/bin/env python3
"""
SPX 2026 Patch Download Script

Downloads S&P 500 (^GSPC) daily data for 2026 to fill the gap.
"""

import pandas as pd
import yfinance as yf
from datetime import date
import os

START = "2026-01-01"
END = date.today().isoformat()
TICKER = "^GSPC"

out_path = "/app/data/spx_patch_2026.csv"

print(f"Downloading {TICKER} from {START} to {END}...")

df = yf.download(
    TICKER,
    start=START,
    end=END,
    interval="1d",
    auto_adjust=False,
    progress=True,
    threads=False,
)

if df is None or df.empty:
    raise SystemExit("No data returned. Try again later or use fallback source.")

# Normalize columns
df = df.reset_index()
df.columns = [str(c).strip().replace(" ", "_").lower() for c in df.columns]

print(f"\nColumns after normalization: {list(df.columns)}")

# Keep only needed cols if present
cols = [c for c in ["date", "open", "high", "low", "close", "adj_close", "volume"] if c in df.columns]
df = df[cols]

df.to_csv(out_path, index=False)
print(f"\n✅ Saved patch: {out_path}")
print(f"   Rows: {len(df)}")
print(f"   Range: {df['date'].min()} → {df['date'].max()}")
