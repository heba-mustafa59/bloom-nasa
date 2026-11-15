# BLOOM — NASA Science Validation Handoff

**Branch:** `fix/nasa-science-validation` (created from `main` at commit `7a8d6330e3ebaba2db578c2c2768d5da61d31621` on 2026-11-15)

**Purpose:** close the most important scientific-documentation gap without editing the BLOOM website, map, visual design, calculation engines, original source CSV files, polygons, or metadata status.

## What is finished in this branch

- Added `scripts/validate_science.py`, an **offline, read-only** audit of the currently committed files. It checks the exact 40 NDVI rows, 40 rainfall rows, 2 Jericho-region study polygons, recorded dataset IDs, expected export-script method markers, and independently computes linear slopes to cross-check the existing trend analysis.
- The script reports annual means, endpoints, endpoint changes, linear slopes per decade, and Mann–Kendall p-values for both areas and variables. These are **statistics of the uploaded repository files**, not proof of NASA source provenance.
- An optional `--original-dir` argument compares 3 independently obtained raw export files against the repo's CSV rows and study-area geometries. Additional CSV columns such as Earth Engine's `system:index` are ignored. It fails with exit code 2 on mismatches or invalid input.
- An optional `--evidence` argument reviews fields from a separately filled evidence manifest. Typed task IDs, export links, and human attestations are **claims pending external inspection**. No automatic method may change `verification_status` to `verified`.
- Added tests that deliberately replace values and geometries in **temporary copies only** to confirm mismatches are caught. The real files are never modified.
- Added a separate branch-specific GitHub Actions workflow to exercise the audit. The existing website and pilot workflows are unchanged.

## Run without changing the site

```bash
git fetch origin
git switch fix/nasa-science-validation
python -m pip install -r requirements.txt
python -m pytest tests/test_science_validation.py -q
python scripts/validate_science.py --report /tmp/bloom_science_audit.md --json /tmp/bloom_science_audit.json
```

To use separately downloaded, **original** completed Earth Engine outputs:

```bash
python scripts/validate_science.py \
  --original-dir /path/to/original_earth_engine_exports \
  --evidence /path/to/filled_evidence.json \
  --report /tmp/bloom_science_with_source_evidence.md \
  --json /tmp/bloom_science_with_source_evidence.json
```

The original-dir folder must contain **`ndvi_annual.csv`, `rainfall_annual.csv`, and `study_areas.geojson`**. Do not copy the repo's files into that folder and claim they are an independent export. Comparison of matching files is a correspondence check, not an upstream NASA authentication. A source review requires completed task history and actual Earth Engine polygon assets.

## Original Google Earth Engine evidence required

1. Open the Earth Engine account/project used for the original exports. Record the project, completed task IDs, task status, UTC export date, links to original task outputs, and who performed the export. Keep task screenshots/logs, not just a GitHub commit.
2. Open the exact `areaA` import or saved Earth Engine asset used in **both** analyses. Confirm **polygon 0 = eastern area_a** and **polygon 1 = western area_b**, its boundaries, crop/land-use descriptions (if supported), and which coordinate geometry is used in the export.
3. Download the original NDVI, rainfall, and GeoJSON outputs of those completed tasks. Do not edit the files. Compare them using the audit's `--original-dir`.
4. Inspect NDVI scaling by 0.0001, `SummaryQA == 0`, valid composite counts, calendar-year range 2005–2024, and the spatial mean → annual mean reduction in `scripts/export_nasa_data.js`.
5. Inspect GPM IMERG Monthly V07 `precipitation` hourly-rate band, multiplication by actual month hours, all 12 valid months, and the sum in millimeters per year. Check close polygons against coarse (~11.1 km) pixels.
6. Independently rerun Earth Engine on the exact documented polygons; compare outputs and document any difference. Do not replace repository data unless the team explicitly reviews the difference and its scientific effect.
7. Obtain a reviewer sign-off (name, UTC date, methods, limitations, source links). Fill a **private copy** of `docs/EARTH_ENGINE_EVIDENCE_TEMPLATE.json` (not fake placeholder IDs).
8. Only after review, consider a separate metadata-only change from `pending` to `verified`. This branch **does not** perform that change.

## Scientific boundaries that must stay visible in the judge handoff

- Code computes trend significance (Mann–Kendall) and rate (linear slope). A trustworthy NASA instrument does **not** mean that a measured time-series trend must be statistically significant.
- The existing Mann–Kendall test does not adjust for serial autocorrelation, seasonality, or multiple comparisons. Findings are exploratory.
- Annual NDVI values are polygon averages across available MODIS composites, not per-pixel time-lapse images.
- GPM precipitation estimates are far coarser than MODIS NDVI; adjacent area rainfall values may share pixels. Rainfall alone does not establish a vegetation cause.
- Land-use names are candidate descriptions in GeoJSON, not independently verified field classifications.
- Area Advisor helps prioritize investigation; it does not determine that a parcel is more suitable for purchasing or agriculture.
- No project tool can certify the original 2026 Earth Engine run by reading an uploaded CSV without original task records.

## Exclusions and safety

**Not changed:** `ui_app.py`, `app.py`, `investigation_app.py`, `modules/ui_pages/*`, `modules/ui_components.py`, `modules/trend_analysis.py`, `modules/data_loader.py`, `modules/mystery_engine.py`, `scripts/export_nasa_data.js`, and `data/*`.

This is not a redesign, deployment, GIS re-extraction, or an independent NASA source certification. It is the reproducible checking and evidence-collection layer needed to pursue that certification.
