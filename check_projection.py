import rasterio
import glob
import os

RESULTS_DIR = r"C:\Projects\santorini_insar\hyp3_results"

corr_files = glob.glob(
    os.path.join(RESULTS_DIR, "**/*corr.tif"), recursive=True)

if not corr_files:
    print("No corr files found")
else:
    with rasterio.open(corr_files[0]) as src:
        print(f"File: {os.path.basename(corr_files[0])}")
        print(f"CRS: {src.crs}")
        print(f"Bounds: {src.bounds}")
        print(f"Width: {src.width} pixels")
        print(f"Height: {src.height} pixels")
        print(f"Transform: {src.transform}")