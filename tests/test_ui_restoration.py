"""Regression checks for restored BLOOM UI stability and honest source labeling."""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pandas as pd

from modules.ui_data import load_ui_context
from modules.ui_pages.reports import _report


ROOT = Path(__file__).resolve().parents[1]


def _sample_csvs(folder):
    rows_ndvi = []
    rows_rain = []
    for area in ("area_a", "area_b"):
        for year in range(2005, 2025):
            rows_ndvi.append({
                "year": year, "area_id": area,
                "ndvi": 0.2, "valid_observations": 22,
            })
            rows_rain.append({
                "year": year, "area_id": area,
                "rainfall_mm": 300.0, "valid_months": 12,
            })
    pd.DataFrame(rows_ndvi).to_csv(folder / "ndvi_annual.csv", index=False)
    pd.DataFrame(rows_rain).to_csv(folder / "rainfall_annual.csv", index=False)


def test_local_csv_renders_supplied_candidate_geography(tmp_path):
    _sample_csvs(tmp_path)
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"area_id": area},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[35.45, 31.85], [35.46, 31.85],
                                     [35.46, 31.86], [35.45, 31.85]]],
                },
            }
            for area in ("area_a", "area_b")
        ],
    }
    (tmp_path / "study_areas.geojson").write_text(json.dumps(geojson), encoding="utf-8")
    ctx = load_ui_context("local", "area_a", 2005, 2024, data_dir=tmp_path)
    assert ctx.ready
    assert ctx.geojson == geojson
    assert ctx.metadata["verification_status"] == "local_unverified"


def test_local_csv_never_claims_verified_nasa_in_download(tmp_path):
    _sample_csvs(tmp_path)
    ctx = load_ui_context("local", "area_a", 2005, 2024, data_dir=tmp_path)
    report = _report(ctx, {"direction": "not_significant"}, {}, {})
    assert "LOCAL CSV — RESEARCH PREVIEW" in report
    assert "VERIFIED NASA EXPORTS" not in report


def test_explore_renderer_uses_two_argument_contract():
    tree = ast.parse((ROOT / "modules/ui_pages/explore.py").read_text(encoding="utf-8"))
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "render_map"
    ]
    assert len(calls) == 1
    assert len(calls[0].args) == 2
    assert not calls[0].keywords


def test_multiline_html_is_not_treated_as_markdown_code():
    for path in ("ui_app.py", "modules/ui_pages/about.py", "modules/ui_components.py"):
        text = (ROOT / path).read_text(encoding="utf-8")
        assert 'st.markdown(\n        \'\'\'' not in text
        assert 'st.markdown(\n            \'\'\'' not in text
        assert "st.html(" in text
