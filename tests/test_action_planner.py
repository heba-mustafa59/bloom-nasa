"""BLOOM Action Pathway safety and scientific grounding tests."""
from __future__ import annotations

import pytest

from modules.action_planner import (
    FIELD_SIGNALS,
    action_plan_markdown,
    build_action_plan,
)
from modules.area_advisor import advise_area
from modules.investigation_case import load_case_data


def test_action_pathway_from_uploaded_2024_area_b_values():
    data = load_case_data()
    recommendation = advise_area(data, "field_followup", 2024)
    assert recommendation.winner == "area_b"
    plan = build_action_plan(data, recommendation, "area_b")
    assert plan.ndvi == pytest.approx(0.2015084997027384)
    assert plan.rainfall_mm == pytest.approx(314.25600992515683)
    assert plan.baseline_ndvi == pytest.approx(0.2635271048007687)
    assert plan.recent_mean_ndvi == pytest.approx(
        (0.2172830002983095 + 0.20981984643647364 + 0.2015084997027384) / 3
    )
    assert plan.measured_change == pytest.approx(0.2015084997027384 - 0.2635271048007687)
    assert plan.status == "FIELD VERIFICATION NEEDED"
    assert "No intervention is prescribed yet" in plan.conditional_action
    assert "not a claim" not in plan.interpretation  # note is scientifically explicit, not marketing
    assert "cannot verify" in plan.interpretation


def test_different_goal_motivates_different_field_question_not_new_data():
    data = load_case_data()
    one = build_action_plan(data, advise_area(data, "current_greenness", 2024), "area_a")
    two = build_action_plan(data, advise_area(data, "long_term_greening", 2024), "area_a")
    assert one.ndvi == two.ndvi
    assert one.rainfall_mm == two.rainfall_mm
    assert one.evidence[3] != two.evidence[3]


@pytest.mark.parametrize("signal", list(FIELD_SIGNALS))
def test_field_clues_are_self_reported_and_never_claim_causation(signal):
    data = load_case_data()
    rec = advise_area(data, "field_followup", 2024)
    plan = build_action_plan(data, rec, "area_b", signal)
    output = action_plan_markdown(data, plan)
    assert FIELD_SIGNALS[signal] in output
    assert "user-reported" in output.lower()
    assert "not independently verified" in output
    assert "no later impact values have been collected" in output


def test_water_hypothesis_response_only_after_confirmation():
    data = load_case_data()
    rec = advise_area(data, "field_followup", 2024)
    plan = build_action_plan(data, rec, "area_b", "water_access")
    assert "Only if a local assessment confirms water stress" in plan.conditional_action
    assert "with a qualified local expert" in " ".join(plan.ground_checks).lower()


def test_checklist_reports_user_ticked_not_verified():
    data = load_case_data()
    rec = advise_area(data, "field_followup", 2024)
    plan = build_action_plan(data, rec, "area_b", "not_checked")
    doc = action_plan_markdown(data, plan, (plan.ground_checks[0],))
    assert "- [x] " + plan.ground_checks[0] in doc
    assert "- [ ] " + plan.ground_checks[1] in doc
    assert "self-reported" in doc


def test_field_clue_does_not_override_advisor_winner():
    data = load_case_data()
    rec = advise_area(data, "field_followup", 2024)
    plan = build_action_plan(data, rec, "area_a", "crop_cycle")
    assert plan.advisor_winner == "area_b"
    assert "user-selected focus" in plan.evidence[-1]
    assert "do not label the area degraded" in plan.conditional_action


@pytest.mark.parametrize(
    "area,signal", [("area_d", "not_checked"), ("area_a", "not_real")]
)
def test_unknown_area_or_signal_rejected(area, signal):
    data = load_case_data()
    rec = advise_area(data, "current_greenness", 2024)
    with pytest.raises(ValueError):
        build_action_plan(data, rec, area, signal)


def test_fake_checklist_entry_rejected():
    data = load_case_data()
    rec = advise_area(data, "current_greenness", 2024)
    plan = build_action_plan(data, rec, "area_a")
    with pytest.raises(ValueError):
        action_plan_markdown(data, plan, ("field result confirmed water stress",))
