"""Static safeguards for the independent-geometry, same-method Earth Engine rerun.

No authenticated Earth Engine account is used during CI. These tests prove
the source geometry frozen in the JS exactly matches the repository GeoJSON,
and the data-reduction algorithm hasn't been silently edited.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

from scripts.validate_science import ROOT

SCRIPT = ROOT / "scripts" / "reproduce_nasa_gee.js"
ORIGINAL = ROOT / "scripts" / "export_nasa_data.js"
GEOJSON = ROOT / "data" / "study_areas.geojson"


def _source() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_rerun_frozen_polygons_match_original_geospatial_source_exactly():
    source = _source()
    match = re.search(r"var FROZEN_GEOJSON = (\{[^\n]+\});", source)
    assert match is not None, "The self-contained geometry block was removed"
    frozen = json.loads(match.group(1))
    committed = json.loads(GEOJSON.read_text(encoding="utf-8"))
    assert frozen == committed  # no tolerance, editing, reversal, reprojection
    assert [f["properties"]["area_id"] for f in frozen["features"]] == [
        "area_a", "area_b"
    ]
    assert [len(f["geometry"]["coordinates"][0]) - 1 for f in frozen["features"]] == [6, 9]
    assert "ee.Geometry.Polygon(FROZEN_GEOJSON.features[0].geometry.coordinates)" in source
    assert "ee.Geometry.Polygon(FROZEN_GEOJSON.features[1].geometry.coordinates)" in source
    assert "areaA.coordinates()" not in source


def test_scientific_reduction_blocks_unchanged():
    source = _source()
    original = ORIGINAL.read_text(encoding="utf-8")
    begin = "// 2. Stable IDs shared by map, CSV files, and statistical analysis."
    end = "// 6. Start all three exports manually in the Tasks panel."
    assert begin in source and begin in original
    assert end in original
    assert "// 6. RECHECK tasks:" in source
    # Original data retrieval, QA, aggregation and time series must remain
    # byte-for-byte unchanged up to the task export configuration.
    new_data_code = source.split(begin, 1)[1].split("// 6. RECHECK tasks:", 1)[0]
    old_data_code = original.split(begin, 1)[1].split(end, 1)[0]
    assert new_data_code == old_data_code


def test_rerun_exports_are_isolated_and_preserve_column_schemas():
    source = _source()
    original = ORIGINAL.read_text(encoding="utf-8")
    assert source.count("Export.table.toDrive({") == 3
    assert source.count("folder: 'BLOOM_EE_RECHECK_2026'") == 3
    for suffix, fmt in (
        ("ndvi_annual", "CSV"),
        ("rainfall_annual", "CSV"),
        ("study_areas", "GeoJSON"),
    ):
        assert f"description: 'BLOOM_RECHECK_{suffix}'" in source
        assert f"description: 'BLOOM_{suffix}'" not in source
        assert f"fileNamePrefix: '{suffix}'" in source
        assert f"fileNamePrefix: '{suffix}'" in original
        assert f"fileFormat: '{fmt}'" in source
    assert "selectors: ['year', 'area_id', 'ndvi', 'valid_observations']" in source
    assert "selectors: ['year', 'area_id', 'rainfall_mm', 'valid_months']" in source
    assert "ee.List(areaA.coordinates())" not in source
    assert "filterDate('2005-01-01', '2025-01-01')" in source


def test_code_fails_safe_if_original_geometry_or_export_method_edited():
    # This test serves as a documentation invariant and is also exercised
    # by GitHub Actions. The rerun is not claimed to be NASA API-verified.
    src = _source()
    for fragment in (
        "MODIS/061/MOD13Q1",
        "NASA/GPM_L3/IMERG_MONTHLY_V07",
        "select('SummaryQA').eq(0)",
        "multiply(0.0001)",
        "validMonths.eq(12)",
        "next.difference(first, 'hour')",
    ):
        assert fragment in src
