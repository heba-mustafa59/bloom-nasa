"""Tests for the isolated investigation pilot; real files are not edited."""
from __future__ import annotations

from pathlib import Path

import pytest

from modules.investigation_case import (
    AREA_NAMES,
    annual_series,
    area_at_point,
    case_report,
    investigate,
    load_case_data,
)


def test_study_files_load_and_preserve_provisional_status():
    data = load_case_data()
    assert len(data.ndvi) == 40
    assert len(data.rainfall) == 40
    assert len(data.geojson["features"]) == 2
    assert data.metadata.get("verification_status") == "pending"
    assert data.verified is False


@pytest.mark.parametrize("area_id", list(AREA_NAMES))
def test_area_timeseries_and_report(area_id):
    data = load_case_data()
    annual = annual_series(data, area_id)
    assert annual["year"].tolist() == list(range(2005, 2025))
    assert annual["ndvi"].between(-1, 1).all()
    assert (annual["rainfall_mm"] >= 0).all()
    results = investigate(data, area_id)
    assert results["ndvi_trend"]["n_observations"] == 20
    assert results["rainfall_trend"]["n_observations"] == 20
    assert results["mystery"]["model_status"] in {"validated", "insufficient_evidence"}
    report = case_report(data, area_id, results)
    assert "PROVISIONAL" in report
    assert "not evidence of causation" in report


def test_map_selection_uses_only_supplied_geometry():
    data = load_case_data()
    for feature in data.geojson["features"]:
        ring = feature["geometry"]["coordinates"][0]
        lon, lat = ring[0]
        assert area_at_point(data.geojson, lat, lon) == feature["properties"]["area_id"]
    assert area_at_point(data.geojson, 0.0, 0.0) is None
