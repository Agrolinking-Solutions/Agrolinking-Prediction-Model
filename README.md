# Agrolinking Commodity Intelligence Platform

> **AI-powered daily price forecasting for Nigerian agricultural commodities.**
> Built and maintained by [Agrolinking Solutions](https://agrolinking.com).

---

## Table of Contents

1. [Overview](#1-overview)
2. [Commodities Covered](#2-commodities-covered)
3. [System Architecture](#3-system-architecture)
4. [Repository Structure](#4-repository-structure)
5. [Data Sources](#5-data-sources)
6. [Pipeline Scripts — Detailed Reference](#6-pipeline-scripts--detailed-reference)
   - [Script 01: Data Preparation](#script-01-add_new_datapy--data-preparation)
   - [Script 02: Model Training & Forecasting](#script-02-02_train_and_forecastpy--model-training--forecasting)
   - [Script 03: Cross-Reference Validation](#script-03-03_crossref_validatepy--cross-reference-validation)
   - [Script 04: Output Generation](#script-04-04_export_outputspy--output-generation)
   - [Script 05: Pipeline Runner](#script-05-run_pipelinepy--master-pipeline-runner)
7. [Forecasting Models](#7-forecasting-models)
8. [Stability Clamping System](#8-stability-clamping-system)
9. [Cross-Reference Validation Logic](#9-cross-reference-validation-logic)
10. [Macroeconomic Inflation Adjustment](#10-macroeconomic-inflation-adjustment)
11. [Output Formats](#11-output-formats)
12. [Dashboard](#12-dashboard)
13. [Setup & Installation](#13-setup--installation)
14. [Running the Pipeline](#14-running-the-pipeline)
15. [Automating with Cron](#15-automating-with-cron)
16. [Adding New Commodities](#16-adding-new-commodities)
17. [Adding New Data Points](#17-adding-new-data-points)
18. [Configuration Reference](#18-configuration-reference)
19. [Troubleshooting](#19-troubleshooting)
20. [Project History & Decisions Log](#20-project-history--decisions-log)

---

## 1. Overview

The **Agrolinking Commodity Intelligence Platform** is a production-grade, automated machine learning pipeline that generates daily price forecasts for 11 Nigerian agricultural commodities. The system runs every morning at 8AM WAT via a scheduled cron job, trains three independent forecasting models per commodity, cross-references live market data from the web, applies macroeconomic bias corrections, and produces validated price intelligence outputs in multiple formats.

### What the system does — end to end

```
Raw price data           Model training           Validation              Outputs
─────────────────   →   ──────────────────   →   ─────────────────   →   ─────────────
Agricom Africa posts     ARIMA (per commodity)    Web cross-reference     Daily WhatsApp msg
WFP Nigeria prices       Prophet (per commodity)  Model selection         Weekly forecast
Manual field data        XGBoost (per commodity)  Inflation adjustment    Long-range outlook
                         ↓                        ↓                       Dashboard charts
                         Clamp to anchor prices   Final JSON log          Forecast logs
```

### Key capabilities

| Capability | Detail |
|---|---|
| **Daily automation** | Cron job runs the full 4-script pipeline every morning |
| **11 commodities** | Hibiscus, Soybeans, Ginger, Cocoa, Cashew Nuts, Sorghum, Sesame, Beans (red), Beans (white), Maize (white), Maize (yellow) |
| **6 forecast horizons** | Daily, Weekly, 2-Week, 1-Month, 3-Month, 6-Month |
| **3 independent models** | ARIMA, Facebook Prophet, XGBoost — all run in parallel |
| **Live validation** | Web cross-reference searches real market prices before selecting the final forecast |
| **Macro-aware** | Long-range forecasts incorporate verified fuel shock and food inflation data |
| **Multiple outputs** | WhatsApp messages, JSON logs, dashboard, long-range outlook reports |

---

## 2. Commodities Covered

| Commodity | Data Source | Anchor Price (Mar 2026) | Notes |
|---|---|---|---|
| Hibiscus (Zobo) | Agricom Africa | Data-derived | Export commodity, weekly posts |
| Soybeans | Agricom Africa | Data-derived | Middle Belt supply |
| Ginger | Agricom Africa | Data-derived | Northern Nigeria |
| Cocoa | Agricom Africa | Data-derived | Southwest Nigeria |
| Cashew Nuts | Agricom Africa | Data-derived | Export commodity |
| Sorghum (Guinea Corn) | Agricom Africa | Data-derived | Staple grain, northern origin |
| Sesame | Agricom Africa | Data-derived | Export commodity |
| Beans (red / oloyin) | WFP Nigeria | ₦1,380,000/MT | Hard anchor — WFP data ends 2023 |
| Beans (white / oloyin) | WFP Nigeria | ₦1,180,000/MT | Hard anchor — WFP data ends 2023 |
| Maize (white) | WFP Nigeria | ₦355,000/MT | Hard anchor — WFP data ends 2023 |
| Maize (yellow) | WFP Nigeria | ₦365,000/MT | Hard anchor — WFP data ends 2023 |

> **Why hard anchors?** The WFP dataset ends in early 2023 when Nigerian commodity prices were
> significantly lower (maize was ~₦80K–₦120K/MT at that time). Models trained on that data will
> extrapolate to 2026 prices that are 60–70% below current market levels. Hard anchors from
> verified March 2026 market research correct this structural drift.

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AGROLINKING INTELLIGENCE PLATFORM                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  DATA LAYER                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Agricom Posts│  │  WFP Nigeria │  │  Manual field updates    │  │
│  │ (9 commod.)  │  │ (Beans/Maize)│  │  (add_new_data.py)       │  │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘  │
│         └─────────────────┴──────────────────────┐│               │
│                                                   ▼▼               │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              agricom_master.csv  (living dataset)          │    │
│  │   record_type: 'historical' | 'forecast'                   │    │
│  └─────────────────────────┬──────────────────────────────────┘    │
│                             │                                       │
│  MODELLING LAYER            ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │            02_train_and_forecast.py                         │   │
│  │                                                             │   │
│  │  ┌──────────┐   ┌────────────┐   ┌──────────────────────┐  │   │
│  │  │  ARIMA   │   │  Prophet   │   │      XGBoost         │  │   │
│  │  │ (weekly  │   │ (seasonal  │   │ (lag features,       │  │   │
│  │  │  series) │   │  trends)   │   │  rolling means)      │  │   │
│  │  └────┬─────┘   └─────┬──────┘   └──────────┬───────────┘  │   │
│  │       │               │                      │              │   │
│  │       └───────────────┴──────────────────────┘              │   │
│  │                       │                                     │   │
│  │              ┌─────────▼──────────┐                         │   │
│  │              │  STABILITY CLAMP   │  ← per-model, per-      │   │
│  │              │  (layer 1 of 2)    │    horizon, per-        │   │
│  │              └─────────┬──────────┘    commodity            │   │
│  └────────────────────────┼─────────────────────────────────── ┘   │
│                            ▼                                        │
│  VALIDATION LAYER                                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │            03_crossref_validate.py                          │   │
│  │                                                             │   │
│  │  ┌──────────────────────┐   ┌──────────────────────────┐   │   │
│  │  │  Web cross-reference │   │  Model selection logic   │   │   │
│  │  │  (DuckDuckGo search) │   │  ┌────────────────────┐  │   │   │
│  │  │  → extract NGN/MT    │   │  │ Ref found?         │  │   │   │
│  │  │  → filter vs anchor  │   │  │ YES → closest model│  │   │   │
│  │  └──────────────────────┘   │  │ NO  → 50/50        │  │   │   │
│  │                             │  │      Prophet+XGB   │  │   │   │
│  │                             │  └────────────────────┘  │   │   │
│  │                             └──────────────────────────┘   │   │
│  │                                                             │   │
│  │  ┌──────────────────────┐   ┌──────────────────────────┐   │   │
│  │  │  POST-SELECT CLAMP   │   │  INFLATION UPLIFT        │   │   │
│  │  │  (layer 2 of 2)      │   │  (long-range only)       │   │   │
│  │  └──────────────────────┘   └──────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                            │                                        │
│  OUTPUT LAYER              ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │            04_export_outputs.py                             │   │
│  │                                                             │   │
│  │  WhatsApp daily  │  Weekly msg  │  Long-range report       │   │
│  │  Movement report │  2-wk msg    │  Master CSV update       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                            │                                        │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              dashboard.py  (Streamlit)                      │   │
│  │  Daily Prices │ Long-Range │ Model Analysis │ About         │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Repository Structure

```
Agrolinking-Prediction-Model/
└── agrolinking-forecast/
    ├── dashboard.py                    # Streamlit web dashboard (5 pages)
    │
    ├── data/
    │   ├── raw/
    │   │   └── wfp_food_prices_nga.csv # WFP Nigeria source (gitignored)
    │   └── processed/
    │       └── agricom_master.csv      # Living master dataset (gitignored)
    │
    ├── scripts/
    │   ├── run_pipeline.py             # Master runner — calls all 4 scripts in order
    │   ├── 02_train_and_forecast.py    # Model training + per-model clamping
    │   ├── 03_crossref_validate.py     # Web validation + model selection + inflation
    │   ├── 04_export_outputs.py        # Generate all output files + update master CSV
    │   ├── add_new_data.py             # Manually add new weekly Agricom price posts
    │   ├── add_beans_data.py           # One-time WFP beans import (already run)
    │   └── add_maize_data.py           # One-time WFP maize import (already run)
    │
    ├── outputs/
    │   ├── forecast_logs/              # JSON logs (gitignored, regenerates daily)
    │   │   ├── model_forecasts_YYYY-MM-DD.json   # Raw 3-model outputs
    │   │   └── final_forecasts_YYYY-MM-DD.json   # Validated final outputs
    │   └── whatsapp_messages/          # Text files (gitignored, regenerates daily)
    │       ├── daily_YYYY-MM-DD.txt
    │       ├── weekly_YYYY-MM-DD.txt
    │       ├── biweekly_YYYY-MM-DD.txt
    │       ├── monthly_YYYY-MM-DD.txt
    │       ├── movement_YYYY-MM-DD.txt
    │       └── longrange_report_YYYY-MM-DD.txt
    │
    └── assets/
        └── Agrolinking_Logo.png        # Logo for dashboard
```

---

## 5. Data Sources

### 5.1 Agricom Africa (Primary — 9 commodities)

Weekly NGN/MT price publications from [Agricom Africa](https://www.instagram.com/agricomafrica/) Instagram market posts. Data covers:

- **Commodities:** Hibiscus, Soybeans, Ginger, Cocoa, Cashew Nuts, Sorghum, Sesame, Beans (red), Beans (white)
- **Format:** Price per tonne in Nigerian Naira (₦/MT)
- **Frequency:** Weekly
- **Coverage:** ~2021–present
- **How data is added:** Using `add_new_data.py` — see [Adding New Data Points](#17-adding-new-data-points)

### 5.2 WFP Nigeria Food Prices (Maize and legacy Beans)

The World Food Programme's [VAM Food Prices dataset](https://data.humdata.org/dataset/wfp-food-prices) for Nigeria.

- **File:** `data/raw/wfp_food_prices_nga.csv`
- **Commodities used:** Maize (white) — 1,549 rows; Maize (yellow) — 1,395 rows
- **Units:** Mixed — KG, 100 KG, 50 KG → normalised to NGN/MT via conversion script
- **Coverage:** Maize (white): 2003–2023 | Maize (yellow): 2014–2023
- **Important limitation:** WFP data ends in early 2023. Prices from that period
  are significantly below current 2026 market levels. This is why **hard anchors**
  are used for Maize and Beans — see [Stability Clamping System](#8-stability-clamping-system)

### 5.3 Live Web Cross-Reference (Validation)

At pipeline run time, `03_crossref_validate.py` searches DuckDuckGo for current
Nigerian market prices for each commodity. This is not a primary data source — it
is used solely for model selection validation. Results are filtered against known
anchor prices before use.

---

## 6. Pipeline Scripts — Detailed Reference

### Script 01: `add_new_data.py` — Data Preparation

**Purpose:** Adds new weekly price observations from Agricom Africa posts to the
master dataset. Run this manually each time a new Agricom post is published.

**Usage:**
```bash
python3 agrolinking-forecast/scripts/add_new_data.py
```

**What it does:**
1. Prompts for the week start date and prices for each commodity
2. Validates the new prices against the rolling historical range (flags outliers)
3. Appends validated rows to `agricom_master.csv` with `record_type = 'historical'`
4. Assigns a `data_quality_score` based on source credibility and recency
5. Reports how many rows were added and the updated dataset size

**When to run:** After each new Agricom Africa Instagram price post (typically weekly).

---

### Script 02: `02_train_and_forecast.py` — Model Training & Forecasting

**Purpose:** Trains all three models per commodity and generates raw forecast values
for all 6 horizons. Applies Layer 1 stability clamping immediately after each model
produces an output.

**Usage:**
```bash
python3 agrolinking-forecast/scripts/02_train_and_forecast.py
```

**Output:** `outputs/forecast_logs/model_forecasts_YYYY-MM-DD.json`

**What it does — step by step:**

**Data preparation:**
- Loads `agricom_master.csv`, filters to `record_type = 'historical'`
- Resamples each commodity series to clean weekly frequency using
  `resample('W-MON').median()` — this removes duplicate entries and irregular
  spacing that would corrupt ARIMA and Prophet fits

**ARIMA:**
- Runs the Augmented Dickey-Fuller test to determine the differencing order `d`
- Tries order grid: `(2,d,2)` → `(1,d,1)` → `(1,1,0)` → `(0,1,1)`
- Sanity-checks each candidate: must be positive and within 0.4×–2.5× of last price
- Falls back to a recency-weighted moving average if all ARIMA orders fail
- Generates: `daily` (1 step), `weekly` (2 steps), `biweekly` (3 steps)

**Prophet:**
- Uses multiplicative seasonality with `changepoint_prior_scale=0.06`
  (tight — prevents overfitting on short commodity series)
- FX rate is only added as a regressor if ALL mapped values are non-null after
  forward-fill — this is critical for Beans/Maize which carry no FX data in WFP
- Generates: daily, weekly, biweekly forecasts with confidence intervals
  (`yhat_lower`, `yhat_upper`) for use in long-range CI construction

**XGBoost:**
- Feature engineering: `lag_1` through `lag_4`, `roll_3`, `roll_6`, `roll_12`,
  `month`, `week`
- Regularisation: `min_child_weight=3`, `reg_alpha=0.1`, `reg_lambda=1.0`
  to prevent overfitting on the ~60–100 week training series
- Iterative multi-step forecast: each prediction feeds back as the next step's lag
- Generates: daily (1 step), weekly (2 steps), biweekly (3 steps)

**Layer 1 Clamp — applied immediately after each model, per horizon:**

```python
# Clamp architecture: value must be within ±MAX_SWING of the anchor price
# Hard anchors override data for WFP-sourced commodities
# Data-derived anchors use weighted average of last 6 historical prices

HARD_ANCHORS = {
    'Maize (white)' : 355_000,    # ₦355K/MT — March 2026 market research
    'Maize (yellow)': 365_000,    # ₦365K/MT — March 2026 market research
    'Beans (red)'   : 1_380_000,  # ₦1.38M/MT — March 2026 market research
    'Beans (white)' : 1_180_000,  # ₦1.18M/MT — March 2026 market research
}

MAX_SWING = {
    'Maize (white)' : {'daily': 0.015, 'weekly': 0.030, 'biweekly': 0.050},
    'Beans (red)'   : {'daily': 0.015, 'weekly': 0.030, 'biweekly': 0.050},
    # ... (same for Maize yellow and Beans white)
    '_default'      : {'daily': 0.040, 'weekly': 0.065, 'biweekly': 0.095},
}
```

> **Why two layers?** Layer 1 prevents wild model outputs from ever reaching the
> cross-reference step. Layer 2 (in Script 03) catches anything that slips through
> after model blending. Belt and suspenders.

---

### Script 03: `03_crossref_validate.py` — Cross-Reference Validation

**Purpose:** Takes the raw model forecasts, validates them against live market data,
selects the best model per commodity, applies inflation uplift to long-range
forecasts, and writes the final validated outputs.

**Usage:**
```bash
python3 agrolinking-forecast/scripts/03_crossref_validate.py
```

**Input:** `outputs/forecast_logs/model_forecasts_YYYY-MM-DD.json`

**Output:** `outputs/forecast_logs/final_forecasts_YYYY-MM-DD.json`

**What it does — step by step:**

**Step 1: Web cross-reference**

For each commodity, runs 2 DuckDuckGo search queries targeting current Nigerian
NGN/MT prices. Extracts price candidates using three regex patterns:
- Pattern 1: `₦X,XXX,XXX` or `NX,XXX,XXX` format
- Pattern 2: Plain 6–8 digit integers in the plausible range
- Pattern 3: USD prices → converted to NGN at current FX rate (₦1,650/USD fallback)

Candidate prices are filtered against a trust window:
- Anchored commodities (Maize, Beans): prices must be within ±30% of anchor
- Agricom commodities: prices must be within ±50% of model median

**Step 2: Model selection**

```
Web reference found?
    YES → Pick model whose daily forecast is closest to reference
          (validates reference isn't >35% from anchor before using it)

    NO  → Proven 50/50 average of Prophet + XGBoost daily values
          ARIMA is excluded from the no-reference blend
          (Prophet-only if XGBoost unavailable; XGBoost-only if Prophet failed)
```

**Step 3: Layer 2 post-selection clamp**

After selection and blending, `final_clamp()` is applied to daily, weekly, and
biweekly values before writing. Same anchor prices as Layer 1.

**Step 4: Long-range forecast construction**

Long-range forecasts (1-month, 3-month, 6-month) are built from the validated
daily value using:
1. A dampened trend derived from the weekly-to-daily ratio (capped at -0.5%/week
   downside, +1.5%/week upside — asymmetric to reflect inflationary environment)
2. A hard floor: the lower bound of all ranges is always ≥ current daily price
3. Minimum spread enforcement (4% for 1M, 7% for 3M, 10% for 6M) so ranges are
   never shown as flat zero-width lines (fixes Sorghum/Sesame zero-spread issue)
4. Inflation uplift applied on top (see Section 10)

**Output JSON structure per commodity:**
```json
{
  "Hibiscus": {
    "daily":     2640684,
    "weekly":    2577648,
    "biweekly":  2424043,
    "monthly":   { "point": 2710000, "lower": 2610000, "upper": 2810000 },
    "q3month":   { "point": 2960000, "lower": 2800000, "upper": 3050000 },
    "q6month":   { "point": 3270000, "lower": 3100000, "upper": 3500000 },
    "model":     "prophet+xgboost",
    "reference": null,
    "error_pct": null,
    "flag":      "🔄",
    "all_models": { "arima": 2593055, "prophet": 2640000, "xgboost": 2641000 },
    "confidence": "Medium",
    "inflation_adjusted": true
  }
}
```

---

### Script 04: `04_export_outputs.py` — Output Generation

**Purpose:** Reads the validated final forecasts JSON, computes daily percentage
changes versus the previous day's forecast, and generates all output files.

**Usage:**
```bash
python3 agrolinking-forecast/scripts/04_export_outputs.py
```

**Daily % change calculation:**
Searches backwards up to 7 days for the most recent `final_forecasts_YYYY-MM-DD.json`
file. This handles weekends and holidays where no pipeline ran.

```python
# Percentage change logic
def pct_change(today_price, prev_price):
    pct = (today_price - prev_price) / prev_price * 100
    if abs(pct) < 0.5:   return "➩stable"     # < 0.5% = stable
    elif pct > 0:         return f"↑ +{pct:.1f}%"
    else:                 return f"↓ {pct:.1f}%"
```

**Outputs generated:**
1. `daily_YYYY-MM-DD.txt` — Daily prices with % change vs previous day
2. `weekly_YYYY-MM-DD.txt` — Weekly forecast for next Monday
3. `biweekly_YYYY-MM-DD.txt` — 2-week forecast
4. `monthly_YYYY-MM-DD.txt` — 1-month, 3-month, 6-month outlook combined
5. `movement_YYYY-MM-DD.txt` — Market movement report (Rising / Falling / Stable)
6. `longrange_report_YYYY-MM-DD.txt` — Standalone long-range report

Also appends forecast rows to `agricom_master.csv` so the living dataset grows
daily with new forecast data points.

---

### Script 05: `run_pipeline.py` — Master Pipeline Runner

**Purpose:** Runs all 4 scripts in order. This is the only script the cron job calls.

**Usage:**
```bash
python3 agrolinking-forecast/scripts/run_pipeline.py
```

**Execution order:**
```
run_pipeline.py
    │
    ├── 02_train_and_forecast.py    (~3-5 min, Prophet trains per commodity)
    │
    ├── 03_crossref_validate.py     (~2-3 min, web requests with sleep delays)
    │
    └── 04_export_outputs.py        (~10 sec)
```

---

## 7. Forecasting Models

### ARIMA (AutoRegressive Integrated Moving Average)

**Library:** `statsmodels.tsa.arima.model.ARIMA`

**What it captures:** Autocorrelation structure in the price series — the fact that
this week's price is correlated with last week's. Handles trend via the integration
(I) component and short-term momentum via the moving average (MA) component.

**Strengths:**
- Interpretable, statistically grounded
- Works well for stable, slowly-evolving price series
- Fast to train

**Weaknesses:**
- Assumes stationarity (or achieves it via differencing)
- Does not capture seasonality explicitly
- Struggles with structural breaks (e.g., sudden fuel price shocks)
- Tends to plateau quickly for multi-step ahead forecasts

**Configuration:**
```python
# ADF test for differencing order d
# Order grid: (2,d,2) → (1,d,1) → (1,1,0) → (0,1,1)
ARIMA(series, order=order, freq='W-MON')
```

---

### Prophet (Meta / Facebook)

**Library:** `prophet`

**What it captures:** Trend changepoints, yearly seasonality, weekly seasonality,
and optional external regressors (FX rate where available). Uses a decomposable
additive/multiplicative model: `y(t) = trend(t) + seasonality(t) + regressors(t)`

**Strengths:**
- Handles harvest seasonality explicitly
- Robust to missing data and outliers
- Provides confidence intervals (`yhat_lower`, `yhat_upper`) used for long-range CI
- Performs well when trend changes are abrupt

**Weaknesses:**
- Requires minimum ~12 data points
- Can overfit on short series if `changepoint_prior_scale` is too high
- Does not accept NaN values in regressors

**Configuration:**
```python
Prophet(
    yearly_seasonality=True,
    weekly_seasonality=False,     # disabled — weekly data has no intra-week pattern
    daily_seasonality=False,
    seasonality_mode='multiplicative',
    changepoint_prior_scale=0.06, # tight — prevents overfitting
    seasonality_prior_scale=4.0,
)
```

**FX rate regressor note:** Only added if `mapped.notna().all()` — WFP-sourced
commodities (Beans, Maize) carry no FX data and will crash Prophet with a NaN
if this check is skipped.

---

### XGBoost (Extreme Gradient Boosting)

**Library:** `xgboost`, `sklearn.preprocessing.StandardScaler`

**What it captures:** Non-linear relationships between lag features and the target
price. Particularly good at capturing momentum — if prices have been rising for
3 weeks, XGBoost will tend to project continuation more aggressively than ARIMA.

**Features engineered:**
```python
lag_1, lag_2, lag_3, lag_4       # price 1–4 weeks ago
roll_3, roll_6, roll_12          # rolling 3, 6, 12-week mean (lagged by 1)
month                            # calendar month (captures seasonality indirectly)
week                             # ISO week number
```

**Strengths:**
- Captures non-linear patterns and interactions between features
- Fast inference after training
- Handles commodities with complex seasonal patterns

**Weaknesses:**
- Can extrapolate aggressively when lag features are from a different price regime
  (e.g., 2023 WFP prices as lags for 2026 forecast)
- Requires more data than ARIMA to fit reliably
- Black-box compared to ARIMA

**Configuration:**
```python
XGBRegressor(
    n_estimators=300,
    learning_rate=0.04,
    max_depth=3,            # shallow — prevents overfitting on short series
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=3,     # prevents splitting on very small node populations
    reg_alpha=0.1,          # L1 regularisation
    reg_lambda=1.0,         # L2 regularisation
    random_state=42,
)
```

---

## 8. Stability Clamping System

The clamping system is the most important production engineering feature in this
pipeline. Without it, models produce wildly inaccurate forecasts for data-limited
commodities.

### Why clamping is necessary

| Commodity | Training data ends | 2023 price | Current 2026 price | Without clamp |
|---|---|---|---|---|
| Maize (white) | Early 2023 | ~₦80K–120K/MT | ~₦355K/MT | Model forecasts ₦150–200K |
| Beans (red) | Early 2023 | ~₦400–600K/MT | ~₦1.38M/MT | Model forecasts ₦600–800K |

The model is not wrong about the historical data — it's correct for 2023. But extrapolating
3 years forward from a low-price regime produces forecasts that are 60–70% below
actual current market prices.

### Two-layer architecture

```
Model output
     │
     ▼
┌─────────────────┐
│  LAYER 1 CLAMP  │  ← Applied in 02_train_and_forecast.py
│                 │    Immediately after each model generates a value
│  anchor ± n%    │    Before anything reaches the cross-reference step
└────────┬────────┘
         │
         ▼  (cross-reference, model selection, blending)
         │
┌─────────────────┐
│  LAYER 2 CLAMP  │  ← Applied in 03_crossref_validate.py (final_clamp())
│                 │    After model selection and blending
│  anchor ± n%    │    Absolute last safety net before JSON write
└────────┬────────┘
         │
         ▼
    Final forecast
```

### Anchor price logic

```python
def get_anchor(commodity):
    # Hard market anchors for WFP-sourced commodities (override all model outputs)
    if commodity in HARD_ANCHORS:
        return HARD_ANCHORS[commodity]

    # For Agricom commodities: use weighted average of last 6 historical prices
    # More recent weeks get higher weight
    hist = master.tail(6)
    weights = [1, 2, 3, 4, 5, 6]  # recency bias
    return weighted_average(hist['price'], weights)
```

### Clamp tolerance by horizon

Tighter for data-limited commodities (Maize/Beans), wider for Agricom commodities
with fresh weekly data:

| Commodity group | Daily | Weekly | Biweekly |
|---|---|---|---|
| Maize, Beans (WFP) | ±1.5% | ±3.0% | ±5.0% |
| Agricom commodities | ±4.0% | ±6.5% | ±9.5% |

---

## 9. Cross-Reference Validation Logic

### Model selection decision tree

```
For each commodity:

    1. Run web search (2 queries per commodity)
    2. Extract price candidates from search text
    3. Filter candidates: must be within trust window of anchor
    4. Is there a credible web reference?

    ┌── YES ──────────────────────────────────────────────────────┐
    │   Is the reference within 35% of the anchor/model median?  │
    │   ├── YES → Use reference; pick model closest to reference  │
    │   └── NO  → Treat as scrape noise; fall through to NO path  │
    └─────────────────────────────────────────────────────────────┘

    ┌── NO ───────────────────────────────────────────────────────┐
    │   Both Prophet and XGBoost available?                       │
    │   ├── YES → Final = (Prophet_daily + XGBoost_daily) / 2    │
    │   ├── Prophet only → Use Prophet                           │
    │   ├── XGBoost only → Use XGBoost                           │
    │   └── Neither → Use ARIMA (last resort, flagged ⚠️)        │
    └─────────────────────────────────────────────────────────────┘
```

### Why ARIMA is excluded from the no-reference blend

ARIMA is useful for stationarity testing and as a sanity anchor, but for
short-term daily forecasting it typically underperforms Prophet and XGBoost on
commodity price series. Across all validated pipeline runs, Prophet and XGBoost
agree within 1-3% for most commodities while ARIMA often diverges significantly.
Including it in the blend would dilute the accuracy of the Prophet+XGBoost signal.

### Status flags in output JSON

| Flag | Meaning |
|---|---|
| ✅ | Web reference found; model error < 5% |
| ⚠️ | Web reference found; model error 5–15%, or only ARIMA available |
| ❌ | Web reference found; model error > 15% — use with caution |
| 🔄 | No web reference; using Prophet+XGBoost 50/50 average |

---

## 10. Macroeconomic Inflation Adjustment

### Context (verified, March 2026)

The models are trained on backward-looking historical data. When the macroeconomic
environment shifts structurally — as it did with the fuel price shock of late
February / early March 2026 — models trained on pre-shock data will produce
forecasts that are directionally wrong for the long range.

**Verified data points integrated into the long-range uplift:**

| Factor | Data | Source |
|---|---|---|
| Fuel price shock | Petrol: ₦875 → ₦1,332/litre (+52%), Feb 28 2026 | Daily Post, Guardian |
| Food inflation | NBS CPI: 8.89% Jan → 12.12% Feb 2026; beans/cowpeas specifically cited | NBS Feb 2026 CPI report |
| Annual projection | FAO: Nigeria 17.1% food inflation 2026 — highest in Africa | FAO Africa Outlook |
| Refinery | Dangote gantry ₦874/litre from ₦774; pump projected ₦980–1,000+ | Dangote press conference Mar 9 2026 |

### Uplift rates applied

**Applied ONLY to long-range forecasts (monthly, 3-month, 6-month).
Daily and weekly forecasts are left to the models.**

```python
# Base monthly uplift rates (compounding)
INFLATION_UPLIFT = {
    'monthly': 0.014,   # +1.4%/month × 1 = ~1.4%
    'q3month': 0.013,   # +1.3%/month × 3 = ~4.0%
    'q6month': 0.012,   # +1.2%/month × 6 = ~7.4%
}

# Additional uplift for NBS-cited staple commodities
# (Beans, Maize, Sorghum, Sesame, Soybeans)
EXTRA_UPLIFT = {
    'monthly': +0.005,  # → 1.9%/month total
    'q3month': +0.006,  # → 1.9%/month total
    'q6month': +0.007,  # → 1.9%/month total
}

# Export commodities (Hibiscus, Ginger, Cocoa, Cashew Nuts)
# Partially USD-priced, 45% of domestic uplift rate applies
```

### When to update these rates

These rates should be reviewed when:
- NBS releases a new monthly CPI report (monthly)
- A significant fuel price change occurs
- FAO or World Bank revises Nigeria food inflation projections
- The Iran-US-Israel conflict situation changes materially (current driver)

To update, edit the `INFLATION_UPLIFT` and `EXTRA_UPLIFT` dictionaries in
`03_crossref_validate.py` and document the source in this README.

---

## 11. Output Formats

### Daily WhatsApp Message (`daily_YYYY-MM-DD.txt`)

```
COPY YOUR DAILY FORECAST:
----------------------------------------------------
Mon 31 March, 2026 · 08:14 AM

Hibiscus ≡ ₦2,640,684/tonne  ↑ +1.4%
Soybeans ≡ ₦669,576/tonne  ➩stable
Ginger ≡ ₦9,656,814/tonne  ↓ -0.8%
...

📊 Daily Price Forecast | Agrolinking Research & Data
⚡ Powered by Agrolinking Intelligence System
```

### Long-Range Report (`monthly_YYYY-MM-DD.txt`)

```
📅 1-MONTH OUTLOOK — April 2026
Commodity          Price Range (₦/tonne)        Trend
------------------------------------------------------------
Hibiscus           ₦2.60M – ₦2.71M              📈 Bullish
Soybeans           ₦708K – ₦712K                📈 Bullish
...
🔵 Confidence: High
```

### Forecast Log (`final_forecasts_YYYY-MM-DD.json`)

Full structured JSON with all 6 horizons, model metadata, reference prices,
error percentages, and flags. Used as input to the dashboard and for
retrospective accuracy analysis.

---

## 12. Dashboard

**File:** `agrolinking-forecast/dashboard.py`

**Run:**
```bash
streamlit run agrolinking-forecast/dashboard.py
```

**Pages:**

| Page | Content |
|---|---|
| **Dashboard** | Hero section, stat cards, price trend chart (commodity selector), market movement |
| **Daily Prices** | All commodity price cards with % change chips, short-range table |
| **Long-Range** | 1M / 3M / 6M range cards, trajectory bar chart |
| **Model Analysis** | ARIMA vs Prophet vs XGBoost comparison, donut chart, commodity breakdown table, historical accuracy chart |
| **About** | Pipeline explanation, feature cards, commodities grid |

**Features:**
- Full light / dark mode toggle (CSS custom properties, Python token injection)
- Live scrolling ticker bar with price and % change
- Animated price cards with hover lift effects
- All Plotly charts adapt to dark / light mode
- Agrolinking brand colours: Dark Fern `#053307`, Japanese Laurel `#007f07`, Sunglow `#FFCE35`
- Fonts: Bricolage Grotesque (headings), Golos Text (body)

---

## 13. Setup & Installation

### Prerequisites

- Python 3.10+
- Ubuntu / WSL (Ubuntu on Windows)
- pip

### Step 1: Clone the repository

```bash
git clone https://github.com/Agrolinking-Solutions/Agrolinking-Prediction-Model.git
cd Agrolinking-Prediction-Model
```

### Step 2: Install Python dependencies

```bash
pip install pandas numpy scikit-learn xgboost prophet statsmodels \
            streamlit plotly requests beautifulsoup4 --break-system-packages
```

### Step 3: Set up directory structure

```bash
mkdir -p agrolinking-forecast/data/raw
mkdir -p agrolinking-forecast/data/processed
mkdir -p agrolinking-forecast/outputs/forecast_logs
mkdir -p agrolinking-forecast/outputs/whatsapp_messages
mkdir -p agrolinking-forecast/assets
```

### Step 4: Add your data files

- Copy `wfp_food_prices_nga.csv` to `agrolinking-forecast/data/raw/`
- Copy `agricom_master.csv` to `agrolinking-forecast/data/processed/`
- Copy `Agrolinking_Logo.png` to `agrolinking-forecast/assets/`

> These files are gitignored for privacy and security. Contact the repository
> maintainer for access to the data files.

### Step 5: Verify installation

```bash
cd ~/Agrolinking-Prediction-Model
python3 agrolinking-forecast/scripts/02_train_and_forecast.py
```

You should see model outputs printed for all 11 commodities.

---

## 14. Running the Pipeline

### Full pipeline (recommended)

```bash
python3 ~/Agrolinking-Prediction-Model/agrolinking-forecast/scripts/run_pipeline.py
```

Expected runtime: **5–9 minutes** (Prophet trains a separate model per commodity)

### Individual scripts

```bash
# Step 1: Model training only
python3 agrolinking-forecast/scripts/02_train_and_forecast.py

# Step 2: Cross-reference validation only (requires step 1 to have run today)
python3 agrolinking-forecast/scripts/03_crossref_validate.py

# Step 3: Generate outputs only (requires step 2 to have run today)
python3 agrolinking-forecast/scripts/04_export_outputs.py
```

### Run the dashboard

```bash
streamlit run agrolinking-forecast/dashboard.py
# Opens at http://localhost:8501
```

---

## 15. Automating with Cron

The pipeline runs automatically every day at 8:00 AM WAT (UTC+1).

**View the current cron schedule:**
```bash
crontab -l
```

**Expected entry:**
```
0 8 * * * /usr/bin/python3 /home/john/Agrolinking-Prediction-Model/agrolinking-forecast/scripts/run_pipeline.py >> /home/john/Agrolinking-Prediction-Model/pipeline.log 2>&1
```

**To add or edit the cron job:**
```bash
crontab -e
```

**To check the latest pipeline log:**
```bash
tail -50 ~/Agrolinking-Prediction-Model/pipeline.log
```

**To manually trigger today's pipeline outside the schedule:**
```bash
python3 ~/Agrolinking-Prediction-Model/agrolinking-forecast/scripts/run_pipeline.py
```

---

## 16. Adding New Commodities

To add a new commodity to the forecasting pipeline:

**Step 1: Add historical data**

Create a data import script (following the pattern of `add_beans_data.py` or
`add_maize_data.py`). The new commodity's price rows must be in NGN/MT and
appended to `agricom_master.csv` with `record_type = 'historical'`.

**Step 2: Add to the commodity list in all scripts**

Each pipeline script has a `DISPLAY_ORDER` or `COMMODITIES` list. Add the new
commodity name consistently across:
- `04_export_outputs.py` — `DISPLAY_ORDER` list
- `dashboard.py` — `COMMODITIES` list and `DOTS` colour dictionary

**Step 3: Configure anchor price and clamp (if data-limited)**

If the historical data for the new commodity is old or sparse, add an entry
to `HARD_ANCHORS` and `MAX_SWING` in `02_train_and_forecast.py`.

**Step 4: Add cross-reference search terms**

Add the new commodity's search queries to `COMMODITY_CONFIG` in
`03_crossref_validate.py` and set its inflation sensitivity group
(`HIGH_FUEL_SENSITIVITY` or `LOW_FUEL_SENSITIVITY`).

**Step 5: Add to dashboard dot colours**

```python
DOTS = {
    ...
    'New Commodity': '#HEX_COLOR',
}
```

---

## 17. Adding New Data Points

When a new Agricom Africa price post is published:

```bash
python3 ~/Agrolinking-Prediction-Model/agrolinking-forecast/scripts/add_new_data.py
```

Follow the prompts. The script will ask for:
- Week start date (Monday of the relevant week, format: YYYY-MM-DD)
- Price per tonne in NGN for each commodity in the Agricom post

After adding data, run the full pipeline to generate updated forecasts:

```bash
python3 ~/Agrolinking-Prediction-Model/agrolinking-forecast/scripts/run_pipeline.py
```

---

## 18. Configuration Reference

### Key configuration locations

| Setting | File | Variable |
|---|---|---|
| Hard anchor prices | `02_train_and_forecast.py` | `HARD_ANCHORS` |
| Daily/weekly/biweekly clamp limits | `02_train_and_forecast.py` | `MAX_SWING` |
| Web search queries per commodity | `03_crossref_validate.py` | `COMMODITY_CONFIG` |
| Reference price trust window | `03_crossref_validate.py` | `REF_TRUST` |
| Post-selection clamp limits | `03_crossref_validate.py` | `POST_CLAMP` |
| Inflation uplift rates | `03_crossref_validate.py` | `INFLATION_UPLIFT` |
| Extra uplift for staples | `03_crossref_validate.py` | apply_inflation_uplift() |
| FX rate fallback | `03_crossref_validate.py` | `FX_RATE` |
| Commodity display order | `04_export_outputs.py` | `DISPLAY_ORDER` |
| Dashboard commodities | `dashboard.py` | `COMMODITIES`, `DOTS` |

### Updating anchor prices

When market research indicates the current anchor prices are materially wrong:

1. Update `HARD_ANCHORS` in `02_train_and_forecast.py`
2. Update `ANCHORS` in `03_crossref_validate.py` (must match)
3. Document the update in this README with the date and source

### Updating inflation rates

When NBS CPI data is released or a new fuel price event occurs:

1. Update `INFLATION_UPLIFT` in `03_crossref_validate.py`
2. Update the comment block with the new data source and date
3. Document the update in the [Project History](#20-project-history--decisions-log) section below

---

## 19. Troubleshooting

### Prophet fails with `NaN in column 'fx_rate'`

**Cause:** A commodity from WFP (Beans or Maize) has no FX rate data.
The fx_rate regressor guard is failing.

**Fix:** Confirm `02_train_and_forecast.py` contains the safe fx_rate check:
```python
if mapped.notna().all():
    weekly['fx_rate'] = mapped.values
    has_fx = True
```
If the check is missing, replace `02_train_and_forecast.py` with the latest version.

---

### Maize or Beans showing wildly low prices (e.g., ₦180K–₦250K)

**Cause:** Clamping is not being applied. The clamp function is defined but
not being called, or the anchor prices are wrong.

**Diagnosis:**
```bash
python3 -c "
import json, os
from datetime import date
logs = os.path.expanduser('~/Agrolinking-Prediction-Model/agrolinking-forecast/outputs/forecast_logs')
with open(f'{logs}/model_forecasts_{date.today()}.json') as f:
    d = json.load(f)
for c in ['Maize (white)', 'Maize (yellow)', 'Beans (red)', 'Beans (white)']:
    if c in d:
        print(c, d[c].get('arima',{}).get('daily'), d[c].get('prophet',{}).get('daily'), d[c].get('xgboost',{}).get('daily'))
"
```

If the model_forecasts values are already correct but final_forecasts are wrong,
the issue is in `03_crossref_validate.py`. If model_forecasts themselves are low,
the issue is in `02_train_and_forecast.py`.

---

### Daily % change showing blank or "First forecast"

**Cause:** No previous `final_forecasts_YYYY-MM-DD.json` file exists to compare
against (first run, or gap in pipeline execution).

**Expected behaviour:** The system searches 7 days back. If no previous file is
found, it shows "First forecast". This resolves automatically once the pipeline
has run on at least two consecutive days.

---

### Pipeline completes but output files are empty / missing

**Cause:** Script 03 failed silently, so Script 04 has no input to read.

**Diagnosis:**
```bash
ls -la ~/Agrolinking-Prediction-Model/agrolinking-forecast/outputs/forecast_logs/ | tail -10
```

Check whether both `model_forecasts_TODAY.json` and `final_forecasts_TODAY.json`
exist. If only `model_forecasts` exists, re-run Script 03:

```bash
python3 ~/Agrolinking-Prediction-Model/agrolinking-forecast/scripts/03_crossref_validate.py
```

---

### Dashboard shows no data

**Cause:** No `final_forecasts_YYYY-MM-DD.json` exists in the forecast_logs
directory for any recent date.

**Fix:** Run the full pipeline at least once:
```bash
python3 ~/Agrolinking-Prediction-Model/agrolinking-forecast/scripts/run_pipeline.py
```

---

## 20. Project History & Decisions Log

This section documents key architectural decisions and why they were made.
Useful context for anyone maintaining or extending the system.

---

**2026-03 | Added Maize (white) and Maize (yellow)**
Source: WFP Nigeria Food Prices dataset (wfp_food_prices_nga.csv)
Unit normalisation: KG / 100 KG / 50 KG → NGN/MT via conversion script
Decision: Both varieties added as separate commodities given the meaningful
price differential (yellow typically 2-3% higher than white).

---

**2026-03 | Introduced hard market anchors for Maize and Beans**
Problem: WFP data ends 2023 at prices ~60-70% below current market levels.
Models trained on 2023 data forecast 2026 prices of ₦150-200K for maize
when the real market is ₦330K-₦380K.
Decision: Hard anchors from verified March 2026 market research. Anchors
are applied as clamp centres rather than replacing model outputs entirely,
preserving model signal within a bounded range.
Anchors set: Maize white ₦355K, Maize yellow ₦365K, Beans red ₦1.38M, Beans white ₦1.18M.

---

**2026-03 | Adopted two-layer clamping architecture**
Problem: Single post-processing clamp was not sufficient — model outputs
were so far from reality that blending them first and then clamping still
produced wrong results.
Decision: Layer 1 applied immediately inside each model's output loop in
Script 02. Layer 2 applied after model selection in Script 03. This ensures
wild values never propagate through the pipeline.

---

**2026-03 | Fixed Prophet NaN crash for WFP commodities**
Problem: WFP-sourced commodities (Beans, Maize) have no fx_rate column.
Old code added fx_rate as a regressor without checking for NaN, crashing
Prophet for these commodities.
Fix: Added guard `if mapped.notna().all()` before using fx_rate as regressor.

---

**2026-03 | Changed no-reference model selection to 50/50 Prophet+XGBoost**
Problem: Multiple experimental approaches (consensus scoring, hybrid blending,
anchor pull) all produced more volatile results than the simple average.
Decision: Reverted to proven simple 50/50 average of Prophet and XGBoost.
ARIMA excluded from the blend. This was the most stable approach across all
tested commodity-date combinations.

---

**2026-03 | Added macroeconomic inflation uplift to long-range forecasts**
Problem: Models trained on 2024-2025 data when food inflation was declining
produced flat or declining long-range forecasts. This is wrong in the current
environment: petrol rose from ₦875 to ₦1,332/litre on Feb 28 2026; NBS
food inflation rose from 8.89% to 12.12% in Feb 2026; FAO projects 17.1%
Nigeria food inflation for 2026.
Decision: Apply verified monthly compounding uplift to long-range forecasts
only. Daily and weekly forecasts remain model-driven (no uplift applied).
Differential rates: staple commodities (full rate) vs export commodities (45%).

---

**2026-03 | Enforced minimum CI spread for Sorghum and Sesame**
Problem: These commodities had very tight Prophet CIs (near-zero spread)
because their historical prices were stable. This produced 1-month and
6-month ranges like "₦283K–₦283K" — useless for decision-making.
Fix: Enforce minimum spread percentages: 4% for 1M, 7% for 3M, 10% for 6M.
The lower bound is also floored at the current daily price.

---

*Maintained by John Olamide Fashola — Data Analyst & ML Engineer, Agrolinking Solutions*
*Last updated: April 2026*