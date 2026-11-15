# BLOOM — Earth Engine Reproduction Runbook (read-only for the website)

**Goal:** Repeat the documented 2005–2024 MODIS NDVI and GPM rainfall extractions using the exact two polygons archived in `data/study_areas.geojson`, then compare the **new output** against the existing data files. This is a **method-reproduction check** (same method, frozen geometry), not an independent validation of the scientific method.

**Branch:** `fix/nasa-science-validation`. **Never edit:** `main`, `data/*`, website components, or the three original archived Earth Engine exports. The new tasks use a separate Google Drive folder and task descriptions.

## A. Preparation (no new task yet)

1. Preserve the three completed originals: `BLOOM_ndvi_annual`, `BLOOM_rainfall_annual`, `BLOOM_study_areas`. Keep the downloaded originals in `~/Desktop/bloom_ee_original`.
2. Read `scripts/reproduce_nasa_gee.js` from this branch. It embeds the original GeoJSON coordinates directly. **Do not draw or modify polygons** and do not copy an `areaA` import into this reproducibility run.
3. Open [Google Earth Engine Code Editor](https://code.earthengine.google.com/) in the account that has access to the NASA collections. Choose a **new script tab**. Copy the entire JS file from the branch into the editor. This does **not** change the original saved script.
4. Check that the new script declares the original study area as frozen coordinates and prints `RECHECK: 2 frozen original study polygons`. Confirm `area_a` east and `area_b` west visually.
5. Press **Run** once to prepare the three new export tasks. A code Run starts the computation/queueing, **not** the task execution itself; select each queued task in the **Tasks** panel and start it manually.

## B. New, isolated Google Drive exports

The new descriptions are deliberately distinct from the originals:

| New task description | Expected Drive file | Format |
| --- | --- | --- |
| `BLOOM_RECHECK_ndvi_annual` | `ndvi_annual.csv` | CSV |
| `BLOOM_RECHECK_rainfall_annual` | `rainfall_annual.csv` | CSV |
| `BLOOM_RECHECK_study_areas` | `study_areas.geojson` | GeoJSON |

All go to the folder `BLOOM_EE_RECHECK_2026`. The Code Editor `Export.table.toDrive` `folder` argument specifies a **Drive folder name**, not a local Linux directory; Earth Engine creates it if it doesn't exist. Check the exact folder and file IDs before downloading. Save a screenshot of each new task's ID, `COMPLETED` status, source script link and output file link. See the [official export reference](https://developers.google.com/earth-engine/apidocs/export-table-todrive).

**Important:** The existing `data/*.csv` are not modified by these exports. If any new task fails, record the error, do not fake missing observations or manually replace missing values with zero.

## C. Copy the NEW exports to a NEW local folder

After confirming all three rerun tasks completed in Earth Engine:

```bash
mkdir -p ~/Desktop/bloom_ee_rerun
```

Download only the three **new** files from `BLOOM_EE_RECHECK_2026` into `~/Desktop/bloom_ee_rerun`. Do **not** copy the old `bloom_ee_original` or repository `data/` files into the rerun directory: that would create a false MATCH.

The comparison script requires filenames `ndvi_annual.csv`, `rainfall_annual.csv`, and `study_areas.geojson` inside the rerun directory. If the browser appends `(1)` or `(2)`, create a correctly named **copy inside the rerun directory only**, keeping the original downloaded file unchanged.

Confirm the input directory before comparing:

```bash
ls -lah ~/Desktop/bloom_ee_rerun
```

## D. Compare current BLOOM data with actual new outputs

Run from the local `bloom-nasa` project root:

```bash
git fetch origin
git switch fix/nasa-science-validation
git pull --ff-only origin fix/nasa-science-validation

python -m pytest tests/test_science_validation.py tests/test_science_rerun_script.py -q
python scripts/validate_science.py \
  --original-dir "$HOME/Desktop/bloom_ee_rerun" \
  --report "$HOME/Desktop/BLOOM_reproduction_result.md" \
  --json "$HOME/Desktop/BLOOM_reproduction_result.json"
grep -A 5 "Comparison with independently supplied" "$HOME/Desktop/BLOOM_reproduction_result.md"
```

**Interpreting the results**

- `match`: 40 NDVI rows + 40 rainfall rows match at the audit's declared numerical tolerance; the two GeoJSON features have matching IDs and ordered coordinate arrays. This demonstrates **reproducibility of the uploaded data under the documented re-execution** — provided the compared files really were downloaded from newly completed tasks.
- `mismatch`: inspect table data, source collection revisions, numerical/resampling variation, QA and month counts, task source, and frozen geometry. **Do not replace** app data automatically.
- `missing original export`: a file is misnamed, missing or in the wrong folder. This is an input-path problem, **not** proof of numerical disagreement.
- `PENDING_EXTERNAL_PROVENANCE_AND_REVIEW` may remain even with `match`: the audit intentionally requires human source verification and review before claiming authenticated NASA provenance.

## E. What is and isn't scientifically established

- **Reproduction:** The script uses **the same method** as `scripts/export_nasa_data.js` with explicitly frozen repository geometries. It is not an entirely independent algorithm.
- **Originals:** The previously user-supplied screenshots show the three original tasks completed, and a local comparison of their downloaded files to the repository returned `MATCH`. The new task screenshots and links provide a separate trace.
- **Study limitations:** MODIS NDVI at ~250 m and monthly GPM at ~11.1 km have different spatial supports. GPM pixels may be shared between these nearby polygons. Mann–Kendall trend significance is not data-source verification or proof of causation.
- **Current status:** Leave `data/metadata.json` at `pending` until the original task-to-file link, exact inputs, new rerun comparison, and reviewer sign-off are documented. Do not modify UI or `main`.

## F. Reviewer hand-off

Keep the 3 new task IDs, dates, Code Editor source-script URL, three Drive file URLs, the comparison report and a description of any differences. A qualified reviewer should verify those pieces, inspect original `areaA` and the new frozen geometry, and record the methods and resolution of discrepancies. See `docs/EARTH_ENGINE_EVIDENCE_TEMPLATE.json` and `docs/OBSERVED_EARTH_ENGINE_TASKS.md`.

**This script has been statically tested in CI, but cannot be executed on the user's Earth Engine project from the GitHub connector alone. The Earth Engine export tasks must be run in the user's authenticated account.**
