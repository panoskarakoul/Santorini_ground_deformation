import asf_search as asf
import hyp3_sdk as hyp3
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# ─── UPDATE THESE TWO LINES ───────────────────────────────────────────────────
USERNAME = "your_username_here"
PASSWORD = "your_password_here"
ROOT_DIR = r"the_path_you_want_to_save_it"

# ─── SETTINGS ─────────────────────────────────────────────────────────────────
SETTINGS = {
    "platform":         asf.PLATFORM.SENTINEL1,
    "processingLevel":  asf.PRODUCT_TYPE.SLC,
    "beamMode":         asf.BEAMMODE.IW,
    "flightDirection":  asf.FLIGHT_DIRECTION.ASCENDING,
    "relativeOrbit":    29,
    "start":            "2024-03-01",
    "end":              "2025-03-31",
    "intersectsWith":   "POLYGON((25.2 36.2, 26.0 36.2, 26.0 36.8, 25.2 36.8, 25.2 36.2))",
}

HYP3_SETTINGS = {
    "looks":                        "10x2",
    "phase_filter_parameter":       0.6,
    "include_dem":                  True,
    "include_inc_map":              True,
    "include_look_vectors":         True,
    "include_displacement_maps":    True,
    "include_wrapped_phase":        True,
    "apply_water_mask":             False,
}

MAX_TEMPORAL_DAYS = 12
MIN_TEMPORAL_DAYS = 6

folders = {
    "root":     Path(ROOT_DIR),
    "scenes":   Path(ROOT_DIR) / "scenes",
    "results":  Path(ROOT_DIR) / "hyp3_results",
    "analysis": Path(ROOT_DIR) / "analysis_output",
    "plots":    Path(ROOT_DIR) / "analysis_output" / "plots",
    "maps":     Path(ROOT_DIR) / "analysis_output" / "maps",
}
for path in folders.values():
    path.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("Santorini InSAR Pipeline")
print("=" * 60)

# STEP 1: SEARCH
print("\nSTEP 1: Searching ASF...")
results = asf.search(**SETTINGS)
results_sorted = sorted(results, key=lambda x: x.properties['startTime'])
print(f"Found {len(results_sorted)} scenes")

# Keep ONE scene per date
seen_dates = {}
unique_scenes = []
for r in results_sorted:
    date = r.properties['startTime'][:10]
    if date not in seen_dates:
        seen_dates[date] = r
        unique_scenes.append(r)

print(f"Unique dates: {len(unique_scenes)}")

scene_data = [{"name": r.properties['sceneName'],
               "date": r.properties['startTime'][:10]}
              for r in unique_scenes]
with open(folders["scenes"] / "scene_list.json", "w") as f:
    json.dump(scene_data, f, indent=2)

# STEP 2: FIND PAIRS
print("\nSTEP 2: Finding 12-day pairs...")
pairs = []
for i in range(len(unique_scenes)):
    for j in range(i + 1, len(unique_scenes)):
        ref = unique_scenes[i]
        sec = unique_scenes[j]
        ref_date = datetime.strptime(ref.properties['startTime'][:10], '%Y-%m-%d')
        sec_date = datetime.strptime(sec.properties['startTime'][:10], '%Y-%m-%d')
        temporal_days = (sec_date - ref_date).days
        if temporal_days > MAX_TEMPORAL_DAYS:
            break
        if temporal_days >= MIN_TEMPORAL_DAYS:
            pairs.append({
                "reference":    ref.properties['sceneName'],
                "secondary":    sec.properties['sceneName'],
                "ref_date":     ref_date.strftime('%Y-%m-%d'),
                "sec_date":     sec_date.strftime('%Y-%m-%d'),
                "temporal_days": temporal_days,
            })

print(f"Found {len(pairs)} unique 12-day pairs")
print(f"Credits needed: {len(pairs) * 10}")

with open(folders["scenes"] / "pairs_list.json", "w") as f:
    json.dump(pairs, f, indent=2)

# STEP 3: SUBMIT TO HYP3
print("\nSTEP 3: Connecting to HyP3...")
hyp3_session = hyp3.HyP3(username=USERNAME, password=PASSWORD)

try:
    user_info = hyp3_session.my_info()
    if isinstance(user_info, dict):
        credits = user_info.get('remaining_credits', 'unknown')
    else:
        credits = getattr(user_info, 'remaining_credits', 'unknown')
    print(f"Logged in as: {USERNAME}")
    print(f"Credits available: {credits}")
except Exception as e:
    print(f"Logged in as: {USERNAME}")
    print(f"Could not retrieve credits: {e}")

print(f"\nSubmitting {len(pairs)} jobs...")

jobs = []
for pair in pairs:
    try:
        job = hyp3_session.submit_insar_job(
            granule1=pair["reference"],
            granule2=pair["secondary"],
            name=f"sant_{pair['ref_date']}_{pair['sec_date']}",
            **HYP3_SETTINGS
        )
        jobs.append(job)
        print(f"  Submitted: {pair['ref_date']} → {pair['sec_date']}")
    except Exception as e:
        print(f"  FAILED: {pair['ref_date']} → {pair['sec_date']}: {e}")

print(f"\n{len(jobs)} jobs submitted.")
print("Check progress at: https://hyp3.asf.alaska.edu")
print("=" * 60)
