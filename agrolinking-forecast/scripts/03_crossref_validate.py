"""
03_crossref_validate.py  — Agrolinking Forecast Pipeline

MODEL SELECTION:
  - Web reference found  → closest model to reference
  - No web reference     → proven 50/50 Prophet + XGBoost average

INFLATIONARY BIAS CORRECTION (March 2026):
  Nigeria is experiencing a severe fuel-driven cost-push shock:
  - Petrol: ₦875 → ₦1,332/litre (Iran-US-Israel war escalation, Feb 28 2026)
  - Food inflation: 8.89% Jan → 12.12% Feb 2026 (NBS confirmed)
  - NBS specifically cited beans, cowpeas, millet flour as rising commodities
  - FAO projects Nigeria food inflation at 17.1% for 2026 (highest in Africa)
  - Transportation costs spiking → direct cost-push on all ag commodity prices

  Our models were trained on 2024 data when inflation was FALLING.
  They therefore produce declining/flat long-range forecasts.
  We apply a verified upward inflation adjustment to the long-range
  (monthly, 3-month, 6-month) forecasts ONLY — daily/weekly unchanged
  as those are short-term and model-driven.

SOURCES:
  NBS CPI Feb 2026 report; Daily Post March 17 2026; Guardian March 4 2026;
  Dangote Refinery press conference March 9 2026; FAO Africa outlook Feb 2026
"""

import json, os, time, requests, warnings
import pandas as pd, numpy as np
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

warnings.filterwarnings('ignore')

BASE_DIR    = os.path.expanduser("~/Agrolinking-Prediction-Model/agrolinking-forecast")
LOGS_DIR    = os.path.join(BASE_DIR, "outputs/forecast_logs")
MASTER_PATH = os.path.join(BASE_DIR, "data/processed/agricom_master.csv")
TODAY       = datetime.today().date()

with open(os.path.join(LOGS_DIR, f"model_forecasts_{TODAY}.json")) as f:
    all_forecasts = json.load(f)

print("🌐 PHASE 3: Cross-Reference Validation")
print("=" * 65)
print(f"📅 Date : {TODAY}")
print(f"📂 Commodities: {list(all_forecasts.keys())}\n")

FX_RATE = 1650

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
}

COMMODITY_CONFIG = {
    'Hibiscus'     : ['hibiscus flower price Nigeria naira per tonne 2025',
                      'zobo hibiscus Nigeria market price per tonne'],
    'Soybeans'     : ['soybean price Nigeria naira per tonne 2025',
                      'soya beans Nigeria market price tonne naira'],
    'Ginger'       : ['ginger price Nigeria naira per tonne 2025',
                      'ginger Nigeria export price per tonne'],
    'Cocoa'        : ['cocoa price Nigeria naira per tonne 2025',
                      'cocoa beans Nigeria market price tonne'],
    'Cashew Nuts'  : ['cashew nuts price Nigeria naira per tonne 2025',
                      'cashew Nigeria export price tonne'],
    'Sorghum'      : ['sorghum price Nigeria naira per tonne 2025',
                      'guinea corn price Nigeria per tonne naira'],
    'Sesame'       : ['sesame seed price Nigeria naira per tonne 2025',
                      'sesame Nigeria export price tonne'],
    'Beans (red)'  : ['red beans oloyin price Nigeria naira per tonne 2025',
                      'oloyin beans Nigeria market price tonne'],
    'Beans (white)': ['white beans oloyin price Nigeria naira per tonne 2025',
                      'white oloyin beans Nigeria market price tonne'],
    'Maize (white)': ['white maize price Nigeria naira per tonne 2025',
                      'maize corn Nigeria market price tonne naira'],
    'Maize (yellow)':['yellow maize price Nigeria naira per tonne 2025',
                      'yellow corn Nigeria market price naira tonne'],
}

# ══════════════════════════════════════════════════════════════════════
# VERIFIED MARKET ANCHORS (March 2026)
# ══════════════════════════════════════════════════════════════════════
ANCHORS = {
    'Maize (white)' : 355_000,
    'Maize (yellow)': 365_000,
    'Beans (red)'   : 1_380_000,
    'Beans (white)' : 1_180_000,
}

