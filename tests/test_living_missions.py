"""Integration tests for actual BLOOM mission records and bounded local fixtures."""
from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
import shutil

from PIL import Image
import pandas as pd
import pytest

from modules.living_data import load_mission_data
from modules.living_missions import (
    ACTIONS, HYPOTHESES, endpoint_change, mission_catalog,
    evidence_cards, evaluate_hypothesis, new_case, record_case_step,
    impact_passport, trends, explain_investigation,
)
from modules.living_ai import interrogate
from modules.living_groundtruth import (
    impact_metrics, record_activity, report_status, review_report, submit_report,
    sanitize_photo, list_pending,
)
from modules.living_webxr import scene_html
from modules.ui_data import load_ui_context

ROOT = Path(__file__).resolve().parents[1] / "data"


def copied_data(tmp_path):
    for name in (
        "ndvi_annual.csv", "rainfall_annual.csv",
        "nasa_power_jericho_point_rainfall.csv",
        "study_areas.geojson", "metadata_TEMPLATE.json",
    ):
        shutil.copy2(ROOT / name, tmp_path / name)
    return tmp_path


@pytest.fixture(scope="module")
def data():
    return load_mission_data()


def test_valid_real_exports_and_pending_provenance(data):
    assert len(data.ndvi) == len(data.rainfall) == 40
    assert len(data.power_point) == 20
    assert data.verification == "pending"
    assert data.observation("area_a", 2005)["ndvi"] == pytest.approx(0.16515122987658773)
    assert data.observation("area_a", 2024)["ndvi"] == pytest.approx(0.35173537554554934)
    assert data.ndvi.year.dtype.kind in ("i", "u")


def test_real_endpoint_changes_not_continuous_claims(data):
    a = endpoint_change(data, "area_a", 2005, 2024)
    b = endpoint_change(data, "area_b", 2005, 2024)
    assert a["ndvi_delta"] > 0
    assert b["ndvi_delta"] < 0
    assert a["ndvi_start"] == pytest.approx(0.16515122987658773)
    assert b["ndvi_end"] == pytest.approx(0.2015084997027384)
    assert len(mission_catalog(data)) == 3


def test_existing_stats_and_ai_are_reused(data):
    assert trends(data, "area_a")["ndvi"]["direction"] == "increasing"
    assert trends(data, "area_b")["ndvi"]["direction"] == "not_significant"
    assert trends(data, "area_a")["mystery"]["model_status"] == "insufficient_evidence"
    assert trends(data, "area_b")["mystery"]["model_status"] == "validated"


def test_point_reference_is_not_gpm_polygon(data):
    observation = data.observation("area_a", 2024)
    assert observation["gpm_rainfall_mm"] != observation["power_point_rainfall_mm"]
    cards = evidence_cards(data, "area_a", 2005, 2024)
    assert len(cards) == 5
    assert "point" in cards[2]["source"].lower()
    assert "polygon" in cards[1]["source"].lower()


def test_local_mode_uses_validated_shared_records():
    ctx = load_ui_context("local", "area_a", 2005, 2024)
    assert ctx.ready and not ctx.is_demo
    assert ctx.metadata["verification_status"] == "pending"
    assert len(ctx.ndvi_df) == 40


def test_duplicate_record_is_rejected(tmp_path):
    folder = copied_data(tmp_path)
    nd = pd.read_csv(folder / "ndvi_annual.csv")
    nd.loc[1, ["area_id", "year"]] = nd.loc[0, ["area_id", "year"]].to_numpy()
    nd.to_csv(folder / "ndvi_annual.csv", index=False)
    with pytest.raises(ValueError):
        load_mission_data(folder)


def test_missing_measurement_is_never_zero_filled(tmp_path):
    folder = copied_data(tmp_path)
    rain = pd.read_csv(folder / "rainfall_annual.csv")
    rain.loc[0, "rainfall_mm"] = None
    rain.to_csv(folder / "rainfall_annual.csv", index=False)
    with pytest.raises(ValueError):
        load_mission_data(folder)


def test_invalid_ndvi_and_months_rejected(tmp_path):
    folder = copied_data(tmp_path)
    nd = pd.read_csv(folder / "ndvi_annual.csv")
    nd.loc[0, "ndvi"] = 999
    nd.to_csv(folder / "ndvi_annual.csv", index=False)
    with pytest.raises(ValueError):
        load_mission_data(folder)
    folder = copied_data(tmp_path)
    rain = pd.read_csv(folder / "rainfall_annual.csv")
    rain.loc[0, "valid_months"] = 11
    rain.to_csv(folder / "rainfall_annual.csv", index=False)
    with pytest.raises(ValueError):
        load_mission_data(folder)


def test_pending_template_cannot_claim_verified(tmp_path):
    import json
    folder = copied_data(tmp_path)
    meta_path = folder / "metadata_TEMPLATE.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["verification_status"] = "verified"
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    assert load_mission_data(folder).verification == "pending"


def test_malformed_geojson_rejected(tmp_path):
    import json
    folder = copied_data(tmp_path)
    path = folder / "study_areas.geojson"
    geo = json.loads(path.read_text())
    geo["features"][0]["geometry"]["coordinates"][0].pop()
    path.write_text(json.dumps(geo), encoding="utf-8")
    with pytest.raises(ValueError):
        load_mission_data(folder)


