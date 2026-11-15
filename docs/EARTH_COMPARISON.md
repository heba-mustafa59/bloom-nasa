# BLOOM Earth Comparison Explorer

Launch `python -m streamlit run ui_app.py` and choose **Compare**. This UI feature leaves the stable `app.py`, map renderer, data loader and scientific interfaces unchanged.

Choose two contract regions using the keyboard-accessible selectors, or choose a target slot and click its exact boundary. Selecting an occupied region swaps the slots. Region A is green and Region B amber; labels provide a non-color cue. Map clicks use streamlit-folium's `last_object_clicked_tooltip`, `last_object_clicked_count` and `on_change` callback. Only exact validated polygon IDs are accepted. A consumed event is not replayed by a later control rerun.

The sidebar's **Display years** aligns both time series and the comparison period within 2005–2024. **Explore year** moves both chart cursors and annual cards without changing the verdict window. Shortening the period clamps the cursor. No manual refresh is required.

## Evidence policy

- Verified-source claims require the existing strict loader and `verification_status: verified`. This feature never creates or changes scientific exports or metadata.
- When loading science fails, supplied local GeoJSON may still be displayed, with dashed outlines and an explicit **UNVERIFIED GEOGRAPHY** warning. Geometry validation is not provenance certification. Missing/invalid polygons are not invented or spatially guessed.
- Demo values remain synthetic, visibly marked **DEMO** in verdicts, cards, charts and statistics. No demo measurements are attached to real polygons.
- Each criterion uses matching valid years for the two regions. Charts retain individual observations and gaps. Duplicates, non-finite readings, impossible values and invalid QA counts are unavailable, never zero-filled.
- Highest average NDVI compares matched-year arithmetic means. Highest annual rainfall compares the mean of matched annual totals, not the maximum year. These are descriptive rankings, not tests of a between-region difference.
- Strongest vegetation improvement compares the shared trend engine's NDVI slope per decade. It needs at least 10 matching years and a positive, significant increasing trend in the candidate leader. Otherwise it reports unavailable or inconclusive. Equal scores within numerical tolerance yield a tie. Individual trend significance does not establish a significant difference between slopes.
- Higher NDVI is not automatically better ecosystem health. Correlation does not establish causation or irrigation. MODIS and GPM have very different spatial support. The page reports independence assumptions, missing years, and source limitations.

## Validation

Run `python -m pytest -q -p no:cacheprovider`. `tests/test_comparison.py` covers selection/swapping, supported map callback handling and replay prevention, criteria, matching-year means, ties, incomplete/invalid data, trend evidence, exact geometry, provenance gating, and Streamlit reruns.

Browser assets require `cdn.jsdelivr.net`; street tiles require `tile.openstreetmap.org` (including provider subdomains if used), satellite tiles require `server.arcgisonline.com`. Existing fonts use `fonts.googleapis.com` and `fonts.gstatic.com`. Network policy and browser trust must permit these providers. The comparison map loads only Leaflet and the fullscreen plugin, omitting unused Bootstrap/jQuery/icon dependencies. Tile outages do not invalidate the dropdown comparison workflow.

Current checkout limitation: `data/metadata.json` is absent. Verified scientific comparisons therefore remain unavailable until the data team completes independent validation. Existing `app.py` error handling is outside this UI feature's scope.
