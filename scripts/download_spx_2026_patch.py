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

print(f"Raw shape: {df.shape}")
print(f"Raw columns: {df.columns.tolist()}")

# Handle MultiIndex columns from yfinance
if isinstance(df.columns, pd.MultiIndex):
    # Flatten: take first level
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    print(f"Flattened columns: {df.columns.tolist()}")

# Reset index to get Date as column
df = df.reset_index()
print(f"After reset_index columns: {df.columns.tolist()}")

# Normalize column names
df.columns = [str(c).strip().replace(" ", "_").lower() for c in df.columns]
print(f"Normalized columns: {df.columns.tolist()}")

# Keep only needed cols
keep_cols = []
for target in ["date", "open", "high", "low", "close", "adj_close", "volume"]:
    for col in df.columns:
        if target in col.lower():
            keep_cols.append(col)
            break

print(f"Keeping columns: {keep_cols}")
df = df[keep_cols]

# Rename to standard names
rename_map = {}
for col in df.columns:
    if 'date' in col.lower():
        rename_map[col] = 'date'
    elif 'open' in col.lower():
        rename_map[col] = 'open'
    elif 'high' in col.lower():
        rename_map[col] = 'high'
    elif 'low' in col.lower():
        rename_map[col] = 'low'
    elif 'adj' in col.lower():
        rename_map[col] = 'adj_close'
    elif 'close' in col.lower():
        rename_map[col] = 'close'
    elif 'volume' in col.lower():
        rename_map[col] = 'volume'

df = df.rename(columns=rename_map)
print(f"Final columns: {df.columns.tolist()}")

# Ensure date format
df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

df.to_csv(out_path, index=False)
print(f"\n✅ Saved patch: {out_path}")
print(f"   Rows: {len(df)}")
print(f"   Range: {df['date'].min()} → {df['date'].max()}")
print(f"\nFirst 3 rows:")
print(df.head(3))
