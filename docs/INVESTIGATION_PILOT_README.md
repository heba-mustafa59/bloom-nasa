# BLOOM Investigation Pilot — isolated trial

This branch is intentionally separate from main. **No merge is required to test it.**

## Run in Codespaces

1. Check that any existing work in your Codespace is committed or safely stashed.
2. Run:

```bash
git fetch origin
git switch --track origin/feature/investigation-case-pilot
python -m pip install -r requirements.txt
python -m pytest tests/test_investigation_case_pilot.py tests/test_area_advisor.py -q
python -m streamlit run investigation_app.py --server.address 0.0.0.0
```

If the branch already exists locally, run `git switch feature/investigation-case-pilot` instead of the second command.
Open port **8501** from the Codespaces Ports tab.

## What to try

- Select Area A or Area B (also by clicking within the original polygons).
- Select 2005 / 2015 / 2024 and inspect NDVI + rainfall values.
- View long-term trends and reported Mann–Kendall statistical significance.
- Review the rainfall-only model validation status.
- In **Area Advisor**, select a question: greener this year, strongest supported long-term greening, or priority for field follow-up. Compare and download the evidence report.
- Download the investigation brief.

## Important limitations

- The input CSVs and exported GeoJSON are the repository's original 2005–2024 study area files; no invented measurements.
- Source provenance remains **pending** in `data/metadata.json`. The pilot explicitly marks conclusions *provisional*. It does not change that metadata.
- An exploratory trend is not evidence of a causal explanation, irrigation change, or land-use classification.
- Area Advisor makes *criterion-specific comparisons* only. Higher NDVI does not prove an area is more suitable for farming; the follow-up priority is a screening indicator, not a diagnosis.
- Rainfall is contextual only and cannot independently rank two closely spaced polygons.
- The separate `ui_app.py` and `app.py` are **unchanged**.
- No areas C/D are added in this pilot. That requires actual polygons and matching extraction results.

## File additions only

- `investigation_app.py` standalone interactive app
- `modules/investigation_case.py` data validation, click mapping, reporting
- `modules/area_advisor.py` goal-driven recommendation logic
- `tests/test_area_advisor.py` comparison guard and regression tests
- `tests/test_investigation_case_pilot.py` tests
- this README

Avoid merging until the pilot passes UI and science review.


## Main BLOOM site integration (this branch only)

The original team site now includes the Investigation Pilot inside **Explore**:

```bash
git switch feature/investigation-case-pilot
git pull --ff-only origin feature/investigation-case-pilot
python -m streamlit run ui_app.py --server.port 8503
``

1. Open port **8503** and navigate to **Explore**. The data source defaults to **Uploaded NASA CSVs (pilot)** (not synthetic demo).
2. Click Area A or Area B on the map. The sidebar study selector synchronizes after the map click; NDVI, rainfall, graphs and advisor reflect the chosen area.
3. Select a year. Choose a goal in **Area Advisor** and download an investigation brief.
4. **Analytics**, **Mystery Lab** and **Reports** can now read the same uploaded CSVs via the UI-only pilot context. Reports includes the Area Advisor explanation.
5. You can still switch to **Synthetic demo** for UI testing.

Safety: `modules/data_loader.py`, `modules/ui_data.py`, original source data and `app.py` were NOT changed. Uploaded records are used unchanged, and `metadata.json` retains `pending` provenance status. **This is not a land-suitability score or a field diagnosis.**
