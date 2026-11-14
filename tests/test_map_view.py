"""TEST GEOMETRY AND TEST NUMBERS below are invented FIXTURES, not NASA observations."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import pandas as pd
import pytest

FILE = Path(__file__).resolve().parents[1] / "modules" / "map_view.py"
spec = importlib.util.spec_from_file_location("bloom_map_test", FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def polygon(lon, lat, key):
    return {"type":"Feature", "properties":{"area_id":key}, "geometry": {
        "type":"Polygon", "coordinates":[[[lon,lat],[lon+.005,lat],
                                      [lon+.005,lat+.005],[lon,lat+.005],[lon,lat]]]}}


def geo():
    return {"type":"FeatureCollection","features":[
        polygon(35.44,31.87,"area_a"), polygon(35.46,31.95,"area_b")]}


def test_no_data_no_nasa_claims():
    html = m.build_map({}, "area_a").get_root().render()
    assert "Tell es-Sultan" in html and "Al-Auja" in html
    assert "NOT a NASA extraction polygon" in html
    assert "Annual NDVI (polygon mean)" not in html


def test_polygon_label_is_not_assumed_site_name():
    html = m.build_map(geo(), "area_a").get_root().render()
    assert m._valid_features(geo())[0]["properties"]["display_name"] == "Area A — Study polygon"
    assert "Reference places (NOT polygon boundaries)" in html
    assert len(m._valid_features(geo())) == 2


def test_geometry_stays_identical():
    input_geo = geo()
    out = m._valid_features(input_geo)
    assert out[0]["geometry"] is input_geo["features"][0]["geometry"]


def test_malformed_or_offsite_ignored():
    off = {"type":"FeatureCollection","features":[polygon(12,14,"area_a")]}
    assert m._valid_features(off) == []
    broken = geo()
    broken["features"][0]["geometry"]["coordinates"][0][-1] = [35.45,31.90]
    assert len(m._valid_features(broken)) == 1


def test_2025_rejected():
    with pytest.raises(ValueError):
        m.build_map({}, selected_year=2025)


def test_verified_metadata_only():
    n = pd.DataFrame([{"year":2020,"area_id":"area_a","ndvi":0.3922,"valid_observations":22}])
    r = pd.DataFrame([{"year":2020,"area_id":"area_a","rainfall_mm":137.8,"valid_months":12}])
    pending = m.build_map(geo(), "area_a", ndvi_df=n, rainfall_df=r,
                          metadata={"verification_status":"pending"},
                          selected_year=2020, mode="Annual NDVI").get_root().render()
    assert "0.3922" not in pending and "137.8" not in pending
    checked = m.build_map(geo(), "area_a", ndvi_df=n, rainfall_df=r,
                          metadata={"verification_status":"verified"},
                          selected_year=2020, mode="Annual NDVI").get_root().render()
    assert "0.3922" in checked and "137.8" in checked
    assert "Annual NDVI (polygon mean)" in checked


def test_rainfall_incomplete_disallowed():
    r = pd.DataFrame([{"year":2020,"area_id":"area_a","rainfall_mm":98.7,"valid_months":11}])
    html = m.build_map(geo(), "area_a", rainfall_df=r, selected_year=2020,
                       metadata={"verification_status":"verified"}).get_root().render()
    assert "98.7" not in html


def test_duplicate_and_invalid_ndvi_disallowed():
    n = pd.DataFrame([{"year":2020,"area_id":"area_a","ndvi":0.4567},
                      {"year":2020,"area_id":"area_a","ndvi":0.4567}])
    assert m._reading(n, "area_a", 2020, "ndvi") is None
    n = pd.DataFrame([{"year":2020,"area_id":"area_a","ndvi":9.8765}])
    assert m._reading(n, "area_a", 2020, "ndvi") is None


def test_basemaps():
    for basemap in m.BASEMAPS:
        html = m.build_map(geo(), "area_b", basemap=basemap).get_root().render()
        assert "World_Imagery" in html


def test_focus_on_references_distinct_from_polygons():
    tell = m.build_map(geo(), "area_b", focus="tell_sultan")
    assert tell.location == [m.REFERENCE_SITES["tell_sultan"]["lat"],
                             m.REFERENCE_SITES["tell_sultan"]["lon"]]
    auja = m.build_map(geo(), "area_a", focus="al_auja")
    assert auja.location == [m.REFERENCE_SITES["al_auja"]["lat"],
                             m.REFERENCE_SITES["al_auja"]["lon"]]


def test_wrong_ids_rejected():
    with pytest.raises(ValueError):
        m.build_map({}, "unknown")
