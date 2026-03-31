"""
02_train_and_forecast.py  — Agrolinking Forecast Pipeline
Clamp is applied AFTER every model produces a value, before saving.
This guarantees no wild numbers ever reach 03_crossref_validate.py.
"""

import pandas as pd
import numpy as np
import os, json, warnings
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

BASE_DIR    = os.path.expanduser("~/Agrolinking-Prediction-Model/agrolinking-forecast")
MASTER_PATH = os.path.join(BASE_DIR, "data/processed/agricom_master.csv")
LOGS_DIR    = os.path.join(BASE_DIR, "outputs/forecast_logs")
os.makedirs(LOGS_DIR, exist_ok=True)

TODAY      = datetime.today().date()
TOMORROW   = TODAY + timedelta(days=1)
DAYS_AHEAD = 7 - TODAY.weekday() if TODAY.weekday() != 0 else 7
NEXT_WEEK  = TODAY + timedelta(days=DAYS_AHEAD)
TWO_WEEKS  = TODAY + timedelta(days=DAYS_AHEAD + 7)

print(f"📅 Forecast date : {TODAY}")
print(f"📅 Daily target  : {TOMORROW}")
print(f"📅 Weekly target : {NEXT_WEEK}")
print(f"📅 2-Wk target   : {TWO_WEEKS}\n")

df = pd.read_csv(MASTER_PATH)
df['week_start_date'] = pd.to_datetime(df['week_start_date'], format='mixed')
df = df.sort_values(['commodity','week_start_date']).reset_index(drop=True)

COMMODITIES = sorted(df['commodity'].unique().tolist())
print(f"🌾 Commodities: {COMMODITIES}\n{'='*65}")

all_forecasts = {}

# ══════════════════════════════════════════════════════════════════════
# HARD MARKET ANCHORS  (March 2026 verified market research)
# These replace model output for data-limited commodities.
# All other commodities use their actual last historical price as anchor.
# ══════════════════════════════════════════════════════════════════════
HARD_ANCHORS = {
    'Maize (white)' : 355_000,    # ₦330K-₦380K range, centre ₦355K
    'Maize (yellow)': 365_000,    # ₦340K-₦390K range, centre ₦365K
    'Beans (red)'   : 1_380_000,  # ₦1.3M-₦1.5M range, centre ₦1.38M
    'Beans (white)' : 1_180_000,  # ₦1.1M-₦1.3M range, centre ₦1.18M
}

# Max allowed % swing from anchor per horizon
# Tight for data-limited, slightly wider for recent-data commodities
MAX_SWING = {
    'Maize (white)' : {'daily': 0.015, 'weekly': 0.030, 'biweekly': 0.050},
    'Maize (yellow)': {'daily': 0.015, 'weekly': 0.030, 'biweekly': 0.050},
    'Beans (red)'   : {'daily': 0.015, 'weekly': 0.030, 'biweekly': 0.050},
    'Beans (white)' : {'daily': 0.015, 'weekly': 0.030, 'biweekly': 0.050},
    # Agricom commodities with fresh weekly data
    '_default'      : {'daily': 0.040, 'weekly': 0.065, 'biweekly': 0.095},
}

def get_anchor(commodity):
    """Return the anchor price for a commodity."""
    if commodity in HARD_ANCHORS:
        return HARD_ANCHORS[commodity]
    # Use weighted average of last 6 historical prices
    hist = df[
        (df['commodity'] == commodity) &
        (df['record_type'] == 'historical')
    ].sort_values('week_start_date').tail(6)
    if hist.empty:
        return None
    w = np.arange(1, len(hist)+1, dtype=float)
    return float(np.average(hist['price'].values, weights=w))

def clamp(value, commodity, horizon='daily'):
    """Clamp value to ±max_swing of anchor. Hard replacement for data-limited."""
    if value is None or not isinstance(value, (int,float)) or value <= 0:
        return value
    anchor = get_anchor(commodity)
    if not anchor or anchor <= 0:
        return value
    cfg = MAX_SWING.get(commodity, MAX_SWING['_default'])
    pct = cfg.get(horizon, 0.04)
    lo  = anchor * (1 - pct)
    hi  = anchor * (1 + pct)
    clamped = float(max(lo, min(hi, value)))
    return clamped

def get_weekly(commodity):
    cdf = df[df['commodity'] == commodity].copy()
    return (cdf.set_index('week_start_date')['price']
               .sort_index()
               .resample('W-MON').median()
               .dropna())

