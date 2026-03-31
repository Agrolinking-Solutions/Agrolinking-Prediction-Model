"""
02b_clamp_forecasts.py
─────────────────────────────────────────────────────────────────
Runs AFTER 02_train_and_forecast.py, BEFORE 03_crossref_validate.py

Clamps per-model daily/weekly/biweekly forecast values to a
tight corridor around the last known historical price.

This prevents wild swings from commodities with sparse or old data
(Maize ends 2023, Beans data is retail-market based).
"""

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.expanduser("~/Agrolinking-Prediction-Model/agrolinking-forecast")
MASTER_PATH = os.path.join(BASE_DIR, "data/processed/agricom_master.csv")
LOGS_DIR    = os.path.join(BASE_DIR, "outputs/forecast_logs")
TODAY       = datetime.today().date()

print("=" * 60)
print("  🔒 02b: FORECAST STABILITY CLAMP")
print("=" * 60)

# ── Load today's raw model forecasts ───────────────────────────────────────
fc_path = os.path.join(LOGS_DIR, f"model_forecasts_{TODAY}.json")
if not os.path.exists(fc_path):
    print(f"❌ No forecast file found: {fc_path}")
    print("   Run 02_train_and_forecast.py first.")
    exit(1)

with open(fc_path) as f:
    all_forecasts = json.load(f)

# ── Load master for last historical price per commodity ────────────────────
master = pd.read_csv(MASTER_PATH)
master['week_start_date'] = pd.to_datetime(master['week_start_date'], format='mixed')

def get_last_price(commodity):
    hist = master[
        (master['commodity'] == commodity) &
        (master['record_type'] == 'historical')
    ].sort_values('week_start_date')
    if hist.empty:
        return None
    return float(hist['price'].iloc[-1])

def get_recent_avg(commodity, n=8):
    """Weighted average of last n historical prices (recent-biased)."""
    hist = master[
        (master['commodity'] == commodity) &
        (master['record_type'] == 'historical')
    ].sort_values('week_start_date').tail(n)
    if hist.empty:
        return None
    weights = np.arange(1, len(hist) + 1, dtype=float)
    return float(np.average(hist['price'].values, weights=weights))

# ── Clamp configuration ─────────────────────────────────────────────────────
# max_pct = maximum allowed % change from last known price per horizon
# anchor  = 'last' uses final price; 'avg' uses weighted recent average
CLAMP_CONFIG = {
    # Maize: WFP data ends 2023 → very tight clamp + anchor to recent avg
    'Maize (white)' : {'daily': 0.025, 'weekly': 0.040, 'biweekly': 0.060, 'anchor': 'avg'},
    'Maize (yellow)': {'daily': 0.025, 'weekly': 0.040, 'biweekly': 0.060, 'anchor': 'avg'},
    # Beans: WFP retail data ends 2023 → tight clamp
    'Beans (red)'   : {'daily': 0.030, 'weekly': 0.050, 'biweekly': 0.080, 'anchor': 'avg'},
    'Beans (white)' : {'daily': 0.030, 'weekly': 0.050, 'biweekly': 0.080, 'anchor': 'avg'},
    # Agricom commodities: recent data, allow more movement
    'Hibiscus'      : {'daily': 0.045, 'weekly': 0.080, 'biweekly': 0.120, 'anchor': 'last'},
    'Ginger'        : {'daily': 0.045, 'weekly': 0.080, 'biweekly': 0.120, 'anchor': 'last'},
    'Cocoa'         : {'daily': 0.040, 'weekly': 0.070, 'biweekly': 0.110, 'anchor': 'last'},
    'Soybeans'      : {'daily': 0.035, 'weekly': 0.060, 'biweekly': 0.090, 'anchor': 'last'},
    'Cashew Nuts'   : {'daily': 0.040, 'weekly': 0.070, 'biweekly': 0.100, 'anchor': 'last'},
    'Sorghum'       : {'daily': 0.035, 'weekly': 0.060, 'biweekly': 0.090, 'anchor': 'last'},
    'Sesame'        : {'daily': 0.040, 'weekly': 0.070, 'biweekly': 0.100, 'anchor': 'last'},
}
DEFAULT_CLAMP = {'daily': 0.050, 'weekly': 0.080, 'biweekly': 0.120, 'anchor': 'last'}

# ── Known price anchors (from market research) ─────────────────────────────
# Override the computed last price when we know the real market level
PRICE_ANCHORS = {
    'Maize (white)' : 302_000,   # ~₦302K/MT based on current market
    'Maize (yellow)': 310_000,   # ~₦310K/MT based on current market
}

# ── Apply clamps ────────────────────────────────────────────────────────────
MODELS    = ['arima', 'prophet', 'xgboost']
HORIZONS  = ['daily', 'weekly', 'biweekly']

total_clamped = 0

for commodity, model_data in all_forecasts.items():
    cfg       = CLAMP_CONFIG.get(commodity, DEFAULT_CLAMP)
    anchor_type = cfg.get('anchor', 'last')

    # Determine anchor price
    if commodity in PRICE_ANCHORS:
        anchor_price = PRICE_ANCHORS[commodity]
        anchor_src   = 'market research'
    elif anchor_type == 'avg':
        anchor_price = get_recent_avg(commodity)
        anchor_src   = 'recent avg'
    else:
        anchor_price = get_last_price(commodity)
        anchor_src   = 'last price'

    if anchor_price is None or anchor_price <= 0:
        print(f"  ⚠️  [{commodity}] No anchor price — skipping")
        continue

    commodity_clamped = 0

    for model in MODELS:
        if model not in model_data:
            continue
        for horizon in HORIZONS:
            v = model_data[model].get(horizon)
            if v is None or not isinstance(v, (int, float)) or v <= 0:
                continue

            max_pct = cfg.get(horizon, DEFAULT_CLAMP['daily'])
            lo = anchor_price * (1 - max_pct)
            hi = anchor_price * (1 + max_pct)

            clamped = float(max(lo, min(hi, v)))

            if abs(clamped - v) > 500:   # only log meaningful changes
                print(f"  🔒 [{commodity}] {model} {horizon}: "
                      f"₦{v:,.0f} → ₦{clamped:,.0f}  "
                      f"(anchor: ₦{anchor_price:,.0f} {anchor_src}, ±{max_pct*100:.1f}%)")
                commodity_clamped += 1
                total_clamped += 1

            all_forecasts[commodity][model][horizon] = clamped

    if commodity_clamped == 0:
        print(f"  ✅ [{commodity}] All values within bounds  "
              f"(anchor ₦{anchor_price:,.0f})")

# ── Save patched forecast file (overwrites) ────────────────────────────────
with open(fc_path, 'w') as f:
    json.dump(all_forecasts, f, indent=2, default=str)

print()
print(f"{'─' * 60}")
print(f"  Total values clamped : {total_clamped}")
print(f"  Forecast file saved  : {fc_path}")
print(f"{'─' * 60}")
print(f"\n✅ Clamp complete. Run 03_crossref_validate.py next.\n")
