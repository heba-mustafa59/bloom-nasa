# BLOOM — Earth Engine Task Evidence (User-Supplied Screenshots)

**Record date:** 2026-11-15.  
**Evidence type:** visual transcription from screenshots supplied in the project conversation; not an authenticated Earth Engine API response.  
**Branch only:** `fix/nasa-science-validation`. No application or science data files are changed by this document.

## Tasks observed in the Earth Engine Code Editor

| Export name | Task ID visible in screenshot | Phase | Started (time shown in browser) | Runtime | Evidence status |
|---|---|---|---|---|---|
| `BLOOM_study_areas` | `MHKKZ5L6AZA7IKNPMKNI3G7Q` | Completed | 2026-11-15 03:40:09 +0200 | 2 s | Screenshot shows task expanded |
| `BLOOM_rainfall_annual` | `RV2ZMQUU4ZHTLSRDFW2250MN` | Completed | 2026-11-15 03:32:16 +0200 | 8 s | Screenshot shows task expanded |
| `BLOOM_ndvi_annual` | `XYDXA2SARYUCONOKY3GF56G7` | Completed | 2026-11-15 01:58:20 +0200 | 3 s | Screenshot shows task expanded, ID and completed phase |

The Earth Engine Code Editor header shows `bloom-514721` as the selected project in the screenshots. This label alone does **not** establish that the three tasks ran under that project, so the export project association remains pending confirmation.

The user previously reported downloading all three outputs using the completed Earth Engine tasks to a separate folder. Their local **read-only** audit displayed:

- `ndvi_annual.csv`: MATCH, 40 rows.
- `rainfall_annual.csv`: MATCH, 40 rows.
- `study_areas.geojson`: MATCH, corresponding feature IDs and ordered coordinates within 1e-9 degrees.

This was a **user-shared local console result**, not an independent rerun by the assistant. A match means the provided original file copies correspond to the repository files under the comparison rules. It does not on its own authenticate Earth Engine upstream provenance. The screenshot of the console output is in the conversation and **not stored in this repository**.

## Export script supplied by the user (2026-11-15)

The user pasted the Google Earth Engine JavaScript source associated in the conversation with the **Source Script** review. Its **six export sections match the existing repository export-script logic** in `scripts/export_nasa_data.js`: same study-area import and order, data products, 2005–2024 period, per-year reductions, QA handling, conversion formulas, output column selectors and three `Export.table.toDrive` descriptions.

The pasted script also appends **read-only Console diagnostics** after the three export declarations: 40-row totals, recent-year filters, yearly record-count histograms, selected 2024 rows, and non-null-measurement counts. These additional `print(...)` statements do not change the exported CSV or GeoJSON computations. This is a comparison of the **text provided by the user**, not an authenticated comparison to an immutable Earth Engine task source revision.

| Reviewed property | Supplied script text |
|---|---|
| Imported geometry | `areaA` MultiPolygon; coordinate item 0 → `area_a` and item 1 → `area_b` |
| NDVI image collection | `MODIS/061/MOD13Q1`; NDVI × `0.0001`, `SummaryQA == 0`, `scale: 250` |
| NDVI annual statistic | Arithmetic mean of the valid 16-day composite spatial means for each polygon, not a pixel-by-pixel raster video |
| Precipitation collection | `NASA/GPM_L3/IMERG_MONTHLY_V07`; `precipitation` band, `scale: 11132` |
| Rainfall annual statistic | Monthly mean rate × calendar-month hours → spatial mean → sum of 12 valid months in mm/year |
| Time window | 2005–2024 inclusive (Earth Engine upper filter bound `2025-01-01`) |
| Export names | `BLOOM_ndvi_annual`, `BLOOM_rainfall_annual`, `BLOOM_study_areas` |

**Scientific interpretation:** The code is technically consistent with the study as described; this source-level review is additional provenance evidence. It does **not** independently prove the three task records executed this exact saved revision, or prove the original `areaA` geometry was the same imported object at execution time. The land-use descriptions remain unverified field labels.

## Earth Engine source-script URL supplied by user

- **User-supplied Code Editor link:** https://code.earthengine.google.com/8b38830576de84dc8d3eb6877b3dd2ac
- **Received:** 2026-11-15, in response to the request for the NDVI export task's Source Script link.
- **Review scope:** The exact URL has been recorded, but its remote content could not be fetched by the independent review tool. The previously pasted JavaScript was compared separately with the repository export logic; **do not treat the pasted text as an authenticated fetch from this URL**.
- **Task association:** **Unverified** until the link is opened directly from the completed `BLOOM_ndvi_annual` task's **Source Script** control or supported by a task detail screenshot / export record. A Code Editor **Get Link** action may share the current editor state and is not by itself a verified immutable task revision.
- **Outstanding:** Record links for rainfall and study-areas Source Script where available; capture original Drive file IDs/URLs; independently reproduce exported numbers using the original imported `areaA` and exact processing parameters.

## Remaining evidence to collect without touching the BLOOM site

1. **Completed:** All three task IDs, completed states and displayed start times are recorded from user-supplied screenshots. Confirm their association with the specific original exported files through the task details and corresponding Drive file IDs.
2. **Script text supplied + URL recorded:** The pasted export logic matches the repository script, and an Earth Engine Code Editor link is recorded above. Its remote content and direct association with the completed NDVI task have **not** been independently verified. Preserve task-specific script records and verify the original imported `areaA` geometry used at task execution.
3. Capture the original Drive URLs or file IDs for all three completed exports, and preserve the unmodified exports separately.
4. Confirm the Earth Engine project used by the actual tasks, not merely the selected project label in the Code Editor header.
5. Independently reproduce the MODIS/GPM extraction with the recorded geometry and parameters, and document any difference in values or methodology.
6. Obtain a named scientific reviewer sign-off. Only then may the team decide whether a **separate reviewed** change to `data/metadata.json` should mark a verified source.

**Decision:** Scientific provenance remains **pending**. Do not change `data/metadata.json` to `verified` or publish unsupported source-certification claims.
