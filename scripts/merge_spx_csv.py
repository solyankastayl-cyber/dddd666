#!/usr/bin/env python3
"""
SPX CSV Merge Script

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

# Read base CSV
print(f"\nReading base: {base_path}")
base = pd.read_csv(base_path)
print(f"  Base columns: {base.columns.tolist()}")
print(f"  Base rows: {len(base)}")

# Normalize column names
base.columns = [str(c).strip().lower() for c in base.columns]

# Find date column (could be 'date' or 'price')
date_col = None
for col in base.columns:
    if 'date' in col or col == 'price':
        date_col = col
        break

if date_col and date_col != 'date':
    base = base.rename(columns={date_col: 'date'})

print(f"  Base date range: {base['date'].min()} → {base['date'].max()}")

# Read patch CSV  
print(f"\nReading patch: {patch_path}")
patch = pd.read_csv(patch_path)
patch.columns = [str(c).strip().lower() for c in patch.columns]
print(f"  Patch rows: {len(patch)}")
print(f"  Patch date range: {patch['date'].min()} → {patch['date'].max()}")

# Ensure date is string in both
base['date'] = pd.to_datetime(base['date']).dt.strftime('%Y-%m-%d')
patch['date'] = pd.to_datetime(patch['date']).dt.strftime('%Y-%m-%d')

# Align columns (patch may have more columns like adj_close)
# Keep only columns that exist in patch for the merged file
common_cols = [c for c in patch.columns if c in base.columns or c == 'adj_close']

# Make sure base has all needed columns (fill with NaN if missing)
for col in common_cols:
    if col not in base.columns:
        base[col] = None

# Select only common columns in same order
final_cols = ['date', 'open', 'high', 'low', 'close']
if 'adj_close' in patch.columns:
    final_cols.append('adj_close')
if 'volume' in patch.columns:
    final_cols.append('volume')

# Filter to available columns
final_cols = [c for c in final_cols if c in base.columns or c in patch.columns]

base = base[[c for c in final_cols if c in base.columns]]
patch = patch[[c for c in final_cols if c in patch.columns]]

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

# Validate - check for gaps > 5 days
merged['date_dt'] = pd.to_datetime(merged['date'])
gaps = merged['date_dt'].diff().dt.days
large_gaps = gaps[gaps > 5]
if len(large_gaps) > 0:
    print(f"\n⚠️  Found {len(large_gaps)} gaps > 5 days")
    print(f"   Largest gap: {gaps.max()} days")
else:
    print(f"\n✅ No large gaps found")

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
