import rasterio
import glob
import numpy as np
import os
from rasterio.windows import from_bounds

RESULTS_DIR = r"your_path"
LEFT, RIGHT, BOTTOM, TOP = 348246, 366563, 4021554, 4040313

corr_files = sorted(glob.glob(
    os.path.join(RESULTS_DIR, "**/*corr.tif"), recursive=True))

with rasterio.open(corr_files[0]) as src:
    window = from_bounds(LEFT, BOTTOM, RIGHT, TOP, src.transform)
    window = window.round_lengths().round_offsets()
    data = src.read(1, window=window).astype(np.float32)
    nodata = src.nodata
    if nodata:
        data[data == nodata] = np.nan

    print(f"Cropped shape: {data.shape}")
    print(f"Min value: {np.nanmin(data):.3f}")
    print(f"Max value: {np.nanmax(data):.3f}")
    print(f"Mean value: {np.nanmean(data):.3f}")
    print(f"Pixels above 0.4: {np.sum(data > 0.4)}")
    print(f"Pixels above 0.6: {np.sum(data > 0.6)}")
    print(f"Total valid pixels: {np.sum(~np.isnan(data))}")
    print(f"\nFull scene stats for comparison:")
    full_data = src.read(1).astype(np.float32)
    if nodata:
        full_data[full_data == nodata] = np.nan
    print(f"Full scene max coherence: {np.nanmax(full_data):.3f}")
    print(f"Full scene mean: {np.nanmean(full_data):.3f}")
