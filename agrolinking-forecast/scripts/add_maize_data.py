import pandas as pd
import numpy as np
import os
from datetime import datetime

BASE_DIR    = os.path.expanduser("~/Agrolinking-Prediction-Model/agrolinking-forecast")
MASTER_PATH = os.path.join(BASE_DIR, "data/processed/agricom_master.csv")
WFP_PATH    = os.path.join(BASE_DIR, "data/raw/wfp_food_prices_nga.csv")

print("=" * 55)
print("  🌽 MAIZE DATA IMPORT — WFP Nigeria Food Prices")
print("=" * 55)

wfp = pd.read_csv(WFP_PATH)
wfp['date'] = pd.to_datetime(wfp['date'])

# ── Target commodities ─────────────────────────────────────────────────────
TARGET = ['Maize (white)', 'Maize (yellow)']
maize  = wfp[wfp['commodity'].isin(TARGET)].copy()
print(f"\n📦 Raw maize rows loaded: {len(maize)}")

# ── Unit conversion → NGN/MT ───────────────────────────────────────────────
# All variants: divide price by unit_kg, then × 1000
def to_per_mt(row):
    p = float(row['price'])
    u = str(row['unit']).strip()
    if u == 'KG':     return p * 1000
    if u == '100 KG': return (p / 100) * 1000
    if u == '50 KG':  return (p / 50)  * 1000
    return None

maize['price_per_mt'] = maize.apply(to_per_mt, axis=1)
maize = maize.dropna(subset=['price_per_mt'])
print(f"💱 Unit conversion applied (KG / 100 KG / 50 KG → NGN/MT)")

# ── Resample to weekly national median ────────────────────────────────────
maize = maize.set_index('date').sort_index()

weekly_dfs = []
for commodity in TARGET:
    subset = maize[maize['commodity'] == commodity]['price_per_mt']
    weekly = subset.resample('W-MON').median().dropna().reset_index()
    weekly.columns = ['week_start_date', 'price']
    weekly['commodity'] = commodity

    # Remove outliers (3 std devs)
    mean, std = weekly['price'].mean(), weekly['price'].std()
    before = len(weekly)
    weekly = weekly[(weekly['price'] >= mean - 3*std) & (weekly['price'] <= mean + 3*std)]
    removed = before - len(weekly)

    print(f"\n  [{commodity}]")
    print(f"    Rows after resample : {before}")
    print(f"    Outliers removed    : {removed}")
    print(f"    Final rows          : {len(weekly)}")
    print(f"    Date range          : {weekly['week_start_date'].min().date()} → {weekly['week_start_date'].max().date()}")
    print(f"    Price range         : ₦{weekly['price'].min():,.0f} – ₦{weekly['price'].max():,.0f}/MT")

    weekly_dfs.append(weekly)

maize_clean = pd.concat(weekly_dfs, ignore_index=True)

# ── Build full schema matching agricom_master.csv ─────────────────────────
maize_clean['currency']           = 'NGN'
maize_clean['unit']               = 'NGN/MT'
maize_clean['source']             = 'WFP Nigeria Food Prices'
maize_clean['market_type']        = 'retail'
maize_clean['region']             = 'National'
maize_clean['fx_rate']            = ''
maize_clean['rainfall_index']     = ''
maize_clean['extraction_date']    = str(datetime.today().date())
maize_clean['data_quality_score'] = 0.88
maize_clean['is_validated']       = True
maize_clean['notes']              = 'WFP VAM data — converted to NGN/MT'
maize_clean['record_type']        = 'historical'

# ── Load master and deduplicate ────────────────────────────────────────────
master = pd.read_csv(MASTER_PATH)
master['week_start_date'] = pd.to_datetime(master['week_start_date'], format='mixed')
maize_clean['week_start_date'] = pd.to_datetime(maize_clean['week_start_date'])

print(f"\n📊 Master dataset before: {len(master)} rows")

existing_keys = set(zip(master['commodity'].astype(str), master['week_start_date'].astype(str)))
maize_clean['key'] = list(zip(maize_clean['commodity'].astype(str), maize_clean['week_start_date'].astype(str)))
before = len(maize_clean)
maize_clean = maize_clean[~maize_clean['key'].isin(existing_keys)].drop(columns=['key'])
dupes = before - len(maize_clean)
if dupes: print(f"⚠️  Skipped {dupes} duplicates already in master")

# ── Append and save ────────────────────────────────────────────────────────
master = pd.concat([master, maize_clean], ignore_index=True)
master = master.sort_values(['commodity', 'week_start_date']).reset_index(drop=True)
master['price'] = master['price'].round(0)
master.to_csv(MASTER_PATH, index=False)

print(f"📊 Master dataset after  : {len(master)} rows")
print(f"\n✅ Maize data added successfully!")
print(f"\nNew commodities added:")
for c in TARGET:
    count = len(master[master['commodity'] == c])
    print(f"  {c}: {count} weekly rows")

print(f"\n➡️  Run the pipeline to include maize in forecasts:")
print(f"   python3 agrolinking-forecast/scripts/run_pipeline.py")