# ══════════════════════════════════════════════════════════════════════
# INFLATIONARY BIAS CORRECTION
# Based on verified macro data — applied to long-range forecasts only
# ══════════════════════════════════════════════════════════════════════
# Fuel shock: petrol ₦875 → ₦1,332/litre (+52%) as of March 2026
# Transportation cost pass-through to food: ~60% coefficient (NBS data)
# Net upward pressure on agricultural commodity prices over next 6 months

# Monthly uplift applied to forecast horizons (compounding)
# Conservative — based on NBS Feb 2026 food inflation of 12.12% annualised
# but accounting for the new fuel shock from Feb 28 escalation
INFLATION_UPLIFT = {
    # horizon_key : base monthly_rate (for HIGH fuel sensitivity commodities)
    # NBS Feb 2026: food inflation 12.12% annualised + fuel shock Feb 28 2026
    # FAO 2026: Nigeria projected 17.1% food inflation — highest in Africa
    'monthly': 0.014,    # +1.4%/month × 1 = ~1.4% (immediate fuel pass-through)
    'q3month': 0.013,    # +1.3%/month × 3 = ~4.0% total
    'q6month': 0.012,    # +1.2%/month × 6 = ~7.4% total
}
HORIZON_MONTHS = {'monthly': 1, 'q3month': 3, 'q6month': 6}

# Commodities where NBS explicitly confirmed fuel-driven price rises
# These get full uplift
HIGH_FUEL_SENSITIVITY = {
    'Beans (red)',   # NBS Feb 2026 CPI explicitly cited
    'Beans (white)', # NBS Feb 2026 CPI explicitly cited
    'Maize (white)', # transport-heavy, northern Nigeria supply
    'Maize (yellow)',# transport-heavy, northern Nigeria supply
    'Sorghum',       # northern Nigeria, long haulage
    'Sesame',        # northern Nigeria, long haulage
    'Soybeans',      # middle belt, transport-sensitive
}
# Export commodities — less directly affected by domestic fuel costs
# (priced partly in USD), so lower uplift
LOW_FUEL_SENSITIVITY = {
    'Hibiscus',
    'Ginger',
    'Cocoa',
    'Cashew Nuts',
}

def apply_inflation_uplift(base_val, commodity, horizon):
    """Apply monthly compounding inflation uplift to long-range forecasts."""
    if base_val is None or base_val <= 0:
        return base_val
    rate   = INFLATION_UPLIFT.get(horizon, 0)
    months = HORIZON_MONTHS.get(horizon, 1)

    # Export commodities: partially USD-priced, less fuel-sensitive domestically
    if commodity in LOW_FUEL_SENSITIVITY:
        rate = rate * 0.45   # export commodities get 45% of domestic uplift

    # High fuel-sensitivity staples: add extra uplift on top of base
    # NBS specifically cited beans, cowpeas; maize/sorghum are long-haul from north
    if commodity in HIGH_FUEL_SENSITIVITY:
        extra = {'monthly': 0.005, 'q3month': 0.006, 'q6month': 0.007}
        rate  = rate + extra.get(horizon, 0)

    # Compound uplift
    multiplier = (1 + rate) ** months
    return float(base_val * multiplier)

# ══════════════════════════════════════════════════════════════════════
# POST-SELECTION CLAMP (safety net)
# ══════════════════════════════════════════════════════════════════════
POST_CLAMP = {
    'Maize (white)' : {'daily': 0.015, 'weekly': 0.030, 'biweekly': 0.050},
    'Maize (yellow)': {'daily': 0.015, 'weekly': 0.030, 'biweekly': 0.050},
    'Beans (red)'   : {'daily': 0.015, 'weekly': 0.030, 'biweekly': 0.050},
    'Beans (white)' : {'daily': 0.015, 'weekly': 0.030, 'biweekly': 0.050},
    '_default'      : {'daily': 0.050, 'weekly': 0.080, 'biweekly': 0.120},
}

def get_anchor(commodity):
    if commodity in ANCHORS:
        return ANCHORS[commodity]
    try:
        df = pd.read_csv(MASTER_PATH)
        df['week_start_date'] = pd.to_datetime(df['week_start_date'], format='mixed')
        hist = df[(df['commodity']==commodity)&(df['record_type']=='historical')]\
                 .sort_values('week_start_date').tail(6)
        if not hist.empty:
            w = np.arange(1, len(hist)+1, dtype=float)
            return float(np.average(hist['price'].values, weights=w))
    except:
        pass
    return None