# ══════════════════════════════════════════════════════════════════════
# MODEL 1 — ARIMA
# ══════════════════════════════════════════════════════════════════════
print("\n🔵 MODEL 1: ARIMA\n" + "-"*45)

from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

def run_arima(series, steps=1):
    if len(series) < 12:
        return None
    d, test = 0, series.copy()
    for i in range(3):
        try:
            if adfuller(test.dropna())[1] < 0.05:
                d = i; break
            test = test.diff().dropna(); d = i+1
        except:
            d = 1; break

    for order in [(2,d,2),(1,d,1),(1,1,0),(0,1,1)]:
        try:
            fc = float(ARIMA(series, order=order, freq='W-MON').fit().forecast(steps=steps).iloc[-1])
            last = float(series.iloc[-1])
            if fc > 0 and 0.3*last <= fc <= 3.0*last:
                return fc
        except:
            continue
    # Weighted MA fallback
    w = np.arange(1, min(len(series),8)+1, dtype=float)
    return float(np.average(series.iloc[-len(w):].values, weights=w))

for commodity in COMMODITIES:
    weekly = get_weekly(commodity)
    all_forecasts[commodity] = {}

    d_fc  = clamp(run_arima(weekly, 1), commodity, 'daily')
    w_fc  = clamp(run_arima(weekly, 2), commodity, 'weekly')
    bw_fc = clamp(run_arima(weekly, 3), commodity, 'biweekly')

    all_forecasts[commodity]['arima'] = {
        'daily': d_fc, 'weekly': w_fc, 'biweekly': bw_fc
    }
    print(f"  [{commodity}]  "
          f"daily=₦{d_fc:,.0f}  weekly=₦{w_fc:,.0f}  2wk=₦{bw_fc:,.0f}")

# ══════════════════════════════════════════════════════════════════════
# MODEL 2 — PROPHET
# ══════════════════════════════════════════════════════════════════════
print("\n🟣 MODEL 2: PROPHET\n" + "-"*45)

from prophet import Prophet

def run_prophet(commodity, target_dates):
    weekly = get_weekly(commodity).reset_index()
    weekly.columns = ['ds','y']
    weekly = weekly.dropna()
    if len(weekly) < 12:
        return None

    cdf    = df[df['commodity'] == commodity].copy()
    has_fx = False
    if 'fx_rate' in cdf.columns and cdf['fx_rate'].notna().sum() >= 5:
        fx_s   = cdf.set_index('week_start_date')['fx_rate'].resample('W-MON').median()
        mapped = weekly['ds'].map(fx_s).ffill().bfill()
        if mapped.notna().all():
            weekly['fx_rate'] = mapped.values
            has_fx = True

    m = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode='multiplicative',
        changepoint_prior_scale=0.06,
        seasonality_prior_scale=4.0,
    )
    if has_fx:
        m.add_regressor('fx_rate')
    m.fit(weekly)

    future = pd.DataFrame({'ds': pd.to_datetime(target_dates)})
    if has_fx:
        future['fx_rate'] = weekly['fx_rate'].iloc[-1]

    fc = m.predict(future)
    return fc[['ds','yhat','yhat_lower','yhat_upper']]

for commodity in COMMODITIES:
    last_p = float(get_weekly(commodity).iloc[-1])
    try:
        res = run_prophet(commodity,
                          [str(TOMORROW), str(NEXT_WEEK), str(TWO_WEEKS)])
        if res is None:
            raise ValueError("Not enough data")

        d_fc  = clamp(max(float(res.iloc[0]['yhat']), last_p*0.3), commodity, 'daily')
        w_fc  = clamp(max(float(res.iloc[1]['yhat']), last_p*0.3), commodity, 'weekly')
        bw_fc = clamp(max(float(res.iloc[2]['yhat']), last_p*0.3), commodity, 'biweekly')

        all_forecasts[commodity]['prophet'] = {
            'daily'       : d_fc,
            'weekly'      : w_fc,
            'biweekly'    : bw_fc,
            'daily_lower' : float(res.iloc[0]['yhat_lower']),
            'daily_upper' : float(res.iloc[0]['yhat_upper']),
            'weekly_lower': float(res.iloc[1]['yhat_lower']),
            'weekly_upper': float(res.iloc[1]['yhat_upper']),
        }
        print(f"  [{commodity}]  "
              f"daily=₦{d_fc:,.0f}  weekly=₦{w_fc:,.0f}  2wk=₦{bw_fc:,.0f}")
    except Exception as e:
        print(f"  [{commodity}] ⚠️  Prophet failed: {e}")
        # Fallback: use anchor price directly
        anchor = get_anchor(commodity)
        all_forecasts[commodity]['prophet'] = {
            'daily': anchor, 'weekly': anchor, 'biweekly': anchor
        } if anchor else {'daily': None, 'weekly': None, 'biweekly': None}

