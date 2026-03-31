import pandas as pd
import os
from datetime import datetime, date

BASE_DIR    = os.path.expanduser("~/Agrolinking-Prediction-Model/agrolinking-forecast")
MASTER_PATH = os.path.join(BASE_DIR, "data/processed/agricom_master.csv")

COMMODITIES = ['Cashew Nuts', 'Cocoa', 'Ginger', 'Hibiscus', 'Sesame', 'Sorghum', 'Soybeans']

print("=" * 50)
print("  📥 AGROLINKING — ADD NEW WEEKLY DATA")
print("=" * 50)
print("Enter prices from the latest Agricom post.")
print("Press Enter to skip a commodity (if not in post).\n")

# ── Get post date ──────────────────────────────────────────────────────────
while True:
    date_input = input("📅 Post date (YYYY-MM-DD) or press Enter for today: ").strip()
    if date_input == "":
        post_date = str(date.today())
        break
    try:
        datetime.strptime(date_input, "%Y-%m-%d")
        post_date = date_input
        break
    except ValueError:
        print("   ⚠️  Invalid format. Use YYYY-MM-DD e.g. 2026-03-14")

# ── Get FX rate ────────────────────────────────────────────────────────────
fx_input = input("💱 USD/NGN FX rate (press Enter to use 1650): ").strip()
fx_rate  = float(fx_input) if fx_input else 1650.0

print(f"\n📌 Recording prices for: {post_date} | FX: {fx_rate}\n")

# ── Load master to check for duplicates ───────────────────────────────────
master = pd.read_csv(MASTER_PATH)
master['week_start_date'] = pd.to_datetime(master['week_start_date'], format='mixed')

new_rows = []
skipped  = []
dupes    = []

for commodity in COMMODITIES:
    # Check if this date already exists
    already = (
        (master['commodity'] == commodity) &
        (master['week_start_date'] == pd.Timestamp(post_date)) &
        (master['record_type'] == 'historical')
    ).any()

    if already:
        dupes.append(commodity)
        print(f"  ⚠️  {commodity:<15} — already exists for {post_date}, skipping")
        continue

    raw = input(f"  {commodity:<15} ₦/tonne: ").strip()

    if raw == "":
        skipped.append(commodity)
        continue

    # Handle formats: 1800000 or 1,800,000
    try:
        price = float(raw.replace(',', ''))
    except ValueError:
        print(f"     ⚠️  Invalid price — skipping {commodity}")
        skipped.append(commodity)
        continue

    new_rows.append({
        'commodity'         : commodity,
        'week_start_date'   : post_date,
        'price'             : price,
        'currency'          : 'NGN',
        'unit'              : 'NGN/MT',
        'source'            : 'Agricom',
        'market_type'       : 'wholesale',
        'region'            : 'National',
        'fx_rate'           : fx_rate,
        'rainfall_index'    : '',
        'extraction_date'   : str(date.today()),
        'data_quality_score': 0.95,
        'is_validated'      : True,
        'notes'             : 'Historical data from Agricom Instagram post',
        'record_type'       : 'historical',
    })

# ── Save ───────────────────────────────────────────────────────────────────
print()
if new_rows:
    new_df = pd.DataFrame(new_rows)
    master = pd.concat([master, new_df], ignore_index=True)
    master = master.sort_values(['commodity', 'week_start_date']).reset_index(drop=True)
    master.to_csv(MASTER_PATH, index=False)

    print("=" * 50)
    print(f"  ✅ {len(new_rows)} row(s) added to master dataset")
    print(f"  📊 Master dataset now has {len(master)} rows")
    if skipped:
        print(f"  ⏭️  Skipped  : {', '.join(skipped)}")
    if dupes:
        print(f"  ♻️  Duplicate: {', '.join(dupes)}")
    print("=" * 50)
    print("\n✅ Data saved. You can now run the pipeline:")
    print("   python3 agrolinking-forecast/scripts/run_pipeline.py")
else:
    print("  ℹ️  No new data entered — master dataset unchanged.")
