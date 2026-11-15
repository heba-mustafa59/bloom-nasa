# BLOOM / Living Earth Missions — Research Preview

**Branch:** `feature/bloom-living-earth-missions` — integrate through review, not a forced main merge.

## Integration map

- Entry point: `ui_app.py`; the existing Home, Explore, Analytics, Mystery Lab, Compare, Reports, and About remain on the navbar.
- Mission page: `modules/ui_pages/living_missions.py` implements the existing `render(ctx, navigate)` pattern.
- `modules/living_data.py`: validates annual MODIS NDVI, annual polygon GPM rainfall, distinct NASA POWER **point** rainfall, two real WGS84 GeoJSON polygons, and metadata status. Uses the same local research CSV files as `modules/ui_data.py`. It does **not** apply the NDVI scale factor to already-scaled values.
- `modules/living_missions.py`: deterministic endpoint changes, existing trend/Mystery Engine reuse, source-attributed evidence, hypotheses, next-step decisions, investigation trail and HTML Passport.
- `modules/living_ai.py`: deterministic explanation by default; **optional** restricted Responses API critique using `OPENAI_API_KEY` only after explicit user consent. The remote text is qualitative, schema-checked, and rejected if it contains digits. Scientific numeric facts stay server-calculated.
- `modules/living_groundtruth.py`: local SQLite private reports, stripped-photo storage and review. Every report begins PENDING.
- `modules/living_webxr.py`: illustrative A-Frame evidence stations, desktop controls, year slider, optional headset via standalone HTTPS hosting. NOT a pixel-accurate geospatial twin.

## Local setup

```powershell
# Do this in a CLEAN separate clone if your current working tree has a merge conflict:
git clone --branch feature/bloom-living-earth-missions https://github.com/heba-mustafa59/bloom-nasa.git bloom-living-earth-demo
cd bloom-living-earth-demo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest tests/test_living_missions.py tests/test_trends.py tests/test_mystery.py tests/test_ui_data.py -q
python -m streamlit run ui_app.py
```

Select **Local CSV - Research Preview**. Open **Living Earth Missions** on the top navigation or sidebar. `Verified NASA` continues to require the independent `data/metadata.json` gate. Do not invent or relabel the metadata template.

## Configuration

No configuration or API key is required for the deterministic investigation and reports.

- `OPENAI_API_KEY`: optional connected model; absence falls back to rule-based explanation. `BLOOM_AI_MODEL` optionally selects model.
- `BLOOM_ENABLE_LOCAL_SUBMISSIONS=1`: enables consent-based private field reports in controlled local environment. Default is **disabled**. SQLite data and image uploads are stored under ignored `.bloom_private/`, not in the CSV directory.
- `BLOOM_REVIEWER_TOKEN`: long random secret required to expose reviewer UI. Do not commit a secret or expose it in source code.
- Never enable local SQLite submissions on publicly deployed ephemeral hosting: use persistent protected storage, authentication, abuse controls, backup, abuse monitoring, image scanning and retention policy before public release.

## Complete non-VR user journey

1. **Discover:** choose one of three missions generated from real endpoint measurements.
2. **Explore:** inspect the actual GeoJSON polygon and annual area-level readings. Optional 3D stations are explicitly illustrative, not real MODIS pixels.
3. **Evidence Lab:** inspect NDVI, GPM polygon rainfall, the separate NASA POWER point reference, the other area and missing-data limitations; collect each evidence item.
4. **AI Investigator:** select a causal *hypothesis* and read source-backed deterministic criticism; optional connected model only after consenting to public annual summaries.
5. **Decision Room:** select an evidence-gathering action. The system never forecasts intervention impact or claims irrigation caused change.
6. **Ground Truth:** submit an optional reviewed observation in a controlled local environment. By default no submission is accepted. Reviewer controls require a secret.
7. **Impact Passport:** download an HTML report derived from session case state. This records evidence and uncertainty, not confirmed environmental outcomes.
8. **Impact Tracking:** read SQLite counts from actual local records, not invented environmental impact scores.

## Scientific limitations

- `metadata_TEMPLATE.json` has `verification_status=pending`. Display **Research Preview**, not Verified NASA.
- MODIS MOD13Q1 V6.1 annual NDVI is the mean of valid 16-day spatial composites, native 250 m. Do not multiply values by `0.0001` again.
- GPM IMERG Monthly V07 precipitation is an annual polygon estimate from much coarser ~11.1 km pixels.
- NASA POWER annual point-reference rainfall is not a substitute for GPM polygon rainfall.
- There are no temperature data, field irrigation logs, crop records or individual-plant observations. Do not infer precise interventions.
- Area B has a negative NDVI **endpoint difference**, but its complete-series Mann–Kendall trend is **not statistically significant**. No fictional emergency is issued.
- Mystery Engine validation can fail, especially Area A; no anomaly is claimed from an invalid model.
- The 3D terrain is an **illustration** and cannot reconstruct individual plants or detailed land cover from polygon means.
- WebXR headset support depends on HTTPS secure context, browser, headset and iframe permissions. The provided Streamlit embed is primarily desktop 3D and a standalone HTML export; an independent HTTPS route is not deployed.
- Session investigation progress survives Streamlit reruns but not browser session loss. Reports and field records persist locally; session state is not server-persistent.
- Full public Arabic translations, independent ground-truth identity verification, rate-limiting across anonymous clients, production moderation infrastructure, audited geospatial topology, and a fully-hosted VR route require future production hardening.

## Acceptance / tests

Run `python -m pytest tests/test_living_missions.py tests/test_ui_data.py tests/test_trends.py tests/test_mystery.py -q`. The tests check actual source CSV values, source distinction, year coercion, provenance, validation failures, case state, restricted AI fallback, image metadata stripping, SQLite status changes, report generation and WebXR source binding.

Do **not** claim a successful browser or VR smoke test until you have opened the actual deployed app and exercised the hardware/browser path.

### Judge demo (90 seconds)

"From MODIS, Area A NDVI changes from about 0.165 to 0.352. Area B has a negative endpoint change, but its 20-year trend is not statistically significant. We compare that to polygon-level GPM rainfall and separately identify the POWER point reference. We gather five evidence cards, choose a hypothesis and let the deterministic investigator challenge its limits. Rather than claiming an unmeasured causal intervention, we select a field measurement as the next scientific action. Optional field reports remain PENDING until reviewed. Our Impact Passport records exactly what we know and what we still need to verify."
