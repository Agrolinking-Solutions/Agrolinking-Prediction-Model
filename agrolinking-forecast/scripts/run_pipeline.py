import subprocess, sys, os
from datetime import datetime

BASE_DIR    = os.path.expanduser("~/Agrolinking-Prediction-Model/agrolinking-forecast")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
TODAY       = datetime.today().date()

path = os.path.expanduser('~/Agrolinking-Prediction-Model/agrolinking-forecast/scripts/run_pipeline.py')

with open(path) as f:
    c = f.read()

PIPELINE = [
    ("01_prepare_data.py",      "Data preparation & master dataset check"),
    ("02_train_and_forecast.py","ARIMA + Prophet + XGBoost forecasting"),
    ("02b_clamp_forecasts.py", "Forecast stability clamp (new step)"),
    ("03_crossref_validate.py", "Cross-reference validation & model selection"),
    ("04_export_outputs.py",    "WhatsApp message generation & dataset update"),
]

path = os.path.expanduser('~/Agrolinking-Prediction-Model/agrolinking-forecast/scripts/run_pipeline.py')

import os
with open(path) as f:
    c = f.read()

# Find the line that calls 03_crossref and insert 02b before it
old = '02_train_and_forecast'
c2 = c.replace(
    '03_crossref_validate',
    '02b_clamp_forecasts\",\n    \"03_crossref_validate'
) if '02b_clamp_forecasts' not in c else c

with open(path, 'w') as f:
    f.write(c2)
print('Done')

print("=" * 55)
print("  🌾 AGROLINKING FORECAST PIPELINE")
print(f"  📅 {TODAY}")
print("=" * 55)

start_total = datetime.now()
failed = False

for i, (script, description) in enumerate(PIPELINE, 1):
    path = os.path.join(SCRIPTS_DIR, script)
    print(f"\n[{i}/{len(PIPELINE)}] {description}")
    print(f"      Running: {script}")
    print("-" * 55)

    start = datetime.now()
    result = subprocess.run(
        [sys.executable, path],
        capture_output=False,   # show output live
        text=True
    )
    elapsed = (datetime.now() - start).seconds

    if result.returncode != 0:
        print(f"\n❌ PIPELINE FAILED at step {i}: {script}")
        print(f"   Fix the error above and re-run: python3 run_pipeline.py")
        failed = True
        break
    else:
        print(f"\n  ✅ Step {i} complete ({elapsed}s)")

total_time = (datetime.now() - start_total).seconds

if not failed:
    print("\n" + "=" * 55)
    print("  🎉 PIPELINE COMPLETE")
    print(f"  ⏱️  Total time : {total_time}s")
    print(f"  📁 Messages   : {BASE_DIR}/outputs/whatsapp_messages/")
    print(f"  📁 Logs       : {BASE_DIR}/outputs/forecast_logs/")
    print(f"  📁 Dataset    : {BASE_DIR}/data/processed/agricom_master.csv")
    print("=" * 55)
    print("\n📋 COPY YOUR DAILY FORECAST:")
    print("-" * 55)
    msg_path = os.path.join(BASE_DIR, f"outputs/whatsapp_messages/daily_{TODAY}.txt")
    try:
        with open(msg_path, encoding='utf-8') as f:
            print(f.read())
    except FileNotFoundError:
        print(f"  Message file not found: {msg_path}")
