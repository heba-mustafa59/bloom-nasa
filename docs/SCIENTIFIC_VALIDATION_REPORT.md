# BLOOM — Scientific Validation Report (Audit of Existing Repository Values)

**Audit basis:** `data/ndvi_annual.csv`, `data/rainfall_annual.csv`, `data/study_areas.geojson`, `data/metadata.json` and the existing scientific code on `main` at SHA `7a8d6330e3ebaba2db578c2c2768d5da61d31621`. The audit executable and regression tests are available on `fix/nasa-science-validation`.

**Date:** 2026-11-15.

**Finding: scientific computations are reproducible from the uploaded files. The original NASA/Earth Engine export provenance remains unverified. The project metadata state must remain `pending`.**

## 1. Challenge objectives and project coverage

| NASA objective | Existing BLOOM capability | Scientific caveat |
| --- | --- | --- |
| Identify Earth-science variables | MODIS NDVI and GPM rainfall | Variable choice is currently restricted to two preselected variables |
| Acquire variables for a defined region | Two real-coordinate Jericho GeoJSON polygons and area-specific CSV files | Coordinates valid; proof that these exact polygons were used in Earth Engine exports is missing |
| Visualize long time series | 20 annual observations (2005–2024) per area per variable; interactive maps and plots | Annual aggregation hides seasonal behavior |
| Estimate rate of change | Linear slope per year and decade (existing `modules/trend_analysis.py`) | Linear slope summarizes a possibly nonlinear history |
| Test significance | Two-sided Mann–Kendall at α=0.05 (existing `modules/trend_analysis.py`) | Exploratory; original test does not correct for serial dependence or multiple testing |
| Compare regions | Area A versus Area B | Area-wise significant trends do **not** establish a significant difference between the slopes |
| Turn results into decisions | Area Advisor + Action Pathway | These are screening and field-check recommendations, not validated causes or land-suitability decisions |

**The core science/visualization objective is implemented in code. Dataset authenticity and export geometry matching remain the central blockers to a verified NASA data study.**

## 2. Structural checks against the repository files

- `ndvi_annual.csv`: 40 rows = 20 years × 2 areas; all NDVI values within [-1, 1]; valid composite counts present.
- `rainfall_annual.csv`: 40 rows = 20 years × 2 areas; nonnegative annual rainfall; each row indicates 12 valid months.
- `study_areas.geojson`: 2 closed polygon features with `area_a` / `area_b`; geographic coordinates around Jericho.
- `metadata.json`: `verification_status: pending`; source claims match the product IDs referenced by the export script.
- `scripts/export_nasa_data.js`: declares `MODIS/061/MOD13Q1`, `NASA/GPM_L3/IMERG_MONTHLY_V07`, NDVI scaling, QA mask and rainfall units/conversion.

These checks demonstrate **internal structure and computation**, not where the uploaded values originally came from.

## 3. Results calculated from the uploaded annual series

| Polygon | Variable | 2005 value | 2024 value | Endpoint change | Linear slope / decade | Mann–Kendall p (approx.) | Interpretation (α=0.05) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Area A | NDVI | 0.165151 | 0.351735 | +0.186584 | +0.102104 | 0.00000035 | Increasing trend supported in this series |
| Area B | NDVI | 0.263527 | 0.201508 | −0.062019 | −0.015447 | 0.3145 | No significant monotonic trend established |
| Area A | Rainfall (mm/year) | 357.544 | 304.048 | −53.496 | +0.984 mm | 0.9225 | No significant monotonic trend established |
| Area B | Rainfall (mm/year) | 370.152 | 314.256 | −55.896 | −0.718 mm | 0.9741 | No significant monotonic trend established |

**Crucial distinctions:**

- The difference between 2005 and 2024 is **not** equivalent to the fitted slope and **not** itself a significance test.
- In Area A, 2005–2024 NDVI endpoints and estimated trend rise; this does **not** prove irrigation, land use, vegetation health or any specific cause.
- Area B's endpoints decline, but its full annual NDVI series does **not** meet the prototype Mann–Kendall significance threshold.
- Rainfall slopes are near zero and non-significant despite the different endpoint rainfall values.
- The historical area ranking reversal (B higher in 2005, A higher in 2024) is a **descriptive observation**, not a between-region statistical trend-difference test.

The values in this table are **computed from the repository files**, not from an independently inspected NASA task or direct NASA API response. To reproduce using the checked-in script, run:

```bash
python scripts/validate_science.py --report /tmp/bloom_science_audit.md --json /tmp/bloom_science_audit.json
```

## 4. NASA products claimed by the project

| Product | Collection ID | Native scale | Aggregation declared in the script |
| --- | --- | --- | --- |
| MODIS NDVI (MOD13Q1 v6.1) | `MODIS/061/MOD13Q1` | ~250 m | `SummaryQA == 0`, scale 0.0001, mean of valid within-polygon composite NDVI means |
| GPM IMERG Monthly V07 | `NASA/GPM_L3/IMERG_MONTHLY_V07` | ~11.1 km | Monthly mm/hour rate × actual month hours, spatial mean per area, sum 12 months into annual mm |

**Important:** filenames, plausible values, and matching source IDs in code do not authenticate the original NASA extraction. GPM's resolution is much coarser than MODIS, and nearby polygon rainfall estimates may not be spatially independent.

