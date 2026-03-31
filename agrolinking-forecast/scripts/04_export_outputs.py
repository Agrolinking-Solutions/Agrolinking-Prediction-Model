"""
04_export_outputs.py  — Agrolinking Forecast Pipeline
──────────────────────────────────────────────────────
Generates all WhatsApp-ready message files from final_forecasts JSON.
Daily % change is computed vs yesterday's final_forecasts file.
"""

import json, os, glob
from datetime import datetime, timedelta

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.expanduser("~/Agrolinking-Prediction-Model/agrolinking-forecast")
LOGS_DIR  = os.path.join(BASE_DIR, "outputs/forecast_logs")
OUT_DIR   = os.path.join(BASE_DIR, "outputs/whatsapp_messages")
os.makedirs(OUT_DIR, exist_ok=True)

TODAY  = datetime.today().date()
NOW    = datetime.now()

print("=" * 60)
print("  📤 04: EXPORT OUTPUTS")
print("=" * 60)

# ── Load today's final forecasts ───────────────────────────────────────────
fc_path = os.path.join(LOGS_DIR, f"final_forecasts_{TODAY}.json")
if not os.path.exists(fc_path):
    print(f"❌  No final forecast file: {fc_path}")
    print("    Run 03_crossref_validate.py first.")
    exit(1)

with open(fc_path) as f:
    fc = json.load(f)

# ── Load YESTERDAY's final forecasts for % change ─────────────────────────
yesterday = TODAY - timedelta(days=1)
yest_path = os.path.join(LOGS_DIR, f"final_forecasts_{yesterday}.json")

# Try up to 7 days back if yesterday missing (weekend/holiday gap)
prev_fc   = {}
prev_date = None
for delta in range(1, 8):
    check = TODAY - timedelta(days=delta)
    path  = os.path.join(LOGS_DIR, f"final_forecasts_{check}.json")
    if os.path.exists(path):
        with open(path) as f:
            prev_fc   = json.load(f)
        prev_date = check
        print(f"📅 Previous forecast loaded: {check}")
        break

if not prev_fc:
    print("⚠️  No previous forecast found — % changes will show as 'First forecast'")

# ── Commodity display order ────────────────────────────────────────────────
DISPLAY_ORDER = [
    'Hibiscus', 'Soybeans', 'Ginger', 'Cocoa', 'Cashew Nuts',
    'Sorghum', 'Sesame', 'Beans (red)', 'Beans (white)',
    'Maize (white)', 'Maize (yellow)'
]

# ── Helpers ────────────────────────────────────────────────────────────────
def fmt(p):
    if p is None: return "—"
    return f"₦{int(round(float(p))):,}"

def fmtM(p):
    if p is None: return "—"
    p = float(p)
    if p >= 1_000_000: return f"₦{p/1_000_000:.2f}M"
    if p >= 1_000:     return f"₦{p/1_000:.0f}K"
    return f"₦{int(p):,}"

def pct_change(today_price, prev_price):
    """
    Returns (pct_float, display_string, arrow_symbol)
    arrow: ↑ ↓ ➩ (stable)
    """
    if prev_price is None or prev_price == 0 or today_price is None:
        return None, "First forecast", "➩"
    pct = (float(today_price) - float(prev_price)) / float(prev_price) * 100
    if abs(pct) < 0.5:           # < 0.5% treated as stable
        return pct, "➩stable", "➩"
    elif pct > 0:
        return pct, f"↑ +{pct:.1f}%", "↑"
    else:
        return pct, f"↓ {pct:.1f}%", "↓"

def get_prev_price(commodity):
    """Get previous daily forecast price for a commodity."""
    if not prev_fc:
        return None
    return prev_fc.get(commodity, {}).get('daily')

def trend_label(daily, weekly):
    """Short-range trend based on daily vs weekly."""
    if daily is None or weekly is None:
        return "Stable"
    pct = (float(weekly) - float(daily)) / float(daily) * 100
    if pct > 4:   return "Bullish"
    if pct < -4:  return "Bearish"
    return "Stable"

# ── Date/time header (Agricom style) ──────────────────────────────────────
DAYS    = ['Mon','Tue','Wed','Thur','Fri','Sat','Sun']
MONTHS  = ['January','February','March','April','May','June',
           'July','August','September','October','November','December']
MONTHS_S= ['Jan','Feb','Mar','Apr','May','Jun',
           'Jul','Aug','Sep','Oct','Nov','Dec']

