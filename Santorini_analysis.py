import os
import glob
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import reproject, Resampling
import matplotlib.pyplot as plt
from pathlib import Path

RESULTS_DIR = r"C:\Projects\santorini_insar\hyp3_results"
MAPS_DIR    = r"C:\Projects\santorini_insar\analysis_output\maps"
PLOTS_DIR   = r"C:\Projects\santorini_insar\analysis_output\plots"

# Bounding box UTM Zone 35N — from ArcGIS shapefile
LEFT, RIGHT, BOTTOM, TOP = 348246, 366563, 4021554, 4040313

COH_THRESHOLD = 0.4

# Site coordinates UTM (easting, northing) — clicked in ArcGIS
SITES = {
    "Thirasia":   (351137, 4033369),
    "Nea_Kameni": (356294, 4029945),
    "Thira_Fira": (359590, 4031478),
}

PUBLISHED = {
    "Thirasia":   10.0,
    "Nea_Kameni": 60.0,
    "Thira_Fira": 15.0,
}

os.makedirs(MAPS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

print("=" * 60)
print("Santorini InSAR Analysis")
print("Replicating Isken et al. (2025) — Nature")
print(f"CRS: EPSG:32635 — WGS 1984 UTM Zone 35N")
print(f"Bounding box: L={LEFT} R={RIGHT} B={BOTTOM} T={TOP}")
print(f"Coherence threshold: {COH_THRESHOLD}")
print("=" * 60)

def crop_raster(filepath, left, right, bottom, top):
    with rasterio.open(filepath) as src:
        window = from_bounds(left, bottom, right, top, src.transform)
        window = window.round_lengths().round_offsets()
        data = src.read(1, window=window).astype(np.float32)
        transform = src.window_transform(window)
        profile = src.profile.copy()
        nodata = src.nodata
    if nodata is not None:
        data[data == nodata] = np.nan
    profile.update(height=data.shape[0], width=data.shape[1],
                   transform=transform, dtype='float32',
                   nodata=np.nan, count=1)
    return data, transform, profile

def get_value(data, transform, easting, northing):
    try:
        col = int((easting  - transform.c) / transform.a)
        row = int((northing - transform.f) / transform.e)
        if 0 <= row < data.shape[0] and 0 <= col < data.shape[1]:
            val = data[row, col]
            if not np.isnan(val):
                return float(val)
    except Exception:
        pass
    return None

def resample_to_ref(data, src_transform, ref_shape, ref_transform, crs):
    if data.shape == ref_shape:
        return data
    dest = np.full(ref_shape, np.nan, dtype=np.float32)
    reproject(source=data, destination=dest,
              src_transform=src_transform, src_crs=crs,
              dst_transform=ref_transform, dst_crs=crs,
              resampling=Resampling.bilinear)
    return dest

print("\nFinding TIF files...")
corr_files      = sorted(glob.glob(
    os.path.join(RESULTS_DIR, "**/*corr.tif"),      recursive=True))
vert_disp_files = sorted(glob.glob(
    os.path.join(RESULTS_DIR, "**/*vert_disp.tif"), recursive=True))

print(f"  Coherence files:    {len(corr_files)}")
print(f"  Displacement files: {len(vert_disp_files)}")

print("\nReading reference grid...")
sample, ref_transform, ref_profile = crop_raster(
    corr_files[0], LEFT, RIGHT, BOTTOM, TOP)
ref_shape = sample.shape
ref_crs   = ref_profile['crs']
print(f"  Grid: {ref_shape[0]} rows x {ref_shape[1]} cols")

# ── MEAN COHERENCE ────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 1: Computing mean coherence map...")

coh_stack = np.zeros(ref_shape, dtype=np.float64)
coh_count = np.zeros(ref_shape, dtype=np.int16)

for i, filepath in enumerate(corr_files):
    try:
        data, transform, _ = crop_raster(filepath, LEFT, RIGHT, BOTTOM, TOP)
        data = resample_to_ref(data, transform, ref_shape, ref_transform, ref_crs)
        valid = ~np.isnan(data) & (data > 0) & (data <= 1)
        coh_stack[valid] += data[valid]
        coh_count[valid] += 1
        print(f"  [{i+1:02d}/{len(corr_files)}] {os.path.basename(filepath)[:55]}")
    except Exception as e:
        print(f"  ERROR [{i+1}]: {e}")

mean_coh = np.where(coh_count > 0, coh_stack / coh_count, np.nan)
land = mean_coh[mean_coh > 0.05]
print(f"\nCoherence stats (land pixels):")
print(f"  Mean: {np.nanmean(land):.3f}")
print(f"  Max:  {np.nanmax(land):.3f}")
print(f"  Pixels above 0.4: {np.sum(mean_coh > 0.4)}")

print("\nCoherence at key locations:")
for site, (e, n) in SITES.items():
    val = get_value(mean_coh, ref_transform, e, n)
    if val is not None:
        status = "GOOD" if val >= 0.4 else "LOW"
        print(f"  {site:<15}: {val:.3f} ({status})")
    else:
        print(f"  {site:<15}: No data")

coh_tif = os.path.join(MAPS_DIR, "mean_coherence.tif")
with rasterio.open(coh_tif, 'w', **ref_profile) as dst:
    dst.write(mean_coh.astype(np.float32), 1)
print(f"\nSaved: {coh_tif}")

fig, ax = plt.subplots(figsize=(10, 9))
im = ax.imshow(mean_coh, cmap='RdYlGn', vmin=0, vmax=1,
               extent=[LEFT, RIGHT, BOTTOM, TOP], origin='upper', aspect='equal')
plt.colorbar(im, ax=ax, label='Mean Coherence (0-1)', shrink=0.8)
for site, (e, n) in SITES.items():
    ax.plot(e, n, '^', markersize=10,
            markerfacecolor='blue', markeredgecolor='white', markeredgewidth=1.5)
    ax.annotate(site.replace('_', ' '), (e, n), xytext=(5, 5),
                textcoords='offset points', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
ax.set_xlabel('Easting (m) — UTM Zone 35N')
ax.set_ylabel('Northing (m) — UTM Zone 35N')
ax.set_title('Santorini — Mean Interferometric Coherence\n'
             'March 2024 to March 2025 — Sentinel-1 Ascending Track 029',
             fontweight='bold')
ax.grid(True, alpha=0.3, linestyle='--')
plt.tight_layout()
coh_plot = os.path.join(PLOTS_DIR, "mean_coherence_map.png")
plt.savefig(coh_plot, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {coh_plot}")

# ── CUMULATIVE DISPLACEMENT ───────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: Computing cumulative displacement map...")

cum_disp  = np.zeros(ref_shape, dtype=np.float64)
cum_count = np.zeros(ref_shape, dtype=np.int16)

for i, (disp_file, corr_file) in enumerate(zip(vert_disp_files, corr_files)):
    try:
        disp, d_tr, _ = crop_raster(disp_file, LEFT, RIGHT, BOTTOM, TOP)
        coh,  c_tr, _ = crop_raster(corr_file, LEFT, RIGHT, BOTTOM, TOP)
        disp = resample_to_ref(disp, d_tr, ref_shape, ref_transform, ref_crs)
        coh  = resample_to_ref(coh,  c_tr, ref_shape, ref_transform, ref_crs)
        valid = (~np.isnan(disp)) & (~np.isnan(coh)) & (coh >= COH_THRESHOLD)
        cum_disp[valid]  += disp[valid]
        cum_count[valid] += 1
        print(f"  [{i+1:02d}/{len(vert_disp_files)}] "
              f"{os.path.basename(disp_file)[:55]}")
    except Exception as e:
        print(f"  ERROR pair {i+1}: {e}")

cum_disp_mm = np.where(cum_count >= 5, cum_disp * 1000, np.nan)

print(f"\nCumulative displacement statistics:")
print(f"  Min:  {np.nanmin(cum_disp_mm):.1f} mm")
print(f"  Max:  {np.nanmax(cum_disp_mm):.1f} mm")
print(f"  Mean: {np.nanmean(cum_disp_mm):.1f} mm")

print(f"\nDisplacement vs Nature paper:")
print(f"  {'Site':<15} {'Your result':>14} {'Published':>12} {'Difference':>12}")
print("  " + "-" * 56)
for site, (e, n) in SITES.items():
    val = get_value(cum_disp_mm, ref_transform, e, n)
    pub = PUBLISHED.get(site)
    if val is not None and pub is not None:
        print(f"  {site:<15} {val:>12.1f}mm {pub:>11.1f}mm {val-pub:>+11.1f}mm")
    else:
        print(f"  {site:<15} {'No data':>14}")

cum_tif = os.path.join(MAPS_DIR, "cumulative_displacement_mm.tif")
with rasterio.open(cum_tif, 'w', **ref_profile) as dst:
    dst.write(cum_disp_mm.astype(np.float32), 1)
print(f"\nSaved: {cum_tif}")

vmax = max(abs(np.nanpercentile(cum_disp_mm, 2)),
           abs(np.nanpercentile(cum_disp_mm, 98)))
vmax = max(vmax, 10)

fig, ax = plt.subplots(figsize=(10, 9))
im = ax.imshow(cum_disp_mm, cmap='RdBu_r', vmin=-vmax, vmax=vmax,
               extent=[LEFT, RIGHT, BOTTOM, TOP], origin='upper', aspect='equal')
plt.colorbar(im, ax=ax, label='Cumulative vertical displacement (mm)', shrink=0.8)
for site, (e, n) in SITES.items():
    val = get_value(cum_disp_mm, ref_transform, e, n)
    label = f"{site.replace('_',' ')}\n{val:.1f}mm" if val else site.replace('_',' ')
    ax.plot(e, n, '^', markersize=10,
            markerfacecolor='yellow', markeredgecolor='black', markeredgewidth=1.5)
    ax.annotate(label, (e, n), xytext=(8, 8), textcoords='offset points',
                fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
ax.set_xlabel('Easting (m) — UTM Zone 35N')
ax.set_ylabel('Northing (m) — UTM Zone 35N')
ax.set_title('Santorini — Cumulative Vertical Displacement\n'
             'March 2024 to March 2025 — Sentinel-1 Ascending Track 029\n'
             f'Coherence masked below {COH_THRESHOLD} | Isken et al. (2025)',
             fontweight='bold')
ax.grid(True, alpha=0.3, linestyle='--')
plt.tight_layout()
disp_plot = os.path.join(PLOTS_DIR, "cumulative_displacement_map.png")
plt.savefig(disp_plot, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {disp_plot}")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
print(f"Pairs processed: {len(vert_disp_files)}")
print(f"\nOutputs:")
print(f"  {coh_tif}")
print(f"  {coh_plot}")
print(f"  {cum_tif}")
print(f"  {disp_plot}")
print("\nLoad the .tif files in ArcGIS for final report maps.")
print("=" * 60)