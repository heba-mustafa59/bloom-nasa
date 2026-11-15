"""Tests for the live homepage discovery and year-driven NDVI Time Machine."""
from __future__ import annotations

import math

import pytest

from modules.discovery_time_machine import discovery, ndvi_color, snapshot
from modules.investigation_case import load_case_data
from modules.ui_pages.explore_pilot import _map


def test_discovery_uses_exact_uploaded_endpoints_and_reversal():
    data = load_case_data()
    result = discovery(data)
    assert result.initial_year == 2005
    assert result.final_year == 2024
    assert result.first_leader == "area_b"
    assert result.final_leader == "area_a"
    assert result.switched_leader is True
    a, b = result.changes["area_a"], result.changes["area_b"]
    assert a.first_ndvi == pytest.approx(0.16515122987658773)
    assert a.selected_ndvi == pytest.approx(0.35173537554554934)
    assert b.first_ndvi == pytest.approx(0.2635271048007687)
    assert b.selected_ndvi == pytest.approx(0.2015084997027384)
    assert a.difference > 0
    assert b.difference < 0
    assert data.metadata["verification_status"] == "pending"


def test_time_machine_snapshots_change_with_year_without_interpolation():
    data = load_case_data()
    start = snapshot(data, 2005)
    middle = snapshot(data, 2015)
    end = snapshot(data, 2024)
    for area_id in ("area_a", "area_b"):
        assert start[area_id].difference == pytest.approx(0)
        assert end[area_id].first_ndvi == pytest.approx(start[area_id].selected_ndvi)
    assert middle["area_a"].selected_ndvi == pytest.approx(0.2193965671341749)
    assert middle["area_b"].selected_ndvi == pytest.approx(0.24784283536652896)
    assert middle["area_a"].selected_ndvi != end["area_a"].selected_ndvi


def test_map_polygons_change_colors_as_year_changes_using_fixed_scale():
    data = load_case_data()
    early = _map(data, "area_a", 2005, "Satellite").get_root().render()
    late = _map(data, "area_a", 2024, "Satellite").get_root().render()
    assert ndvi_color(0.16515122987658773) == "#C8D99C"
    assert ndvi_color(0.2635271048007687) == "#72AD6B"
    assert ndvi_color(0.35173537554554934) == "#1F5F40"
    assert ndvi_color(0.2015084997027384) == "#A2C784"
    for color in ("#C8D99C", "#72AD6B"):
        assert color in early
    for color in ("#1F5F40", "#A2C784"):
        assert color in late
    assert "0.1652" in early
    assert "0.3517" in late
    assert "Annual polygon-mean NDVI" in late


@pytest.mark.parametrize("value", [-2, 2, float("inf"), float("nan")])
def test_ndvi_scale_rejects_impossible_values(value):
    with pytest.raises(ValueError):
        ndvi_color(value)


@pytest.mark.parametrize("year", [2004, 2025, True])
def test_snapshots_reject_invalid_year(year):
    with pytest.raises(ValueError):
        snapshot(load_case_data(), year)
