"""Area Advisor behavior based on repository data; no modified source CSVs."""
from __future__ import annotations

import pytest

from modules.area_advisor import GOAL_LABELS, advise_area, advisor_report
from modules.investigation_case import CaseData, load_case_data


def test_current_vegetation_recommendation_follows_selected_year():
    data = load_case_data()
    early = advise_area(data, "current_greenness", 2005)
    later = advise_area(data, "current_greenness", 2024)

    assert early.winner == "area_b"
    assert later.winner == "area_a"
    assert later.values["area_a"] == pytest.approx(0.35173537554554934)
    assert later.values["area_b"] == pytest.approx(0.2015084997027384)
    assert later.period == "2024"


def test_field_followup_is_low_three_year_ndvi_not_claim_of_damage():
    data = load_case_data()
    rec = advise_area(data, "field_followup", 2024)
    assert rec.winner == "area_b"
    assert rec.period == "2022–2024"
    assert rec.values["area_a"] > rec.values["area_b"]
    assert "NOT proof of damage" in rec.explanation
    assert "pending" in advisor_report(data, rec)


def test_long_term_greening_uses_existing_trend_engine():
    data = load_case_data()
    rec = advise_area(data, "long_term_greening", 2024)
    assert rec.winner == "area_a"
    assert rec.period == "2005–2024"
    assert rec.values["area_a"] > 0
    assert "does NOT establish" in rec.explanation


def test_abstains_when_both_areas_show_declining_ndvi():
    original = load_case_data()
    ndvi = original.ndvi.copy()
    ndvi["ndvi"] = 0.5 - 0.012 * (ndvi["year"] - 2005)
    altered = CaseData(ndvi, original.rainfall, original.geojson, original.metadata)
    rec = advise_area(altered, "long_term_greening", 2024)
    assert rec.winner is None


def test_tied_values_do_not_force_a_winner():
    original = load_case_data()
    ndvi = original.ndvi.copy()
    value_a = ndvi.loc[(ndvi["year"] == 2024) & (ndvi["area_id"] == "area_a"), "ndvi"].iloc[0]
    ndvi.loc[(ndvi["year"] == 2024) & (ndvi["area_id"] == "area_b"), "ndvi"] = value_a
    altered = CaseData(ndvi, original.rainfall, original.geojson, original.metadata)
    assert advise_area(altered, "current_greenness", 2024).winner is None


@pytest.mark.parametrize("goal,year", [("unknown", 2024), ("current_greenness", 2025), ("current_greenness", True)])
def test_invalid_goal_or_year_rejected(goal, year):
    with pytest.raises(ValueError):
        advise_area(load_case_data(), goal, year)


def test_goal_labels_are_explicit():
    assert set(GOAL_LABELS) == {"current_greenness", "long_term_greening", "field_followup"}
