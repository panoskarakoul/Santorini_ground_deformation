[README (1).md](https://github.com/user-attachments/files/30929208/README.1.md)
# Santorini InSAR — Ground Deformation Analysis
### Sentinel-1 multi-temporal InSAR Study of the 2024–2025 Volcanic Unrest

**Course:** GE7090 Advanced Remote Sensing  
**University:** Stockholm University  
**Data:** Sentinel-1 Ascending Track 029 + Descending Track 109 — March 2024 to March 2025  
**Method:** Multi-temporal DInSAR using ASF HyP3 InSAR GAMMA  
**Reference:** Replicating the InSAR component of Isken et al. (2025), *Nature*, 645(8082)

---

## Project Overview

This repository contains the Python scripts used to process and analyse Sentinel-1 InSAR data over Santorini, Greece, during the 2024–2025 volcanic unrest episode. The study replicates the InSAR methodology of Isken et al. (2025) using ascending track 029 and descending track 109, covering the same March 2024 to March 2025 period.

29 consecutive 12-day interferometric pairs were processed per track using the ASF HyP3 InSAR GAMMA cloud platform. The main outputs are a mean coherence map and a cumulative vertical displacement map covering the Santorini island group.

---

## Repository Structure

```
Santorini_InSAR/
│
├── Data_download_ascending.py    # Search ASF and submit ascending track 029
├── Data_download_descending.py   # Search ASF and submit descending track 109
├── unzip_downloads.py            # Extract downloaded zip files
├── check_projection.py           # Diagnostic — verify coordinate system
├── Check_coherence.py            # Diagnostic — verify bounding box coherence
├── check_single_pair.py          # Diagnostic — inspect per-pair displacement
├── create_AOI_box.py             # Find bounding box of coherent pixels
├── Santorini_analysis.py         # Main analysis — coherence + displacement maps
├── requirements.txt              # Python dependencies
└── README.md
```

---

## Scripts Description

### Data_download_ascending.py
Connects to ASF, searches for all Sentinel-1 SLC scenes over Santorini on ascending track 029 from March 2024 to March 2025, identifies valid 12-day interferometric pairs, submits them to HyP3 InSAR GAMMA, monitors jobs and downloads results automatically. Results saved to `hyp3_results_ascending/`.

**Run first for ascending data.**

### Data_download_descending.py
Identical to the ascending script — only the flight direction (DESCENDING), relative orbit (109), and output folders differ. Results saved to `hyp3_results_descending/`.

**Run first for descending data.**

### unzip_downloads.py
Extracts the zip files downloaded from HyP3 into their respective folders. Prints a summary of all TIF files found by type.

**Run after each download script finishes.**

### check_projection.py
Diagnostic script. Opens the first coherence TIF and prints the coordinate system (CRS), spatial extent, pixel size, and image dimensions. Confirms the data is in EPSG:32635 (WGS 1984 UTM Zone 35N) at 40m resolution.

### Check_coherence.py
Diagnostic script. Crops the first coherence file to the Santorini bounding box and checks coherence statistics — minimum, maximum, mean, and number of pixels above 0.4 and 0.6 thresholds. Confirms the bounding box is correctly placed over the islands.

### check_single_pair.py
Diagnostic script. Extracts the vertical displacement value at Nea Kameni (caldera centre) for all interferogram pairs and prints them as a table. Used to inspect individual pair values and identify outliers caused by atmospheric noise.

### create_AOI_box.py
Searches the full Sentinel-1 scene for pixels with coherence above 0.5 and calculates the UTM bounding box containing all of them. Used to define the correct crop area for the Santorini islands.

### Santorini_analysis.py
Main analysis script. Performs two computations:

1. **Mean coherence map** — averages all coherence files pixel by pixel, showing where InSAR is reliably coherent throughout the study period.
2. **Cumulative displacement map** — sums all vertical displacement files with coherence masking (threshold 0.4), showing total ground deformation from March 2024 to March 2025.

Saves GeoTIFF outputs for ArcGIS and PNG figures for reporting.

---

## Processing Parameters

| Parameter | Value |
|---|---|
| Satellite | Sentinel-1A |
| Ascending track | 029 |
| Descending track | 109 |
| Polarisation | VV |
| Temporal baseline | 12 days |
| Range looks | 10 |
| Azimuth looks | 2 |
| Output resolution | ~40m |
| Phase filter alpha | 0.6 (Goldstein) |
| DEM | Copernicus GLO-90 30m |
| Phase unwrapping | SNAPHU statistical cost |
| Coherence threshold | 0.4 |
| Processing platform | ASF HyP3 InSAR GAMMA |
| Coordinate system | EPSG:32635 — WGS 1984 UTM Zone 35N |

---

## Study Area

**Location:** Santorini, Aegean Sea, Greece  
**Bounding box (UTM Zone 35N):** Left 348246, Right 366563, Bottom 4021554, Top 4040313

---

## Data Sources

- **Sentinel-1 SLC data:** Alaska Satellite Facility (ASF) — search.asf.alaska.edu
- **InSAR processing:** ASF HyP3 On Demand — hyp3.asf.alaska.edu
- **Reference paper:** Isken et al. (2025), *Nature*, DOI: 10.1038/s41586-025-09525-7

---

## Requirements

Python 3.10 or higher is required. Install the following libraries:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install asf_search hyp3_sdk rasterio numpy matplotlib shapely scipy netCDF4 pandas pyproj
```

Or create a dedicated conda environment:

```bash
conda create -n santorini_insar python=3.10
conda activate santorini_insar
pip install -r requirements.txt
```

---

## How to Run

```bash
# Step 1 — Download ascending data (update credentials first)
python Data_download_ascending.py

# Step 1b — Download descending data (update credentials first)
python Data_download_descending.py

# Step 2 — Extract downloaded files
python unzip_downloads.py

# Step 3 — Optional diagnostics
python check_projection.py
python Check_coherence.py
python check_single_pair.py
python create_AOI_box.py

# Step 4 — Run main analysis
python Santorini_analysis.py
```

---

## Methodology

Multi-temporal Differential InSAR (DInSAR) was applied to consecutive 12-day Sentinel-1 interferometric pairs covering the Santorini volcanic unrest period of March 2024 to March 2025. Data were processed using the ASF HyP3 InSAR GAMMA cloud platform with parameters matching those of Isken et al. (2025): 10×2 range-azimuth multilooking (~40m resolution), Goldstein adaptive phase filtering (alpha=0.6), topographic phase removal using the Copernicus GLO-90 DEM, and SNAPHU statistical-cost phase unwrapping. Interferometric coherence was assessed for all pairs with pixels below 0.4 masked out before computing the cumulative displacement map.

---

## References

- Isken, M.P. et al. (2025). Volcanic crisis reveals coupled magma system at Santorini and Kolumbo. *Nature*, 645(8082), 939–945. DOI: 10.1038/s41586-025-09525-7
- Papazachos, C. et al. (2025). The Santorini 2024–2025 Volcano-Tectonic Sequence. *Geophysical Research Letters*, 52. DOI: 10.1029/2025GL115856
- Poyraz, B. et al. (2025). InSAR time-series results of the 2025 Santorini unrest. *Annals of Geophysics*, 68(6), G691. DOI: 10.4401/ag-9393
- Torres, R. et al. (2012). GMES Sentinel-1 mission. *Remote Sensing of Environment*, 120, 9–24. DOI: 10.1016/j.rse.2011.05.028
