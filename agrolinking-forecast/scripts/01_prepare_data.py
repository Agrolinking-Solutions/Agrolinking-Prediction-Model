import pandas as pd
import numpy as np
import os
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.expanduser("~/Agrolinking-Prediction-Model/agrolinking-forecast")
RAW_PATH   = os.path.join(BASE_DIR, "data/raw/agricom_cleaned.csv")
MASTER_PATH = os.path.join(BASE_DIR, "data/processed/agricom_master.csv")

# ── Load raw data ──────────────────────────────────────────────────────────
print("📂 Loading raw data...")
df = pd.read_csv(RAW_PATH)
print(f"   Loaded {len(df)} rows, {df['commodity'].nunique()} commodities")

# ── Clean & standardize ────────────────────────────────────────────────────
print("🧹 Cleaning data...")

# Parse dates
df['week_start_date'] = pd.to_datetime(df['week_start_date'])

# Ensure price is numeric
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['fx_rate'] = pd.to_numeric(df['fx_rate'], errors='coerce')

# Drop rows with missing price or date
before = len(df)
df = df.dropna(subset=['price', 'week_start_date'])
print(f"   Dropped {before - len(df)} rows with missing price/date")

# Remove duplicates (same commodity + date)
before = len(df)
df = df.drop_duplicates(subset=['commodity', 'week_start_date'])
print(f"   Removed {before - len(df)} duplicate rows")

# Remove extreme outliers per commodity (beyond 3 std deviations)
clean_dfs = []
for commodity, group in df.groupby('commodity'):
    mean = group['price'].mean()
    std  = group['price'].std()
    filtered = group[
        (group['price'] >= mean - 3 * std) &
        (group['price'] <= mean + 3 * std)
    ]
    removed = len(group) - len(filtered)
    if removed > 0:
        print(f"   [{commodity}] Removed {removed} outlier(s)")
    clean_dfs.append(filtered)

df = pd.concat(clean_dfs).reset_index(drop=True)

# Add a column to track whether row is historical or forecasted
if 'record_type' not in df.columns:
    df['record_type'] = 'historical'

# Sort by commodity and date
df = df.sort_values(['commodity', 'week_start_date']).reset_index(drop=True)

print(f"✅ Clean dataset: {len(df)} rows")
print(f"   Commodities  : {sorted(df['commodity'].unique().tolist())}")
print(f"   Date range   : {df['week_start_date'].min().date()} → {df['week_start_date'].max().date()}")

# ── Create master dataset (ONLY if it doesn't exist yet) ──────────────────
if not os.path.exists(MASTER_PATH):
    df.to_csv(MASTER_PATH, index=False)
    print(f"\n🗄️  Master dataset created for the first time → {MASTER_PATH}")
else:
    print(f"\n🗄️  Master dataset already exists — skipping creation → {MASTER_PATH}")

print("\n✅ Phase 1 complete. Ready for model training.")
