#!/usr/bin/env python3
"""
SPX Historical Data Download Script

Downloads S&P 500 (^GSPC) daily OHLCV data from Yahoo Finance
using yfinance library.

Output: spx_1950_2025.csv
"""

import yfinance as yf
import pandas as pd
import sys

print("=" * 60)
print("SPX Historical Data Download")
print("=" * 60)

print("\nDownloading S&P 500 data from Yahoo Finance...")
print("Symbol: ^GSPC")
print("Period: 1950-01-01 to 2026-01-01")
print("Interval: 1d (daily)")
print()

try:
    spx = yf.download(
        "^GSPC",
        start="1950-01-01",
        end="2026-01-01",
        interval="1d",
        auto_adjust=False,  # Raw OHLC without adjustment
        progress=True
    )

    if spx.empty:
        print("\n❌ ERROR: No data downloaded!")
        sys.exit(1)

    # Data info
    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"First date: {spx.index.min()}")
    print(f"Last date:  {spx.index.max()}")
    print(f"Total rows: {len(spx)}")
    print()

    # Check for issues
    issues = []
    
    # Check NaN
    nan_count = spx[['Open', 'High', 'Low', 'Close']].isna().sum().sum()
    if nan_count > 0:
        issues.append(f"Found {nan_count} NaN values in OHLC")
    
    # Check zeros
    zero_count = (spx[['Open', 'High', 'Low', 'Close']] == 0).sum().sum()
    if zero_count > 0:
        issues.append(f"Found {zero_count} zero values in OHLC")
    
    # Check negative
    neg_count = (spx[['Open', 'High', 'Low', 'Close']] < 0).sum().sum()
    if neg_count > 0:
        issues.append(f"Found {neg_count} negative values in OHLC")

    if issues:
        print("⚠️  WARNINGS:")
        for issue in issues:
            print(f"   - {issue}")
        print()
    else:
        print("✅ Data quality: OK (no NaN, zeros, or negative values)")
        print()

    # Show sample
    print("Sample data (first 5 rows):")
    print(spx.head())
    print()
    print("Sample data (last 5 rows):")
    print(spx.tail())
    print()

    # Save to CSV
    file_name = "/app/data/spx_1950_2025.csv"
    
    # Ensure data directory exists
    import os
    os.makedirs("/app/data", exist_ok=True)
    
    spx.to_csv(file_name)
    
    # File size
    file_size = os.path.getsize(file_name) / (1024 * 1024)
    
    print("=" * 60)
    print(f"✅ Saved to: {file_name}")
    print(f"   File size: {file_size:.2f} MB")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    sys.exit(1)
