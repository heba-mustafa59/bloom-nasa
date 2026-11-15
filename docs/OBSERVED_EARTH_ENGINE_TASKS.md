# BLOOM — Earth Engine Task Evidence (User-Supplied Screenshots)

**Record date:** 2026-11-15.  
**Evidence type:** visual transcription from screenshots supplied in the project conversation; not an authenticated Earth Engine API response.  
**Branch only:** `fix/nasa-science-validation`. No application or science data files are changed by this document.

## Tasks observed in the Earth Engine Code Editor

| Export name | Task ID visible in screenshot | Phase | Started (time shown in browser) | Runtime | Evidence status |
|---|---|---|---|---|---|
| `BLOOM_study_areas` | `MHKKZ5L6AZA7IKNPMKNI3G7Q` | Completed | 2026-11-15 03:40:09 +0200 | 2 s | Screenshot shows task expanded |
| `BLOOM_rainfall_annual` | `RV2ZMQUU4ZHTLSRDFW2250MN` | Completed | 2026-11-15 03:32:16 +0200 | 8 s | Screenshot shows task expanded |
| `BLOOM_ndvi_annual` | **Not captured yet** | Completion checkmark visible; details not expanded | Unknown | Unknown | Screenshot with expanded task ID required |

The Earth Engine Code Editor header shows `bloom-514721` as the selected project in the screenshots. This label alone does **not** establish that the three tasks ran under that project, so the export project association remains pending confirmation.

The user previously reported downloading all three outputs using the completed Earth Engine tasks to a separate folder. Their local **read-only** audit displayed:

- `ndvi_annual.csv`: MATCH, 40 rows.
- `rainfall_annual.csv`: MATCH, 40 rows.
- `study_areas.geojson`: MATCH, corresponding feature IDs and ordered coordinates within 1e-9 degrees.

This was a **user-shared local console result**, not an independent rerun by the assistant. A match means the provided original file copies correspond to the repository files under the comparison rules. It does not on its own authenticate Earth Engine upstream provenance. The screenshot of the console output is in the conversation and **not stored in this repository**.

## Remaining evidence to collect without touching the BLOOM site

1. Expand `BLOOM_ndvi_annual` under **Submitted Tasks** and capture the complete task ID, phase, start date/time, and any `Source Script` / `Open in Drive` URLs.
2. In Earth Engine, open **Source Script** for each task and confirm the script version and original two-polygon `areaA` import. A screenshot of a current unsaved `New Script *` is not sufficient to prove which script was used to export.
3. Capture the original Drive URLs or file IDs for all three completed exports, and preserve the unmodified exports separately.
4. Confirm the Earth Engine project used by the actual tasks, not merely the selected project label in the Code Editor header.
5. Independently reproduce the MODIS/GPM extraction with the recorded geometry and parameters, and document any difference in values or methodology.
6. Obtain a named scientific reviewer sign-off. Only then may the team decide whether a **separate reviewed** change to `data/metadata.json` should mark a verified source.

**Decision:** Scientific provenance remains **pending**. Do not change `data/metadata.json` to `verified` or publish unsupported source-certification claims.