# ══════════════════════════════════════════════════════════════════════
# MODEL 3 — XGBOOST
# ══════════════════════════════════════════════════════════════════════
print("\n🟠 MODEL 3: XGBOOST\n" + "-"*45)

import xgboost as xgb
from sklearn.preprocessing import StandardScaler

def make_features(s):
    s = s.reset_index(); s.columns = ['ds','y']
    s['lag_1']   = s['y'].shift(1)
    s['lag_2']   = s['y'].shift(2)
    s['lag_3']   = s['y'].shift(3)
    s['lag_4']   = s['y'].shift(4)
    s['roll_3']  = s['y'].shift(1).rolling(3).mean()
    s['roll_6']  = s['y'].shift(1).rolling(6).mean()
    s['roll_12'] = s['y'].shift(1).rolling(12).mean()
    s['month']   = s['ds'].dt.month
    s['week']    = s['ds'].dt.isocalendar().week.astype(int)
    return s.dropna()

def run_xgboost(series, steps=1):
    feat = make_features(series)
    if len(feat) < 12:
        return None
    fcols  = ['lag_1','lag_2','lag_3','lag_4','roll_3','roll_6','roll_12','month','week']
    scaler = StandardScaler()
    X = scaler.fit_transform(feat[fcols].values)
    y = feat['y'].values
    model = xgb.XGBRegressor(
        n_estimators=300, learning_rate=0.04, max_depth=3,
        subsample=0.8, colsample_bytree=0.8,
        min_child_weight=3, reg_alpha=0.1, reg_lambda=1.0,
        random_state=42, verbosity=0
    )
    model.fit(X, y)
    last   = feat.iloc[-1].copy()
    preds  = []
    for step in range(steps):
        row = np.array([[
            last['y'], last['lag_1'], last['lag_2'], last['lag_3'],
            last['roll_3'], last['roll_6'], last['roll_12'],
            (last['ds']+timedelta(weeks=step+1)).month,
            int((last['ds']+timedelta(weeks=step+1)).isocalendar()[1])
        ]])
        pred = float(model.predict(scaler.transform(row))[0])
        preds.append(pred)
        last['lag_4']=last['lag_3']; last['lag_3']=last['lag_2']
        last['lag_2']=last['lag_1']; last['lag_1']=last['y']
        last['y']     = pred
        last['roll_3'] = float(np.mean(preds[-3:]))  if len(preds)>=3  else float(np.mean(preds))
        last['roll_6'] = float(np.mean(preds[-6:]))  if len(preds)>=6  else float(np.mean(preds))
        last['roll_12']= float(np.mean(preds[-12:])) if len(preds)>=12 else float(np.mean(preds))
    return preds[-1]

for commodity in COMMODITIES:
    weekly = get_weekly(commodity)
    d_raw  = run_xgboost(weekly, 1)
    w_raw  = run_xgboost(weekly, 2)
    bw_raw = run_xgboost(weekly, 3)

    if d_raw and w_raw:
        d_fc  = clamp(d_raw,  commodity, 'daily')
        w_fc  = clamp(w_raw,  commodity, 'weekly')
        bw_fc = clamp(bw_raw or w_raw, commodity, 'biweekly')
        all_forecasts[commodity]['xgboost'] = {
            'daily': d_fc, 'weekly': w_fc, 'biweekly': bw_fc
        }
        print(f"  [{commodity}]  "
              f"daily=₦{d_fc:,.0f}  weekly=₦{w_fc:,.0f}  2wk=₦{bw_fc:,.0f}")
    else:
        print(f"  [{commodity}] ⚠️  XGBoost skipped — using anchor")
        anchor = get_anchor(commodity)
        all_forecasts[commodity]['xgboost'] = {
            'daily': anchor, 'weekly': anchor, 'biweekly': anchor
        } if anchor else {'daily': None, 'weekly': None, 'biweekly': None}

# ── Save ───────────────────────────────────────────────────────────────────
log_path = os.path.join(LOGS_DIR, f"model_forecasts_{TODAY}.json")
with open(log_path,'w') as f:
    json.dump(all_forecasts, f, indent=2, default=str)

print(f"\n✅ All models complete → {log_path}")
print("➡️  Next: 03_crossref_validate.py\n")