day_name = DAYS[NOW.weekday()]
month    = MONTHS[NOW.month - 1]
month_s  = MONTHS_S[NOW.month - 1]
hour     = NOW.strftime('%I').lstrip('0') or '12'
minute   = NOW.strftime('%M')
ampm     = NOW.strftime('%p')
header   = f"{day_name} {NOW.day} {month}, {NOW.year} · {hour}:{minute} {ampm}"

FOOTER_DAILY = "📊 Daily Price Forecast | Agrolinking Research & Data\n⚡ Powered by Agrolinking Intelligence System"
FOOTER_BRAND = "🌱 Agrolinking Research & Data | Powered by Agrolinking Intelligence System"

# ════════════════════════════════════════════════════════════════════════════
# FILE 1: DAILY FORECAST  (with % change vs yesterday)
# ════════════════════════════════════════════════════════════════════════════
lines = [
    "COPY YOUR DAILY FORECAST:",
    "-" * 52,
    header,
    ""
]

for c in DISPLAY_ORDER:
    if c not in fc:
        continue
    today_p = fc[c].get('daily')
    prev_p  = get_prev_price(c)
    pct, label, arrow = pct_change(today_p, prev_p)
    lines.append(f"{c} ≡ {fmt(today_p)}/tonne  {label}")

lines += ["", FOOTER_DAILY]
daily_path = os.path.join(OUT_DIR, f"daily_{TODAY}.txt")
with open(daily_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"✅ Daily forecast   → {daily_path}")

# ════════════════════════════════════════════════════════════════════════════
# FILE 2: WEEKLY FORECAST
# ════════════════════════════════════════════════════════════════════════════
nxt       = TODAY + timedelta(days=7 - TODAY.weekday() if TODAY.weekday() != 0 else 7)
nxt_label = f"w/c {nxt.day} {MONTHS_S[nxt.month-1]} {nxt.year}"

lines = [
    "📅 WEEKLY FORECAST:",
    "-" * 52,
    f"📅 WEEKLY FORECAST – {nxt_label}",
    ""
]
for c in DISPLAY_ORDER:
    if c not in fc:
        continue
    lines.append(f"{c} ≡ {fmt(fc[c].get('weekly'))}/tonne")

lines += ["", FOOTER_BRAND]
weekly_path = os.path.join(OUT_DIR, f"weekly_{TODAY}.txt")
with open(weekly_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"✅ Weekly forecast  → {weekly_path}")

# ════════════════════════════════════════════════════════════════════════════
# FILE 3: 2-WEEK FORECAST
# ════════════════════════════════════════════════════════════════════════════
twk       = nxt + timedelta(weeks=1)
twk_label = f"w/c {twk.day} {MONTHS_S[twk.month-1]} {twk.year}"

lines = [
    "📅 2-WEEK FORECAST:",
    "-" * 52,
    f"📅 2-WEEK FORECAST – {twk_label}",
    ""
]
for c in DISPLAY_ORDER:
    if c not in fc:
        continue
    lines.append(f"{c} ≡ {fmt(fc[c].get('biweekly'))}/tonne")

lines += ["", FOOTER_BRAND]
biweekly_path = os.path.join(OUT_DIR, f"biweekly_{TODAY}.txt")
with open(biweekly_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"✅ 2-Week forecast  → {biweekly_path}")

# ════════════════════════════════════════════════════════════════════════════
# FILE 4: MONTHLY FORECAST
# ════════════════════════════════════════════════════════════════════════════
m1_month = MONTHS[(TODAY + timedelta(weeks=4)).month - 1]
m1_year  = (TODAY + timedelta(weeks=4)).year

lines = [
    "-" * 52,
    f"📅 1-MONTH OUTLOOK — {m1_month} {m1_year}",
    f"{'Commodity':<18} {'Price Range (₦/tonne)':<28} Trend",
    "-" * 60
]
for c in DISPLAY_ORDER:
    if c not in fc:
        continue
    m = fc[c].get('monthly', {})
    if isinstance(m, dict) and m.get('lower') and m.get('upper'):
        rng  = f"{fmtM(m['lower'])} – {fmtM(m['upper'])}"
        trd  = trend_label(fc[c].get('daily'), fc[c].get('monthly', {}).get('point'))
    else:
        rng  = fmt(m) if m else "—"
        trd  = "Stable"
    conf_icon = "🔵" if fc[c].get('confidence') == 'High' else ("🟡" if fc[c].get('confidence') == 'Medium' else "🔴")
    lines.append(f"{c:<18} {rng:<28} {'📈' if trd=='Bullish' else '📉' if trd=='Bearish' else '➡️'} {trd}")

