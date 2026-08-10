import zipfile
import os
from pathlib import Path

RESULTS_DIR = r"C:\Projects\santorini_insar\hyp3_results"

print("=" * 60)
print("Unzipping HyP3 results")
print("=" * 60)
print(f"Results folder: {RESULTS_DIR}\n")

pair_folders = sorted([
    f for f in Path(RESULTS_DIR).iterdir() if f.is_dir()])

print(f"Found {len(pair_folders)} pair folders\n")

extracted_count = 0
skipped_count = 0
error_count = 0
all_tif_files = []

for folder in pair_folders:
    zip_files = list(folder.glob("*.zip"))

    if not zip_files:
        print(f"  NO ZIP FOUND: {folder.name}")
        continue

    zip_path = zip_files[0]

    existing_tifs = list(folder.rglob("*.tif"))
    if existing_tifs:
        print(f"  Already extracted: {folder.name} "
              f"({len(existing_tifs)} TIF files)")
        skipped_count += 1
        all_tif_files.extend(existing_tifs)
        continue

    print(f"  Extracting: {folder.name}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(folder)

        tif_files = list(folder.rglob("*.tif"))
        print(f"    Done — {len(tif_files)} TIF files extracted")
        extracted_count += 1
        all_tif_files.extend(tif_files)

    except Exception as e:
        print(f"    ERROR: {e}")
        error_count += 1

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Folders processed:  {len(pair_folders)}")
print(f"Newly extracted:    {extracted_count}")
print(f"Already existed:    {skipped_count}")
print(f"Errors:             {error_count}")
print(f"\nTotal TIF files found: {len(all_tif_files)}")

tif_types = {}
for tif in all_tif_files:
    name = tif.name
    for suffix in ['vert_disp', 'corr', 'unw_phase', 'wrapped_phase',
                   'dem', 'inc_map', 'lv_theta', 'lv_phi', 'los_disp']:
        if suffix in name:
            tif_types[suffix] = tif_types.get(suffix, 0) + 1
            break

print("\nFiles by type:")
for file_type, count in sorted(tif_types.items()):
    print(f"  {file_type:<20} {count} files")

print("\n" + "=" * 60)
print("Unzipping complete. Ready for analysis.")
print("=" * 60)