### Source-code review update — 2026-11-15

The user supplied the Earth Engine JavaScript following the request to inspect the source script of the completed export tasks. The core export logic **matches** `scripts/export_nasa_data.js` as checked into GitHub (study geometry split, MODIS/GPM collections, QA and scaling, annual reductions, task names and export columns). The pasted version adds several `print()` diagnostics for record counts, coverage and 2024 values, which do not alter data generation.

This substantially clarifies the methodology actually represented in the supplied source text. Two distinct URLs have been recorded: a confirmed **Get Link** editor snapshot (https://code.earthengine.google.com/8b38830576de84dc8d3eb6877b3dd2ac), and a later link supplied following the completed NDVI task's **Source Script** instruction (https://code.earthengine.google.com/18b1cc4f75db094aa3ead046cacfac61). **Neither URL's remote contents could be fetched independently.** The second link is user-associated with the task but its exact source revision and imported `areaA` geometry remain unverified. Preserve task-specific source, asset import and Drive export IDs to close those evidentiary gaps. More details: `docs/OBSERVED_EARTH_ENGINE_TASKS.md`.

## 5. Verification items that still require human-supplied evidence

| Evidence | Current status | Needed to close |
| --- | --- | --- |
| Original Earth Engine project, task history and task IDs | **PARTIAL** — three completed task IDs and start times shown; supplied source text matches repository export logic | Preserve task-specific script revisions, project association and Drive export links; see `docs/OBSERVED_EARTH_ENGINE_TASKS.md` |
| Original completed task output CSVs | **PARTIAL** — user-shared local comparison reported MATCH for 40 NDVI rows and 40 rainfall rows | Keep original Drive task links/files and independently verify correspondence to those task IDs |
| Original `areaA` imported geometry and export match | **PARTIAL** — user-shared GeoJSON comparison reported matching IDs/coordinates; screenshot now also shows a current `areaA` MultiPolygon with two coordinate elements and index 0/1 selection | Confirm identical import coordinates at the completed task's execution or independently rerun on documented polygon coordinates |
| Earth Engine reproduction | **TASKS COMPLETED; RESULTS NOT YET COMPARED** — three rerun tasks show Completed on 2026-11-15 using frozen repository polygon coordinates | Download new rerun outputs from the isolated Drive folder and compare all 40 NDVI + 40 rainfall rows and both polygons; document Drive file links |
| Reviewer sign-off and documented field/land-use classifications | **MISSING** | Named reviewer, UTC date, methods and conclusions |

**Additional geometry screenshot (2026-11-15):** The Code Editor's Imports panel shows `var areaA: MultiPolygon, 15 vertices`, with `coordinates: List (2 elements)`. The visible script splits coordinate indexes 0/1 into `studyA` and `studyB`, and the map visually shows two polygons near Jericho. This validates the currently displayed import configuration, not the precise historical input coordinates of the completed export task. See `docs/OBSERVED_EARTH_ENGINE_TASKS.md`.

**Update on 2026-11-15:** The supplied Earth Engine screenshots document three completed export tasks. The user separately ran the original-file comparison and reported MATCH for both 40-row tables and the two polygon geometries. This strengthens the provenance trail but does not yet independently link each Drive file to its task ID or establish a reproducible rerun. See `docs/OBSERVED_EARTH_ENGINE_TASKS.md`.

**Decision: do not change `data/metadata.json` to `verified` and do not describe the uploaded polygons or annual values as independently authenticated NASA measurements yet.**

### Reproducibility workflow prepared — execution pending

A new standalone Earth Engine script, `scripts/reproduce_nasa_gee.js`, has been added on the science-only branch. It freezes the exact two polygons from the committed `study_areas.geojson`, preserves the documented MODIS/GPM reductions and exports into a **separate Drive folder** with `BLOOM_RECHECK_*` task names. The accompanying `tests/test_science_rerun_script.py` statically checks the frozen coordinates, unchanged reduction code and isolated exports. Follow `docs/SCIENCE_REPRODUCTION_RUNBOOK.md` to perform an authenticated rerun and then compare its new outputs using `scripts/validate_science.py`.

**Update after the rerun (2026-11-15):** User-supplied Earth Engine Tasks screenshot shows `BLOOM_RECHECK_ndvi_annual` (`SYAG3QOLLYCRACPFJWCSHDDQ`), `BLOOM_RECHECK_rainfall_annual` (`HSJD5S6KXFCMVYRYKIU7MDUS`) and `BLOOM_RECHECK_study_areas` (`W6GSGMBVSMYBG7LEMDX64ZCC`) all at **Completed**. This is evidence that the re-extraction tasks executed. **Fresh outputs and their numerical/geometry comparison have not yet been provided**; successful task completion alone is not a matching-output result. The remaining items must be resolved with downloaded new task outputs and reviewer evidence.

## 6. No-impact guarantee

The new verification work is confined to additions under `scripts/`, `tests/`, `docs/` and a branch-specific CI workflow. Existing Python application entry points, pages, maps, CSS, annual data tables, GeoJSON, scientific engines and metadata are not modified.

See `docs/SCIENCE_VALIDATION_HANDOFF.md` for the step-by-step evidence capture and future sign-off protocol.
