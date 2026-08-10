import rasterio
import glob
import numpy as np
import os
from rasterio.windows import from_bounds

RESULTS_DIR = r"C:\Projects\santorini_insar\hyp3_results"
LEFT, RIGHT, BOTTOM, TOP = 348246, 366563, 4021554, 4040313

# Nea Kameni coordinates
EASTING, NORTHING = 356294, 4029945

vert_files = sorted(glob.glob(
    os.path.join(RESULTS_DIR, "**/*vert_disp.tif"), recursive=True))

print("Displacement at Nea Kameni for each pair:")
print(f"{'Pair':<50} {'Value (mm)':>12}")
print("-" * 65)

for f in vert_files:
    with rasterio.open(f) as src:
        window = from_bounds(LEFT, BOTTOM, RIGHT, TOP, src.transform)
        window = window.round_lengths().round_offsets()
        data = src.read(1, window=window).astype(np.float32)
        transform = src.window_transform(window)
        nodata = src.nodata
        if nodata:
            data[data == nodata] = np.nan

        col = int((EASTING  - transform.c) / transform.a)
        row = int((NORTHING - transform.f) / transform.e)

        if 0 <= row < data.shape[0] and 0 <= col < data.shape[1]:
            val = data[row, col]
            val_mm = val * 1000 if not np.isnan(val) else None
            name = os.path.basename(f)[:45]
            print(f"{name:<50} {val_mm:>11.1f}mm" if val_mm
                  else f"{name:<50} {'No data':>12}")