def post_clamp(value, commodity, horizon='daily'):
    if value is None or value <= 0:
        return value
    anchor = get_anchor(commodity)
    if not anchor:
        return value
    cfg = POST_CLAMP.get(commodity, POST_CLAMP['_default'])
    pct = cfg.get(horizon, 0.05)
    return float(max(anchor*(1-pct), min(anchor*(1+pct), value)))

# ── Price extraction from web ───────────────────────────────────────────────
REF_TRUST = {
    'Maize (white)' : 0.30,
    'Maize (yellow)': 0.30,
    'Beans (red)'   : 0.30,
    'Beans (white)' : 0.30,
    '_default'      : 0.50,
}

def extract_ngn(text, commodity):
    import re
    prices = []
    for m in re.finditer(r'[₦N]\s?(\d{1,3}(?:,\d{3})+)', text):
        v = float(m.group(1).replace(',',''))
        if 50_000 <= v <= 60_000_000:
            prices.append(v)
    for m in re.finditer(r'\b(\d{6,8})\b', text):
        v = float(m.group(1))
        if 50_000 <= v <= 60_000_000:
            prices.append(v)
    for m in re.finditer(r'\$\s?(\d{1,4}(?:,\d{3})?(?:\.\d+)?)\s?(?:per\s?(?:MT|tonne|ton))?', text, re.I):
        usd = float(m.group(1).replace(',',''))
        if 50 <= usd <= 25_000:
            prices.append(usd * FX_RATE)
    return prices

def safe_get(url, timeout=10):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        return r.text if r.status_code == 200 else None
    except:
        return None

def ddg(query):
    url  = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
    html = safe_get(url)
    if not html: return ""
    soup = BeautifulSoup(html, 'html.parser')
    return " ".join(s.get_text() for s in
                    soup.find_all('a', class_='result__snippet') +
                    soup.find_all('a', class_='result__a'))

# ── Fetch web references ────────────────────────────────────────────────────
print("🔍 Fetching live reference prices...\n")
reference_prices = {}

for commodity, terms in COMMODITY_CONFIG.items():
    if commodity not in all_forecasts:
        continue
    found = []
    for term in terms:
        print(f"  Searching: \"{term}\"")
        found.extend(extract_ngn(ddg(term), commodity))
        time.sleep(1.2)

    if found:
        anchor = get_anchor(commodity)
        limit  = REF_TRUST.get(commodity, REF_TRUST['_default'])
        if anchor:
            found = [p for p in found if anchor*(1-limit) <= p <= anchor*(1+limit)]

    if found:
        ref = float(np.median(found))
        print(f"  ✅ [{commodity}] {len(found)} signal(s) → ₦{ref:,.0f}\n")
        reference_prices[commodity] = ref
    else:
        print(f"  ⚠️  [{commodity}] No verified price — using Prophet+XGBoost average\n")
        reference_prices[commodity] = None

