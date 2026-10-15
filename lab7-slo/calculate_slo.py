"""Compare a request log with an SLO and report the error budget.

usage: python3 calculate_slo.py [traffic-log] [slo-file]
"""
import sys

import yaml

log_path = sys.argv[1] if len(sys.argv) > 1 else "traffic-good.log"
slo_path = sys.argv[2] if len(sys.argv) > 2 else "slo.yaml"

with open(slo_path) as f:
    slo = yaml.safe_load(f)

target = float(slo["slo"]["target"])
window = str(slo["slo"]["window"])
if not window.endswith("d"):
    raise SystemExit(f"window must be in days, for example 30d (got {window})")
window_minutes = int(window[:-1]) * 24 * 60

with open(log_path) as f:
    statuses = [int(line.strip()) for line in f if line.strip()]

total = len(statuses)
if total == 0:
    raise SystemExit(f"{log_path} has no requests")
good = sum(1 for s in statuses if 100 <= s < 500)  # 000 (no response) is a failure
sli = good / total * 100

budget_pct = 100 - target
budget_minutes = window_minutes * budget_pct / 100

print(f"Service: {slo['service']}")
print(f"Total requests: {total}")
print(f"Good requests: {good}")
print(f"SLI: {sli:.2f}%")
print(f"SLO target: {target}% over {window}")
print(f"Error budget: {budget_pct:.2f}% ({budget_minutes:.1f} minutes of full outage per window)")

if sli >= target:
    print("SLO met. Safe to deploy.")
else:
    print("SLO violated. Pause feature work and fix reliability.")
    print(f"Shortfall against target: {target - sli:.2f} percentage points")