lines += [f"{'🔵' if True else ''} Confidence: High", "", "=" * 60]

# ── 3-Month ──
m3_month = MONTHS[(TODAY + timedelta(weeks=13)).month - 1]
m3_year  = (TODAY + timedelta(weeks=13)).year
lines += [
    f"📅 3-MONTH OUTLOOK — Q{((TODAY+timedelta(weeks=13)).month-1)//3+1} {m3_year}",
    f"{'Commodity':<18} {'Price Range (₦/tonne)':<28} Trend",
    "-" * 60
]
for c in DISPLAY_ORDER:
    if c not in fc: continue
    m = fc[c].get('q3month', {})
    if isinstance(m, dict) and m.get('lower') and m.get('upper'):
        rng = f"{fmtM(m['lower'])} – {fmtM(m['upper'])}"
        trd = trend_label(fc[c].get('daily'), m.get('point'))
    else:
        rng = "—"; trd = "Stable"
    lines.append(f"{c:<18} {rng:<28} {'📈' if trd=='Bullish' else '📉' if trd=='Bearish' else '➡️'} {trd}")
lines += ["🟡 Confidence: Medium", "", "=" * 60]

# ── 6-Month ──
m6_month = MONTHS[(TODAY + timedelta(weeks=26)).month - 1]
m6_year  = (TODAY + timedelta(weeks=26)).year
lines += [
    f"📅 6-MONTH OUTLOOK — H{2 if (TODAY+timedelta(weeks=26)).month > 6 else 1} {m6_year}",
    f"{'Commodity':<18} {'Price Range (₦/tonne)':<28} Trend",
    "-" * 60
]
for c in DISPLAY_ORDER:
    if c not in fc: continue
    m = fc[c].get('q6month', {})
    if isinstance(m, dict) and m.get('lower') and m.get('upper'):
        rng = f"{fmtM(m['lower'])} – {fmtM(m['upper'])}"
        trd = trend_label(fc[c].get('daily'), m.get('point'))
    else:
        rng = "—"; trd = "Stable"
    lines.append(f"{c:<18} {rng:<28} {'📈' if trd=='Bullish' else '📉' if trd=='Bearish' else '➡️'} {trd}")
lines += ["🔴 Confidence: Low — directional guidance only", "", "=" * 60]
lines.append(f"🌱 Agrolinking Research & Data | Powered by Agrolinking Intelligence System")

monthly_path = os.path.join(OUT_DIR, f"monthly_{TODAY}.txt")
with open(monthly_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"✅ Monthly outlook  → {monthly_path}")

# ════════════════════════════════════════════════════════════════════════════
# FILE 5: MARKET MOVEMENT REPORT
# ════════════════════════════════════════════════════════════════════════════
lines = [
    "📊 MARKET MOVEMENT REPORT",
    "-" * 52,
    f"📊 MARKET MOVEMENT — {header}",
    ""
]

movers_up   = []
movers_down = []
stable      = []

for c in DISPLAY_ORDER:
    if c not in fc: continue
    today_p = fc[c].get('daily')
    prev_p  = get_prev_price(c)
    pct, label, arrow = pct_change(today_p, prev_p)

    if pct is None:
        stable.append((c, today_p, label))
    elif pct > 0.5:
        movers_up.append((c, today_p, pct, label))
    elif pct < -0.5:
        movers_down.append((c, today_p, pct, label))
    else:
        stable.append((c, today_p, label))

if movers_up:
    lines.append("📈 RISING:")
    for c, p, pct, lbl in sorted(movers_up, key=lambda x: -x[2]):
        lines.append(f"  {c}: {fmt(p)}/tonne  (+{pct:.1f}%)")
    lines.append("")

if movers_down:
    lines.append("📉 FALLING:")
    for c, p, pct, lbl in sorted(movers_down, key=lambda x: x[2]):
        lines.append(f"  {c}: {fmt(p)}/tonne  ({pct:.1f}%)")
    lines.append("")

if stable:
    lines.append("➡️  STABLE:")
    for c, p, lbl in stable:
        lines.append(f"  {c}: {fmt(p)}/tonne")
    lines.append("")

lines.append(FOOTER_BRAND)
mv_path = os.path.join(OUT_DIR, f"movement_{TODAY}.txt")
with open(mv_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"✅ Movement report  → {mv_path}")

