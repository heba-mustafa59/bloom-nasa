# BLOOM — NASA data provenance and verification protocol

**Review date:** 2026-11-15 (UTC)  
**Current status:** **PENDING**. The files are internally consistent, but their original NASA extraction and exact polygon match are **not yet independently confirmed**.

## Inventory and chain of custody

| File | Intended role | Current evidence |
| --- | --- | --- |
| `data/ndvi_annual.csv` | Annual NDVI per area, 2005–2024 | 40 rows with plausible values and valid QA-count fields; NASA source **not independently established** |
| `data/rainfall_annual.csv` | Annual GPM rainfall per area, 2005–2024 | 40 rows with 12 valid months each; NASA source **not independently established** |
| `data/study_areas.geojson` | Geographic areas (`area_a`, `area_b`) | Two closed polygons with Jericho-region coordinates; original extraction boundaries **not independently established** |
| `data/nasa_power_jericho_point_rainfall.csv` | Independent **point** reference at approx. 31.86 N, 35.45 E | 20 full-year rows by local structural checks; **not** two-area rainfall data |
| `scripts/export_nasa_data.js` | Earth Engine processing/export instructions | Source code is available; this **does not** prove it was run to create the committed CSVs |

The three primary data files were added via GitHub upload in commit `1521cf0ed78dc49a0264a1962caebdbab70f76c6` (2026-11-15T01:46:14Z). This is an **upload record**, not a NASA export audit trail. No original Earth Engine task ID, account/project, actual extraction date, or source export checksum was provided with those files.

## Declared upstream products

**Vegetation:** `MODIS/061/MOD13Q1`, NASA MODIS MOD13Q1 Collection 6.1, NDVI band. The repository script applies 0.0001 scaling, selects `SummaryQA == 0` and averages valid within-polygon 16-day composite means across the calendar year. Nominal native resolution 250 m. This method differs from a pixel-time weighted mean.

**Precipitation:** `NASA/GPM_L3/IMERG_MONTHLY_V07`, NASA GPM IMERG Monthly V07, `precipitation` band in mm/hour. The script multiplies by calendar-month hours and sums twelve spatially averaged monthly depths to mm/year. Nominal native pixel size 11,132 m. An annual total is valid only with all 12 monthly results.

Official product documentation:

- MODIS catalog: https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1
- MODIS DOI: https://doi.org/10.5067/MODIS/MOD13Q1.061
- GPM Monthly catalog: https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_MONTHLY_V07
- GPM Monthly DOI: https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07

These source pages establish what the *products* represent; they **do not authenticate the uploaded CSVs**.

## Verification steps required before setting `verification_status: verified`

- [ ] Identify the original Earth Engine project/account, exporting person, export date and task IDs.
- [ ] Obtain the exact original Earth Engine `areaA` import or equivalent saved asset; visually check polygon order, eastern `area_a` and western `area_b`, land use, and land-water/mixed pixel issues.
- [ ] Confirm the exported `study_areas.geojson` matches the polygons passed to **both** MODIS and GPM spatial aggregations (coordinate-for-coordinate or geometry-equivalent after documented normalization).
- [ ] Obtain original NDVI and rainfall export CSVs directly from completed Earth Engine tasks/Drive and compare complete tables or stable checksums with files committed to GitHub.
- [ ] Independently rerun `scripts/export_nasa_data.js` on those recorded geometries, or reproduce the reductions with a documented equivalent pipeline; reconcile any differences and missing months/composites.
- [ ] Confirm correct masking, NDVI scaling, dates, units, monthly hours including leap years, valid counts and treatment of nulls.
- [ ] Check whether small polygons share coarse GPM source pixels; disclose limits on independence and spatial precision.
- [ ] Record a named reviewer, reproduction date, source outputs, resolved discrepancies and any land-use evidence.
- [ ] Only then change `data/metadata.json` to `"verification_status": "verified"` and keep links to the supporting records.

## Publication rules

Until the steps above are complete, **do not** label the saved area-level values verified NASA observations or remove all provenance caveats merely because a CSV exists. Do not automatically copy point rainfall into polygon rows. Keep DEMO values completely separate from real-file candidates, and do not treat numeric validity checks as upstream authentication. Only make scientific comparisons using independently validated area-specific observations and matching years.

See `docs/NASA_DATA_VALIDATION_REPORT.md` for the file-level checks already completed.
