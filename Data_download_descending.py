import asf_search as asf
import hyp3_sdk as hyp3
import os
import json
import time
from datetime import datetime
from pathlib import Path

# ─── UPDATE THESE ─────────────────────────────────────────────────────────────
USERNAME = "your_username_here"
PASSWORD = "your_password_here"
ROOT_DIR = r"C:\Projects\Personal_projects\Santorini_Insar"

# ─── SETTINGS ─────────────────────────────────────────────────────────────────
SETTINGS = {
    "platform":        asf.PLATFORM.SENTINEL1,
    "processingLevel": asf.PRODUCT_TYPE.SLC,
    "beamMode":        asf.BEAMMODE.IW,
    "flightDirection": asf.FLIGHT_DIRECTION.DESCENDING,  # changed
    "relativeOrbit":   109,                               # changed
    "start":           "2024-03-01",
    "end":             "2025-03-31",
    "intersectsWith":  "POLYGON((25.2 36.2, 26.0 36.2, 26.0 36.8, 25.2 36.8, 25.2 36.2))",
}

HYP3_SETTINGS = {
    "looks":                     "10x2",
    "phase_filter_parameter":    0.6,
    "include_dem":               True,
    "include_inc_map":           True,
    "include_look_vectors":      True,
    "include_displacement_maps": True,
    "include_wrapped_phase":     True,
    "apply_water_mask":          False,
}

MAX_TEMPORAL_DAYS = 12
MIN_TEMPORAL_DAYS = 6

folders = {
    "scenes":  Path(ROOT_DIR) / "scenes_descending",      # changed
    "results": Path(ROOT_DIR) / "hyp3_results_descending", # changed
}
for path in folders.values():
    path.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("Santorini InSAR — Descending Track 109")  # changed
print("March 2024 to March 2025")
print("=" * 60)

# STEP 1: SEARCH
print("\nSTEP 1: Searching ASF...")
results = asf.search(**SETTINGS)
results_sorted = sorted(results, key=lambda x: x.properties['startTime'])

seen_dates = {}
unique_scenes = []
for r in results_sorted:
    date = r.properties['startTime'][:10]
    if date not in seen_dates:
        seen_dates[date] = r
        unique_scenes.append(r)

print(f"Found {len(unique_scenes)} unique scenes")

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
        ref_date = datetime.strptime(
            ref.properties['startTime'][:10], '%Y-%m-%d')
        sec_date = datetime.strptime(
            sec.properties['startTime'][:10], '%Y-%m-%d')
        days = (sec_date - ref_date).days
        if days > MAX_TEMPORAL_DAYS:
            break
        if days >= MIN_TEMPORAL_DAYS:
            pairs.append({
                "reference": ref.properties['sceneName'],
                "secondary": sec.properties['sceneName'],
                "ref_date":  ref_date.strftime('%Y-%m-%d'),
                "sec_date":  sec_date.strftime('%Y-%m-%d'),
                "days":      days,
            })

print(f"Found {len(pairs)} unique 12-day pairs")
print(f"Credits needed: {len(pairs) * 10}")

with open(folders["scenes"] / "pairs_list.json", "w") as f:
    json.dump(pairs, f, indent=2)

# STEP 3: SUBMIT
print("\nSTEP 3: Submitting to HyP3...")
hyp3_session = hyp3.HyP3(username=USERNAME, password=PASSWORD)
print(f"Logged in as: {USERNAME}")

jobs = []
for pair in pairs:
    try:
        job = hyp3_session.submit_insar_job(
            granule1=pair["reference"],
            granule2=pair["secondary"],
            name=f"desc109_{pair['ref_date']}_{pair['sec_date']}",  # changed
            **HYP3_SETTINGS
        )
        jobs.append(job)
        print(f"  Submitted: {pair['ref_date']} → {pair['sec_date']}")
    except Exception as e:
        print(f"  FAILED: {pair['ref_date']} → {pair['sec_date']}: {e}")

print(f"\n{len(jobs)} jobs submitted.")
print("Check: https://hyp3.asf.alaska.edu")

# STEP 4: MONITOR
print("\nSTEP 4: Monitoring jobs (checking every 5 minutes)...")

while True:
    try:
        all_jobs = list(hyp3_session.find_jobs())
        desc_jobs = [j for j in all_jobs
                     if j.name and 'desc109_' in j.name.lower()]  # changed

        succeeded = sum(1 for j in desc_jobs if j.status_code == 'SUCCEEDED')
        failed    = sum(1 for j in desc_jobs if j.status_code == 'FAILED')
        pending   = sum(1 for j in desc_jobs
                       if j.status_code in ('PENDING', 'RUNNING'))

        now = datetime.now().strftime('%H:%M:%S')
        print(f"  [{now}] Total: {len(desc_jobs)} | "
              f"Succeeded: {succeeded} | "
              f"Failed: {failed} | Pending: {pending}")

        if pending == 0:
            break

    except Exception as e:
        print(f"  Error: {e}")

    time.sleep(300)

# STEP 5: DOWNLOAD
print("\nSTEP 5: Downloading results...")

downloaded = 0
skipped = 0

for job in desc_jobs:
    if job.status_code != 'SUCCEEDED':
        print(f"  SKIPPING ({job.status_code}): {job.name}")
        continue

    pair_folder = folders["results"] / job.name
    pair_folder.mkdir(exist_ok=True)

    if len(list(pair_folder.glob("*.tif"))) >= 5:
        print(f"  Already downloaded: {job.name}")
        skipped += 1
        continue

    try:
        job.download_files(location=str(pair_folder))
        print(f"  Downloaded: {job.name}")
        downloaded += 1
    except Exception as e:
        print(f"  ERROR: {job.name} — {e}")

print("\n" + "=" * 60)
print("COMPLETE")
print("=" * 60)
print(f"Downloaded: {downloaded} | Skipped: {skipped}")
print(f"Results: {folders['results']}")
print("=" * 60)