# ── Model selection ─────────────────────────────────────────────────────────
def select(commodity, models_data, ref_price):
    vals = {}
    for m in ('arima','prophet','xgboost'):
        v = models_data.get(m,{}).get('daily')
        if v and isinstance(v,(int,float)) and v > 0:
            vals[m] = float(v)
    if not vals:
        return None, None, None, 'none', None, None, '❌'

    # Case A: credible web reference
    if ref_price and ref_price > 0:
        errors = {m: abs(v-ref_price)/ref_price*100 for m,v in vals.items()}
        best   = min(errors, key=errors.get)
        err    = errors[best]
        flag   = "✅" if err < 5 else ("⚠️" if err < 15 else "❌")
        d  = vals[best]
        w  = models_data.get(best,{}).get('weekly',  d)
        bw = models_data.get(best,{}).get('biweekly', w)
        return d, w, bw, best, err, ref_price, flag

    # Case B: no ref → proven 50/50 Prophet + XGBoost
    p_d  = vals.get('prophet')
    x_d  = vals.get('xgboost')
    p_w  = models_data.get('prophet',{}).get('weekly')
    x_w  = models_data.get('xgboost',{}).get('weekly')
    p_bw = models_data.get('prophet',{}).get('biweekly')
    x_bw = models_data.get('xgboost',{}).get('biweekly')

    if p_d and x_d:
        d  = (p_d + x_d) / 2
        w  = ((p_w or p_d) + (x_w or x_d)) / 2
        bw = ((p_bw or p_w or p_d) + (x_bw or x_w or x_d)) / 2
        label, flag = 'prophet+xgboost', '🔄'
    elif p_d:
        d, w, bw = p_d, p_w or p_d, p_bw or p_w or p_d
        label, flag = 'prophet', '🔄'
    elif x_d:
        d, w, bw = x_d, x_w or x_d, x_bw or x_w or x_d
        label, flag = 'xgboost', '🔄'
    else:
        a_d  = vals.get('arima')
        a_w  = models_data.get('arima',{}).get('weekly',  a_d)
        a_bw = models_data.get('arima',{}).get('biweekly', a_w)
        d, w, bw = a_d, a_w, a_bw
        label, flag = 'arima', '⚠️'

    return d, w, bw, label, None, None, flag

# ── Long-range builder with inflation uplift ────────────────────────────────
def build_lr_with_inflation(commodity, models_data, label, best_daily):
    m_key   = label.split('+')[0]
    prophet = models_data.get('prophet', {})

    weekly_val = (models_data.get(m_key,{}).get('weekly') or
                  models_data.get('prophet',{}).get('weekly') or
                  best_daily)

    # Spread from Prophet CI — but enforce a MINIMUM spread so ranges are never zero
    # Minimum spreads: 4% for 1M, 7% for 3M, 10% for 6M of the daily price
    MIN_SPREAD_PCT = {'monthly': 0.04, 'q3month': 0.07, 'q6month': 0.10}

    if prophet.get('weekly_lower') and prophet.get('weekly_upper'):
        raw_spread = abs(float(prophet['weekly_upper']) - float(prophet['weekly_lower']))
    else:
        raw_spread = best_daily * 0.06

    # Model-derived trend — dampened, asymmetric (more upside room than downside)
    trend = (weekly_val - best_daily) / best_daily if best_daily else 0
    trend = max(-0.005, min(0.015, trend))  # allow up to +1.5%/wk upside, only -0.5% downside

    # Base forecast points from dampened trend
    m1_base = best_daily * (1 + trend * 4)
    m3_base = best_daily * (1 + trend * 13)
    m6_base = best_daily * (1 + trend * 26)

    # Floor = current daily price, ceiling = +20/25/30% for 1M/3M/6M
    m1_base = max(best_daily * 1.00, min(best_daily * 1.20, m1_base))
    m3_base = max(best_daily * 1.00, min(best_daily * 1.25, m3_base))
    m6_base = max(best_daily * 1.00, min(best_daily * 1.30, m6_base))

    # Apply verified inflation uplift on top of model trend
    m1_inflated = apply_inflation_uplift(m1_base, commodity, 'monthly')
    m3_inflated = apply_inflation_uplift(m3_base, commodity, 'q3month')
    m6_inflated = apply_inflation_uplift(m6_base, commodity, 'q6month')

    # Confidence interval spreads — enforce minimum so Sorghum/Sesame aren't flat
    sp1 = max(raw_spread * 1.4, best_daily * MIN_SPREAD_PCT['monthly'])
    sp3 = max(raw_spread * 2.2, best_daily * MIN_SPREAD_PCT['q3month'])
    sp6 = max(raw_spread * 3.0, best_daily * MIN_SPREAD_PCT['q6month'])

    # Lower bound floor: never let the lower bound fall below the current daily price
    # (it makes no sense to say the price might go below where it is today given current inflation)
    lo1 = max(round(m1_inflated - sp1, 0), round(best_daily, 0))
    lo3 = max(round(m3_inflated - sp3, 0), round(best_daily, 0))
    lo6 = max(round(m6_inflated - sp6, 0), round(best_daily, 0))

    return {
        'monthly': {
            'point': round(m1_inflated, 0),
            'lower': lo1,
            'upper': round(m1_inflated + sp1, 0)
        },
        'q3month': {
            'point': round(m3_inflated, 0),
            'lower': lo3,
            'upper': round(m3_inflated + sp3, 0)
        },
        'q6month': {
            'point': round(m6_inflated, 0),
            'lower': lo6,
            'upper': round(m6_inflated + sp6, 0)
        },
    }

