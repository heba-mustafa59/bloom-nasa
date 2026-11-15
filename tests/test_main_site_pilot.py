"""Contract tests for the main-site BLOOM pilot integration."""
from __future__ import annotations

import pandas as pd

from modules.investigation_case import CaseData, load_case_data
from modules.ui_data import UIContext, load_ui_context
from modules.ui_pilot_context import pilot_context
from modules.ui_pages.explore_pilot import _map, _chart
from modules.ui_pages.reports import _report
from modules.area_advisor import advise_area, advisor_report


def test_main_site_pilot_recovers_uploaded_files_without_false_verification():
    original = load_ui_context("verified", "area_a", 2005, 2024)
    assert original.ready is False
    assert original.error is not None
    integrated = pilot_context(original)
    assert integrated.ready is True
    assert integrated.mode == "verified"
    assert integrated.metadata["verification_status"] == "pending"
    assert len(integrated.geojson["features"]) == 2
    assert len(integrated.area_data("ndvi")) == 20
    assert len(integrated.area_data("rainfall_mm")) == 20


def test_demo_mode_remains_opt_in_and_unchanged():
    demo = load_ui_context("demo", "area_b", 2005, 2024)
    assert demo.is_demo is True
    assert pilot_context(demo) is demo
    assert demo.geojson == {}


def test_pilot_map_and_trend_figures_use_uploaded_values():
    data = load_case_data()
    image_map = _map(data, "area_a", 2024, "Satellite")
    html = image_map.get_root().render()
    assert "0.3517" in html
    assert "0.2015" in html
    assert "314.3 mm" in html
    assert "name" in html
    series = data.ndvi.loc[data.ndvi["area_id"] == "area_a", ["year", "ndvi"]]
    fig = _chart(series, 2024, "ndvi", "NDVI", "#2E7254")
    assert fig.data[0].y[-1] == 0.35173537554554934


def test_main_reports_keep_data_status_and_include_advisor():
    raw = load_ui_context("verified", "area_b", 2005, 2024)
    ctx = pilot_context(raw)
    from modules.ui_data import mystery_for, trend_for

    report = _report(
        ctx,
        trend_for(ctx, "ndvi"),
        trend_for(ctx, "rainfall_mm"),
        mystery_for(ctx),
    )
    assert "provenance pending" in report
    assert "VERIFIED NASA EXPORTS" not in report
    data = CaseData(ctx.ndvi_df, ctx.rainfall_df, ctx.geojson, ctx.metadata)
    rec = advise_area(data, "current_greenness", 2024)
    combined = report + "\n" + advisor_report(data, rec)
    assert "Area A" in combined
