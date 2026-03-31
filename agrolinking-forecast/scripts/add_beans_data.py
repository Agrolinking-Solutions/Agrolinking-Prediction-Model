import pandas as pd
import numpy as np
import os
from datetime import datetime

BASE_DIR    = os.path.expanduser("~/Agrolinking-Prediction-Model/agrolinking-forecast")
MASTER_PATH = os.path.join(BASE_DIR, "data/processed/agricom_master.csv")

# ── Load WFP data ──────────────────────────────────────────────────────────
# Update this path to wherever you saved the WFP CSV
WFP_PATH = os.path.expanduser("/home/john/Agrolinking-Prediction-Model/agrolinking-forecast/data/raw/wfp_food_prices_nga.csv")

print("=" * 55)
print("  🫘 BEANS DATA IMPORT — WFP Nigeria Food Prices")
print("=" * 55)

wfp = pd.read_csv(WFP_PATH)
wfp['date'] = pd.to_datetime(wfp['date'])

# ── Filter to beans only (red + white) ────────────────────────────────────
target = ['Beans (red)', 'Beans (white)']
beans  = wfp[wfp['commodity'].isin(target)].copy()
print(f"\n📦 Raw beans rows loaded: {len(beans)}")

# ── Convert price to NGN/MT ────────────────────────────────────────────────
# All beans rows are priced per 2.5 KG → divide by 2.5 then multiply by 1000
beans['price_per_mt'] = (beans['price'] / 2.5) * 1000
print(f"💱 Unit conversion: NGN/2.5KG → NGN/MT (÷2.5 ×1000)")

# ── Resample to weekly national median ────────────────────────────────────
# Set date as index, resample to weekly Monday-anchored
beans = beans.set_index('date').sort_index()

weekly_dfs = []
for commodity in target:
    subset = beans[beans['commodity'] == commodity]['price_per_mt']

    # Resample to weekly median across all markets
    weekly = subset.resample('W-MON').median().dropna().reset_index()
    weekly.columns = ['week_start_date', 'price']
    weekly['commodity'] = commodity

    # Remove outliers (beyond 3 std)
    mean = weekly['price'].mean()
    std  = weekly['price'].std()
    before = len(weekly)
    weekly = weekly[
        (weekly['price'] >= mean - 3*std) &
        (weekly['price'] <= mean + 3*std)
    ]
    removed = before - len(weekly)
    print(f"\n  [{commodity}]")
    print(f"    Rows after resampling : {before}")
    print(f"    Outliers removed      : {removed}")
    print(f"    Final rows            : {len(weekly)}")
    print(f"    Date range            : {weekly['week_start_date'].min().date()} → {weekly['week_start_date'].max().date()}")
    print(f"    Price range           : ₦{weekly['price'].min():,.0f} – ₦{weekly['price'].max():,.0f}/MT")

    weekly_dfs.append(weekly)

beans_clean = pd.concat(weekly_dfs, ignore_index=True)

# ── Build full schema matching agricom_master.csv ─────────────────────────
beans_clean['currency']          = 'NGN'
beans_clean['unit']              = 'NGN/MT'
beans_clean['source']            = 'WFP Nigeria Food Prices'
beans_clean['market_type']       = 'retail'
beans_clean['region']            = 'National'
beans_clean['fx_rate']           = ''
beans_clean['rainfall_index']    = ''
beans_clean['extraction_date']   = str(datetime.today().date())
beans_clean['data_quality_score']= 0.90
beans_clean['is_validated']      = True
beans_clean['notes']             = 'WFP VAM data — converted from NGN/2.5KG to NGN/MT (×400)'
beans_clean['record_type']       = 'historical'

# ── Load master and check for duplicates ──────────────────────────────────
master = pd.read_csv(MASTER_PATH)
master['week_start_date'] = pd.to_datetime(master['week_start_date'], format='mixed')
beans_clean['week_start_date'] = pd.to_datetime(beans_clean['week_start_date'])

print(f"\n📊 Master dataset before: {len(master)} rows")

# Drop any rows already in master for these commodities + dates
existing_keys = set(
    zip(master['commodity'].astype(str),
        master['week_start_date'].astype(str))
)
beans_clean['key'] = list(zip(
    beans_clean['commodity'].astype(str),
    beans_clean['week_start_date'].astype(str)
))
before = len(beans_clean)
beans_clean = beans_clean[~beans_clean['key'].isin(existing_keys)]
beans_clean = beans_clean.drop(columns=['key'])
dupes = before - len(beans_clean)
if dupes:
    print(f"⚠️  Skipped {dupes} duplicate rows already in master")

# ── Append and save ────────────────────────────────────────────────────────
master = pd.concat([master, beans_clean], ignore_index=True)
master = master.sort_values(['commodity', 'week_start_date']).reset_index(drop=True)
master['price'] = master['price'].round(0)
master.to_csv(MASTER_PATH, index=False)

print(f"📊 Master dataset after : {len(master)} rows")
print(f"\n✅ Beans data successfully added to master dataset!")
print(f"\nNew commodities added:")
for c in target:
    count = len(master[master['commodity'] == c])
    print(f"  {c}: {count} weekly rows")

print(f"\n➡️  You can now run the pipeline and beans will be")
print(f"   included in all forecasts and WhatsApp messages.")