# ── Build final forecasts ───────────────────────────────────────────────────
print("\n📊 MODEL SELECTION")
print("=" * 75)
print(f"{'Commodity':<16} {'ARIMA':>12} {'Prophet':>12} {'XGBoost':>12} "
      f"{'Ref':>10} {'Winner':>18} St")
print("-" * 92)

final_forecasts = {}

for commodity, models_data in all_forecasts.items():
    ref = reference_prices.get(commodity)

    d, w, bw, label, err, ref_used, flag = select(commodity, models_data, ref)
    if d is None:
        print(f"  [{commodity}] ❌ No valid forecast")
        continue

    # Post-selection clamp (daily + weekly only — long-range is inflation-adjusted)
    d  = post_clamp(d,  commodity, 'daily')
    w  = post_clamp(w,  commodity, 'weekly')
    bw = post_clamp(bw, commodity, 'biweekly')

    # Long-range with inflation uplift
    lr = build_lr_with_inflation(commodity, models_data, label, d)

    final_forecasts[commodity] = {
        'daily'     : round(d,  0),
        'weekly'    : round(w,  0),
        'biweekly'  : round(bw, 0),
        'monthly'   : lr['monthly'],
        'q3month'   : lr['q3month'],
        'q6month'   : lr['q6month'],
        'model'     : label,
        'reference' : ref_used,
        'error_pct' : round(err, 2) if err is not None else None,
        'flag'      : flag,
        'all_models': {m: models_data.get(m,{}).get('daily')
                       for m in ('arima','prophet','xgboost')},
        'confidence': (
            'High'   if err is not None and err < 5
            else 'Medium' if err is None or err < 15
            else 'Low'
        ),
        'inflation_adjusted': True,
    }

    a = models_data.get('arima',  {}).get('daily') or 0
    p = models_data.get('prophet',{}).get('daily') or 0
    x = models_data.get('xgboost',{}).get('daily') or 0
    r_str = f"₦{ref_used:,.0f}" if ref_used else "No ref"
    print(f"{commodity:<16} {a:>12,.0f} {p:>12,.0f} {x:>12,.0f} "
          f"{r_str:>10} {label:>18} {flag}")

out = os.path.join(LOGS_DIR, f"final_forecasts_{TODAY}.json")
with open(out,'w') as f:
    json.dump(final_forecasts, f, indent=2, default=str)

print(f"\n✅ Validation complete → {out}")
print(f"\n📈 Inflation adjustment applied to long-range forecasts:")
print(f"   Base rates (high fuel-sensitivity commodities):")
print(f"   1-month  : +{(INFLATION_UPLIFT['monthly']+0.005)*100:.1f}%/month — fuel shock + NBS-cited staples")
print(f"   3-month  : +{(INFLATION_UPLIFT['q3month']+0.006)*100:.1f}%/month × 3 = ~{((1+(INFLATION_UPLIFT['q3month']+0.006))**3-1)*100:.1f}% total")
print(f"   6-month  : +{(INFLATION_UPLIFT['q6month']+0.007)*100:.1f}%/month × 6 = ~{((1+(INFLATION_UPLIFT['q6month']+0.007))**6-1)*100:.1f}% total")
print(f"   Export commodities (Hibiscus, Ginger, Cocoa, Cashew): 45% of base rate")
print(f"   Floor: long-range lower bound ≥ current daily price (no declining forecasts)")
print(f"\n   Source: NBS CPI Feb 2026 | Dangote Refinery Mar 9 2026 | FAO 2026 Outlook")

winners = {}
for c,fc in final_forecasts.items():
    m = fc.get('model','?')
    winners[m] = winners.get(m,0)+1
print("\n📊 Model selection:")
for m,n in sorted(winners.items(), key=lambda x:-x[1]):
    print(f"   {m:<22}: {n} commodity(ies)")
print("\n➡️  Next: 04_export_outputs.py\n")