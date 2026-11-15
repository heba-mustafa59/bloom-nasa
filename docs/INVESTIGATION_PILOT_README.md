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
