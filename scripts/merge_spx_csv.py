#!/usr/bin/env python3
"""
SPX CSV Merge Script (Fixed for yfinance multi-header format)

Merges base SPX data (1950-2025) with 2026 patch.
"""

import pandas as pd
import os

base_path = "/app/data/spx_1950_2025.csv"
patch_path = "/app/data/spx_patch_2026.csv"
out_path = "/app/data/spx_1950_2026.csv"

print("=" * 60)
print("SPX CSV Merge")
print("=" * 60)

# Read base CSV - skip first 2 header rows, use row 3 (dates start at row 4)
print(f"\nReading base: {base_path}")
base = pd.read_csv(base_path, skiprows=2)  # Skip "Price,Adj Close..." and "Ticker,^GSPC..."
print(f"  Base columns after skip: {base.columns.tolist()}")

# First column should be dates
base.columns = ['date', 'adj_close', 'close', 'high', 'low', 'open', 'volume']

# Remove any rows where date is not a valid date
base = base[base['date'].str.match(r'^\d{4}-\d{2}-\d{2}', na=False)]
print(f"  Base rows (valid dates): {len(base)}")
print(f"  Base date range: {base['date'].min()} → {base['date'].max()}")

# Read patch CSV (already clean format)
print(f"\nReading patch: {patch_path}")
patch = pd.read_csv(patch_path)
print(f"  Patch rows: {len(patch)}")
print(f"  Patch date range: {patch['date'].min()} → {patch['date'].max()}")

# Ensure columns match
final_cols = ['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']

# Reorder base columns
base = base[final_cols]
patch = patch[final_cols]

# Convert numeric columns
for col in ['open', 'high', 'low', 'close', 'adj_close', 'volume']:
    base[col] = pd.to_numeric(base[col], errors='coerce')
    patch[col] = pd.to_numeric(patch[col], errors='coerce')

# Merge
print(f"\nMerging...")
merged = pd.concat([base, patch], ignore_index=True)

# Remove duplicates, keep last (patch wins)
merged = merged.drop_duplicates(subset=['date'], keep='last')

# Sort by date
merged = merged.sort_values('date')
merged = merged.reset_index(drop=True)

print(f"  Merged rows: {len(merged)}")
print(f"  Merged date range: {merged['date'].min()} → {merged['date'].max()}")

# Validate - check for gaps > 7 days
merged['date_dt'] = pd.to_datetime(merged['date'])
gaps = merged['date_dt'].diff().dt.days
large_gaps = gaps[gaps > 7]
if len(large_gaps) > 0:
    print(f"\n⚠️  Found {len(large_gaps)} gaps > 7 days (largest: {gaps.max()} days)")
    # Show largest gaps
    for idx in large_gaps.nlargest(3).index:
        prev_date = merged.loc[idx-1, 'date'] if idx > 0 else 'N/A'
        curr_date = merged.loc[idx, 'date']
        print(f"   Gap: {prev_date} → {curr_date} ({int(gaps.loc[idx])} days)")
else:
    print(f"\n✅ No gaps > 7 days found")

# Check transition from 2025 to 2026
transition = merged[(merged['date'] >= '2025-12-25') & (merged['date'] <= '2026-01-10')]
print(f"\n📊 2025→2026 transition:")
print(transition[['date', 'close']].to_string(index=False))

# Save
merged = merged.drop(columns=['date_dt'])
merged.to_csv(out_path, index=False)

file_size = os.path.getsize(out_path) / (1024 * 1024)
print(f"\n✅ Saved: {out_path}")
print(f"   Size: {file_size:.2f} MB")
print(f"   Final rows: {len(merged)}")

# Show tail
print(f"\nLast 5 rows:")
print(merged.tail(5).to_string())