def test_case_progress_hypothesis_and_passport(data):
    case = new_case("mission_a", "area_a", (2005, 2024))
    case2 = record_case_step(case, "evidence", "ndvi")
    case2 = record_case_step(case2, "evidence", "ndvi")
    assert case["evidence"] == [] and case2["evidence"] == ["ndvi"]
    case3 = record_case_step(case2, "hypothesis", "rainfall")
    case3 = record_case_step(case3, "decision", "field_visit")
    assert evaluate_hypothesis(data, "area_a", "rainfall", (2005, 2024))["conclusion"].startswith("HYPOTHESIS")
    report = impact_passport(case3, data)
    assert case3["case_id"] in report
    assert "Impact Passport" in report
    assert "not proof" in report.lower() or "not an intervention" in report.lower()


def test_rule_interpreter_no_fabricated_cause(data, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    a = explain_investigation(data, "area_a", "irrigation", (2005, 2024))
    assert "Deterministic" in a["engine"]
    assert "irrigation" in a["counter_evidence"].lower()
    result = interrogate(data, "area_a", "irrigation", (2005, 2024))
    assert result["llm_status"] == "not_connected"


def test_model_output_numeric_text_rejected(data):
    import json
    def inappropriate(_):
        obj = {"plausible": "The missing data might help123.",
               "counter_evidence": "There are alternative explanations.",
               "unknown": "Agricultural history is not available.",
               "next_data": "Collect local records from observers."}
        return {"output": [{"type": "message",
                            "content": [{"type": "output_text", "text": json.dumps(obj)}]}]}
    result = interrogate(data, "area_b", "unknown", (2005, 2024),
                         key="test-key", requester=inappropriate)
    assert result["llm_status"] == "unavailable_fallback"
    assert result["llm_notes"] is None


def test_photo_scrub_and_local_groundtruth(tmp_path):
    photo = BytesIO()
    Image.new("RGB", (15, 15), (23, 89, 44)).save(photo, format="PNG")
    clean, suffix, digest = sanitize_photo(photo.getvalue(), "field.png")
    assert suffix == ".jpg" and len(digest) == 64
    with Image.open(BytesIO(clean)) as picture:
        assert not picture.getexif()
    case = new_case("mission_b", "area_b", (2005, 2024))
    with pytest.raises(ValueError):
        submit_report(case_id=case["case_id"], area="area_b",
                      observed_date=date.today().isoformat(), category="Other",
                      description="Field observation.", source_note="", consent=False,
                      root=tmp_path)
    report_id = submit_report(
        case_id=case["case_id"], area="area_b",
        observed_date=date.today().isoformat(), category="Other",
        description="Visible vegetation was inspected in the field.",
        source_note="Local observer", consent=True, root=tmp_path,
        photo=photo.getvalue(), photo_filename="field.png",
        approx_location=(31.8512, 35.4632), location_consent=True)
    assert report_status(report_id, root=tmp_path) == "PENDING"
    assert len(list_pending(root=tmp_path)) == 1
    with pytest.raises(ValueError):
        submit_report(case_id=case["case_id"], area="area_b",
                      observed_date=date.today().isoformat(), category="Other",
                      description="An entirely different report.", source_note="",
                      consent=True, root=tmp_path)
    review_report(report_id, "VERIFIED", root=tmp_path)
    assert report_status(report_id, root=tmp_path) == "VERIFIED"
    with pytest.raises(ValueError):
        review_report(report_id, "REJECTED", root=tmp_path)


def test_operational_metrics_are_persisted(tmp_path):
    case = new_case("mission_a", "area_a", (2005, 2024))
    record_activity(case["case_id"], "ACTION_RECORDED", "monitor", root=tmp_path)
    record_activity(case["case_id"], "ACTION_RECORDED", "monitor", root=tmp_path)
    record_activity(case["case_id"], "INVESTIGATION_COMPLETED", "mission_a", root=tmp_path)
    m = impact_metrics(root=tmp_path)
    assert m["actions_recorded"] == 1
    assert m["investigations_completed"] == 1
    assert m["field_verified"] == 0
    assert m["verified_environmental_impact"] == "Impact not yet verified."


def test_webxr_scene_uses_real_annual_observations(data):
    page = scene_html(data, "area_a", 2024)
    assert "0.35173537554554934" in page
    assert "Illustrative landscape" in page
    assert 'raycaster="objects: .station"' in page
    assert "https://aframe.io/" in page


def test_bad_inputs_cannot_mutate_case_or_extract_data(data):
    with pytest.raises(ValueError):
        new_case("not_a_mission", "area_a", (2005, 2024))
    with pytest.raises(ValueError):
        record_case_step(new_case("mission_a", "area_a", (2005, 2024)),
                         "evidence", "fictional_evidence")
    with pytest.raises(ValueError):
        data.observation("area_c", 2024)


def test_compare_allows_validated_research_preview():
    """Compare real local CSV values while maintaining PENDING provenance."""
    from modules.comparison import annual_series, compare_regions
    ctx = load_ui_context("local", "area_a", 2005, 2024)
    assert ctx.ready and ctx.metadata["verification_status"] == "pending"
    series = annual_series(ctx, "ndvi", "area_a", 2005, 2024)
    assert series.loc[series.year == 2005, "ndvi"].iloc[0] == pytest.approx(
        0.16515122987658773
    )
    result = compare_regions(ctx, ("area_a", "area_b"), "ndvi", 2005, 2024)
    assert result["status"] != "unavailable"
    assert result["common_years"] == list(range(2005, 2025))
