"""Regression tests for the read-only scientific audit.

Fixtures are copied into tmp_path ONLY; original repository data never change.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil

import pandas as pd
import pytest

from scripts.validate_science import (
    INPUT_FILES,
    ROOT,
    _manual_slope,
    audit,
    compare_exports,
    evidence_review,
    file_digest,
    main,
    markdown_report,
)

DATA_DIR = ROOT / "data"


@pytest.fixture
def independent_files(tmp_path: Path) -> Path:
    folder = tmp_path / "ee_exports"
    folder.mkdir()
    for filename in INPUT_FILES:
        shutil.copyfile(DATA_DIR / filename, folder / filename)
    return folder


def test_current_repository_audit_is_structurally_sound_but_pending():
    result = audit(DATA_DIR)
    assert result["audit_status"] == "PENDING_EXTERNAL_PROVENANCE_AND_REVIEW"
    assert result["repository_metadata_status"] == "pending"
    assert result["structural_validation"]["status"] == "passed"
    assert result["structural_validation"]["ndvi_rows"] == 40
    assert result["structural_validation"]["rainfall_rows"] == 40
    assert result["structural_validation"]["polygon_features"] == 2
    assert result["structural_validation"]["upstream_source_authenticated"] is False
    assert result["independent_export_comparison"]["status"] == "not_provided"
    assert len(result["blockers"]) >= 2
    assert result["statistics"]["area_a"]["ndvi"]["n_years"] == 20
    assert result["statistics"]["area_b"]["rainfall"]["n_years"] == 20


def test_known_recorded_endpoints_and_independent_slope_reproduction():
    result = audit(DATA_DIR)
    area_a = result["statistics"]["area_a"]["ndvi"]
    area_b = result["statistics"]["area_b"]["ndvi"]
    assert area_a["first"] == pytest.approx(0.16515122987658773)
    assert area_a["last"] == pytest.approx(0.35173537554554934)
    assert area_a["slope_per_decade"] == pytest.approx(0.1021039849536616)
    assert area_b["first"] == pytest.approx(0.2635271048007687)
    assert area_b["last"] == pytest.approx(0.2015084997027384)
    assert area_b["slope_per_decade"] == pytest.approx(-0.015446627771444982)
    assert area_a["mann_kendall_significant_at_0_05"] is True
    assert area_b["mann_kendall_significant_at_0_05"] is False
    assert result["statistics"]["area_a"]["rainfall"]["mann_kendall_significant_at_0_05"] is False


def test_matched_copies_are_only_correspondence_not_provenance(independent_files):
    result = compare_exports(DATA_DIR, independent_files)
    assert result["status"] == "match"
    for filename in INPUT_FILES:
        assert result["files"][filename]["match"] is True
    full_audit = audit(DATA_DIR, original_dir=independent_files)
    assert full_audit["audit_status"] == "PENDING_EXTERNAL_PROVENANCE_AND_REVIEW"
    assert "human inspection" in " ".join(full_audit["blockers"])


def test_corrupted_comparison_csv_detected(independent_files):
    path = independent_files / "ndvi_annual.csv"
    frame = pd.read_csv(path)
    frame.loc[(frame["year"] == 2024) & (frame["area_id"] == "area_a"), "ndvi"] = 0.4
    frame.to_csv(path, index=False)
    result = compare_exports(DATA_DIR, independent_files)
    assert result["status"] == "mismatch"
    assert result["files"]["ndvi_annual.csv"]["match"] is False
    assert result["files"]["rainfall_annual.csv"]["match"] is True


def test_wrong_original_polygon_detected(independent_files):
    path = independent_files / "study_areas.geojson"
    geo = json.loads(path.read_text(encoding="utf-8"))
    geo["features"][0]["geometry"]["coordinates"][0][0][0] += 0.01
    path.write_text(json.dumps(geo), encoding="utf-8")
    result = compare_exports(DATA_DIR, independent_files)
    assert result["status"] == "mismatch"
    assert result["files"]["study_areas.geojson"]["match"] is False


def test_incomplete_manifest_stays_pending(independent_files, tmp_path):
    manifest = tmp_path / "evidence.json"
    manifest.write_text(json.dumps({"earth_engine_project": "some-project"}), encoding="utf-8")
    result = audit(DATA_DIR, original_dir=independent_files, evidence=manifest)
    assert result["evidence_manifest"]["present"] is True
    assert result["evidence_manifest"]["complete_fields"] is False
    assert "export_utc" in result["evidence_manifest"]["missing"]
    assert result["audit_status"] == "PENDING_EXTERNAL_PROVENANCE_AND_REVIEW"


def test_filled_self_reported_manifest_does_not_auto_verify(independent_files, tmp_path):
    manifest = tmp_path / "evidence.json"
    manifest.write_text(json.dumps({
        "earth_engine_project": "demo-project",
        "export_utc": "2026-11-15T07:00:00Z",
        "original_polygon_asset": "users/example/areas",
        "tasks": {
            key: {"task_id": "reported-" + key, "state": "COMPLETED", "drive_file_url": "https://example.com/" + key}
            for key in ("ndvi_annual", "rainfall_annual", "study_areas")
        },
        "independent_rerun": {"completed": True, "evidence_link": "https://example.com/rerun"},
        "review": {"reviewer": "example", "reviewed_utc": "2026-11-15T10:00:00Z"},
    }), encoding="utf-8")
    # This fixture is fabricated TEST INPUT ONLY and is NOT production evidence.
    result = audit(DATA_DIR, original_dir=independent_files, evidence=manifest)
    assert result["evidence_manifest"]["complete_fields"] is True
    assert result["audit_status"] == "PENDING_EXTERNAL_PROVENANCE_AND_REVIEW"
    assert result["repository_metadata_status"] == "pending"
    assert result["structural_validation"]["upstream_source_authenticated"] is False


def test_report_and_cli_use_tmp_outputs_and_never_touch_source(tmp_path):
    before = {name: file_digest(DATA_DIR / name) for name in (*INPUT_FILES, "metadata.json")}
    report = tmp_path / "audit.md"
    machine = tmp_path / "audit.json"
    code = main(["--data-dir", str(DATA_DIR), "--report", str(report), "--json", str(machine)])
    assert code == 0
    assert "PENDING_EXTERNAL_PROVENANCE_AND_REVIEW" in report.read_text()
    assert "Mann–Kendall" in report.read_text()
    payload = json.loads(machine.read_text())
    assert payload["statistics"]["area_a"]["ndvi"]["slope_per_decade"] > 0
    assert before == {name: file_digest(DATA_DIR / name) for name in before}


def test_cli_returns_nonzero_on_comparison_mismatch(independent_files):
    frame = pd.read_csv(independent_files / "rainfall_annual.csv")
    frame.loc[0, "rainfall_mm"] += 200
    frame.to_csv(independent_files / "rainfall_annual.csv", index=False)
    result = main(["--data-dir", str(DATA_DIR), "--original-dir", str(independent_files)])
    assert result == 2


def test_invalid_year_or_series_rejected():
    with pytest.raises(ValueError):
        _manual_slope([2024, 2024], [0.2, 0.3])
