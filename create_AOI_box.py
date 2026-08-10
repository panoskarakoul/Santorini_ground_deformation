import rasterio
import glob
import numpy as np
import os

RESULTS_DIR = r"C:\Projects\santorini_insar\hyp3_results"

corr_files = sorted(glob.glob(
    os.path.join(RESULTS_DIR, "**/*corr.tif"), recursive=True))

with rasterio.open(corr_files[0]) as src:
    data = src.read(1).astype(np.float32)
    transform = src.transform
    nodata = src.nodata
    if nodata:
        data[data == nodata] = np.nan

    rows, cols = np.where(data > 0.5)

    if len(rows) == 0:
        print("No pixels above 0.5 found")
    else:
        eastings  = transform.c + cols * transform.a
        northings = transform.f + rows * transform.e

        print(f"High coherence pixels found: {len(rows)}")
        print(f"\nBounding box of high coherence areas (UTM metres):")
        print(f"  Left   (min easting):  {eastings.min():.0f}")
        print(f"  Right  (max easting):  {eastings.max():.0f}")
        print(f"  Bottom (min northing): {northings.min():.0f}")
        print(f"  Top    (max northing): {northings.max():.0f}")
        print(f"\nUse these in the analysis script:")
        print(f"LEFT, RIGHT, BOTTOM, TOP = "
              f"{eastings.min():.0f}, {eastings.max():.0f}, "
              f"{northings.min():.0f}, {northings.max():.0f}")