# ════════════════════════════════════════════════════════════════════════════
# FILE 6: LONG-RANGE COMBINED REPORT
# ════════════════════════════════════════════════════════════════════════════
# (already written in monthly file above — create a clean standalone)
lr_lines = [
    "=" * 60,
    f"📊 AGROLINKING LONG-RANGE OUTLOOK — {NOW.strftime('%B %Y').upper()}",
    "=" * 60, ""
]

for horizon, label, conf in [
    ('monthly', f"1-MONTH OUTLOOK — {m1_month} {m1_year}", "High"),
    ('q3month', f"3-MONTH OUTLOOK — {m3_month} {m3_year}", "Medium"),
    ('q6month', f"6-MONTH OUTLOOK — {m6_month} {m6_year}", "Low"),
]:
    icon = "🔵" if conf=="High" else ("🟡" if conf=="Medium" else "🔴")
    lr_lines += [f"{icon} {label}", f"{'Commodity':<18} {'Price Range (₦/tonne)':<28} Trend", "-"*55]
    for c in DISPLAY_ORDER:
        if c not in fc: continue
        m = fc[c].get(horizon, {})
        if isinstance(m, dict) and m.get('lower') and m.get('upper'):
            rng = f"{fmtM(m['lower'])} – {fmtM(m['upper'])}"
            trd = trend_label(fc[c].get('daily'), m.get('point'))
        else:
            rng = "—"; trd = "Stable"
        lr_lines.append(f"{c:<18} {rng:<28} {'📈' if trd=='Bullish' else '📉' if trd=='Bearish' else '➡️'} {trd}")
    lr_lines += [f"{icon} Confidence: {conf}", "", "="*60, ""]

lr_lines.append(FOOTER_BRAND)
lr_path = os.path.join(OUT_DIR, f"longrange_report_{TODAY}.txt")
with open(lr_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lr_lines))
print(f"✅ Long-range report→ {lr_path}")

# ════════════════════════════════════════════════════════════════════════════
# UPDATE MASTER CSV with today's forecasts
# ════════════════════════════════════════════════════════════════════════════
import pandas as pd
from datetime import datetime as dt

MASTER_PATH = os.path.join(BASE_DIR, "data/processed/agricom_master.csv")
master = pd.read_csv(MASTER_PATH)
master['week_start_date'] = pd.to_datetime(master['week_start_date'], format='mixed')

new_rows = []
for horizon, offset_weeks in [('daily',0), ('weekly',1), ('biweekly',2),
                               ('monthly',4), ('q3month',13), ('q6month',26)]:
    for c in DISPLAY_ORDER:
        if c not in fc: continue
        val = fc[c].get(horizon)
        if isinstance(val, dict):
            val = val.get('point')
        if val is None:
            continue
        fc_date = TODAY + timedelta(weeks=offset_weeks)
        new_rows.append({
            'commodity'         : c,
            'week_start_date'   : pd.Timestamp(fc_date),
            'price'             : round(float(val), 0),
            'currency'          : 'NGN',
            'unit'              : 'NGN/MT',
            'source'            : 'Agrolinking AI Pipeline',
            'market_type'       : 'forecast',
            'region'            : 'National',
            'record_type'       : 'forecast',
            'extraction_date'   : str(TODAY),
            'data_quality_score': 0.85,
            'is_validated'      : True,
            'notes'             : f'AI forecast generated {TODAY}'
        })

if new_rows:
    new_df = pd.DataFrame(new_rows)
    # Deduplicate: remove existing forecasts for same dates
    existing_keys = set(
        zip(master[master['record_type']=='forecast']['commodity'].astype(str),
            master[master['record_type']=='forecast']['week_start_date'].astype(str))
    )
    new_df['_key'] = list(zip(new_df['commodity'].astype(str),
                              new_df['week_start_date'].astype(str)))
    new_df = new_df[~new_df['_key'].isin(existing_keys)].drop(columns=['_key'])

    master = pd.concat([master, new_df], ignore_index=True)
    master = master.sort_values(['commodity','week_start_date']).reset_index(drop=True)
    master['price'] = master['price'].round(0)
    master.to_csv(MASTER_PATH, index=False)
    print(f"\n✅ Master CSV updated — {len(new_df)} forecast rows appended")

print(f"\n{'='*60}")
print(f"  📤 ALL OUTPUTS COMPLETE — {TODAY}")
print(f"{'='*60}\n")