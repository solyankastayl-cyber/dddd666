#!/usr/bin/env python3
"""
SPX 2026 Patch Download Script (Fixed)

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

print(f"Raw shape: {df.shape}")

# Handle MultiIndex columns from yfinance
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

# Reset index to get Date as column
df = df.reset_index()

# Standardize column names
col_map = {
    'Date': 'date',
    'Open': 'open', 
    'High': 'high',
    'Low': 'low',
    'Close': 'close',
    'Adj Close': 'adj_close',
    'Volume': 'volume'
}
df = df.rename(columns=col_map)

# Keep only what we need (in correct order)
final_cols = ['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
df = df[[c for c in final_cols if c in df.columns]]

# Ensure date format
df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

print(f"Final columns: {df.columns.tolist()}")
print(f"Shape: {df.shape}")

df.to_csv(out_path, index=False)
print(f"\n✅ Saved patch: {out_path}")
print(f"   Rows: {len(df)}")
print(f"   Range: {df['date'].min()} → {df['date'].max()}")
print(f"\nFirst 3 rows:")
print(df.head(3).to_string())
print(f"\nLast 3 rows:")
print(df.tail(3).to_string())
