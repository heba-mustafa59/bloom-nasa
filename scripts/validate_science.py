#!/usr/bin/env python3
"""Read-only, reproducible audit of BLOOM's uploaded study files.

Run from the repository root:
    python scripts/validate_science.py --report docs/generated_science_audit.md

Optionally compare *independently obtained* Earth Engine exports:
    python scripts/validate_science.py --original-dir /path/to/ee_exports \
        --evidence /path/to/filled_evidence.json --report /tmp/audit.md \
        --json /tmp/audit.json

The audit never writes to data/, metadata.json, or the Streamlit UI. It never
automatically grants NASA-source verification, even if copied files match.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.investigation_case import AREA_NAMES, END_YEAR, START_YEAR, load_case_data
from modules.trend_analysis import analyze_trend

INPUT_FILES = ("ndvi_annual.csv", "rainfall_annual.csv", "study_areas.geojson")
REQUIRED_COLUMNS = {
    "ndvi_annual.csv": ("year", "area_id", "ndvi", "valid_observations"),
    "rainfall_annual.csv": ("year", "area_id", "rainfall_mm", "valid_months"),
}
EXPECTED_DATASETS = {
    "vegetation": "MODIS/061/MOD13Q1",
    "precipitation": "NASA/GPM_L3/IMERG_MONTHLY_V07",
}
REQUIRED_SCRIPT_FRAGMENTS = (
    "MODIS/061/MOD13Q1",
    "NASA/GPM_L3/IMERG_MONTHLY_V07",
    "SummaryQA",
    "multiply(0.0001)",
    "valid_months",
    "next.difference(first, 'hour')",
)


def file_digest(path: Path) -> str:
    """SHA-256 of the actual committed bytes, not a declaration of NASA origin."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_polygons(geojson: dict) -> list[dict]:
    checks = []
    features = geojson.get("features", [])
    if len(features) != 2:
        raise ValueError("Expected two original polygon features")
    for item in features:
        area = item.get("properties", {}).get("area_id", "unknown")
        geometry = item.get("geometry", {})
        kind = geometry.get("type")
        coordinates = geometry.get("coordinates", [])
        polygon_parts = [coordinates] if kind == "Polygon" else coordinates if kind == "MultiPolygon" else []
        if not polygon_parts:
            raise ValueError(f"{area}: empty or unsupported polygon")
        count = 0
        for polygon in polygon_parts:
            if not polygon:
                raise ValueError(f"{area}: polygon has no rings")
            for ring in polygon:
                if len(ring) < 4 or ring[0] != ring[-1]:
                    raise ValueError(f"{area}: unclosed or short polygon ring")
                for pair in ring:
                    if len(pair) < 2:
                        raise ValueError(f"{area}: invalid coordinate pair")
                    lon, lat = float(pair[0]), float(pair[1])
                    if not (math.isfinite(lon) and math.isfinite(lat)):
                        raise ValueError(f"{area}: non-finite coordinate")
                    # This is only a geographic sanity check, NOT field verification.
                    if not (35.3 <= lon <= 35.7 and 31.6 <= lat <= 32.1):
                        raise ValueError(f"{area}: coordinate outside the Jericho region")
                    count += 1
        checks.append({"area_id": area, "closed_rings_and_jericho_bounds": True, "coordinate_count": count})
    return checks


def _manual_slope(years: list[int], values: list[float]) -> float:
    """Independent arithmetic check of the linear trend (per decade)."""
    mx = sum(years) / len(years)
    my = sum(values) / len(values)
    denom = sum((x - mx) ** 2 for x in years)
    if denom == 0:
        raise ValueError("Cannot calculate slope with constant years")
    return 10.0 * sum((x - mx) * (y - my) for x, y in zip(years, values)) / denom


def _series_summary(data) -> dict:
    summaries = {}
    for area in AREA_NAMES:
        summaries[area] = {}
        for kind, table, field in (
            ("ndvi", data.ndvi, "ndvi"),
            ("rainfall", data.rainfall, "rainfall_mm"),
        ):
            series = table.loc[table["area_id"] == area].sort_values("year")
            result = analyze_trend(series, field, START_YEAR, END_YEAR)
            years = [int(v) for v in series["year"]]
            values = [float(v) for v in series[field]]
            independent_slope = _manual_slope(years, values)
            if result["status"] != "success" or not math.isclose(
                independent_slope, float(result["slope_per_decade"]), abs_tol=1e-10
            ):
                raise ValueError(f"{area}/{field}: slope calculation not reproducible")
            summaries[area][kind] = {
                "n_years": len(years),
                "period": [min(years), max(years)],
                "mean": sum(values) / len(values),
                "first": values[0],
                "last": values[-1],
                "endpoint_change": values[-1] - values[0],
                "slope_per_decade": independent_slope,
                "mann_kendall_p_value": result["p_value"],
                "mann_kendall_significant_at_0_05": result["significant"],
                "trend_direction": result["direction"],
            }
    return summaries


def _read_export_csv(path: Path, columns: tuple[str, ...]) -> pd.DataFrame:
    if not path.is_file():
        raise ValueError(f"Missing original export: {path.name}")
    frame = pd.read_csv(path)
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f"{path.name} lacks columns: {sorted(missing)}")
    frame = frame.loc[:, list(columns)].copy()
    if frame.isna().any().any():
        raise ValueError(f"{path.name} contains missing values")
    frame["year"] = pd.to_numeric(frame["year"], errors="raise")
    if not (frame["year"] % 1 == 0).all():
        raise ValueError(f"{path.name}: noninteger years")
    frame["year"] = frame["year"].astype(int)
    if frame.duplicated(["area_id", "year"]).any():
        raise ValueError(f"{path.name}: duplicate area/year records")
    expected = {(area, year) for area in AREA_NAMES for year in range(START_YEAR, END_YEAR + 1)}
    if set(zip(frame["area_id"], frame["year"])) != expected:
        raise ValueError(f"{path.name}: missing or unexpected area/year rows")
    for field in columns[2:]:
        frame[field] = pd.to_numeric(frame[field], errors="raise")
        if not frame[field].map(math.isfinite).all():
            raise ValueError(f"{path.name}: non-finite {field}")
    return frame.set_index(["area_id", "year"]).sort_index()


def _same_coordinates(a: Any, b: Any) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-9)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same_coordinates(x, y) for x, y in zip(a, b))
    return a == b


def _compare_geojson(committed: Path, original: Path) -> dict:
    if not original.is_file():
        return {"match": False, "detail": "Original GeoJSON file missing"}
    try:
        a, b = json.loads(committed.read_text(encoding="utf-8")), json.loads(original.read_text(encoding="utf-8"))
        def features(doc):
            return {f["properties"]["area_id"]: f["geometry"] for f in doc["features"]}
        x, y = features(a), features(b)
        ok = set(x) == set(y) and all(
            x[area]["type"] == y[area]["type"]
            and _same_coordinates(x[area]["coordinates"], y[area]["coordinates"])
            for area in x
        )
        return {
            "match": ok,
            "detail": (
                "Feature IDs and ordered geometry coordinates match (tolerance 1e-9 degrees)"
                if ok else "Feature IDs or ordered coordinates differ; investigate original imported polygons"
            ),
        }
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"match": False, "detail": str(exc)}


def compare_exports(data_dir: Path, original_dir: Path) -> dict:
    """Check the user-supplied exports against the current files.

    Matches prove file/value correspondence ONLY, NOT that the files came
    from Earth Engine or from the intended original polygon import.
    """
    output = {"status": "match", "files": {}, "limitations": (
        "A matching external file is not proof of NASA provenance. Review Earth Engine task logs, source project, and exact imported polygons."
    )}
    for filename, columns in REQUIRED_COLUMNS.items():
        try:
            committed = _read_export_csv(data_dir / filename, columns)
            original = _read_export_csv(original_dir / filename, columns)
            matches = True
            worst_difference = 0.0
            for key in committed.index:
                for field in columns[2:]:
                    value, reference = float(committed.loc[key, field]), float(original.loc[key, field])
                    worst_difference = max(worst_difference, abs(value - reference))
                    if not math.isclose(value, reference, rel_tol=1e-12, abs_tol=1e-10):
                        matches = False
            result = {
                "match": matches,
                "rows_compared": len(committed),
                "max_absolute_difference": worst_difference,
                "sha256_uploaded_file": file_digest(data_dir / filename),
                "sha256_supplied_original": file_digest(original_dir / filename),
            }
        except (ValueError, TypeError, KeyError, OSError) as exc:
            result = {"match": False, "error": str(exc)}
        output["files"][filename] = result
        if not result["match"]:
            output["status"] = "mismatch"
    geo = _compare_geojson(data_dir / "study_areas.geojson", original_dir / "study_areas.geojson")
    output["files"]["study_areas.geojson"] = geo
    if not geo["match"]:
        output["status"] = "mismatch"
    return output


def evidence_review(path: Path | None) -> dict:
    """Read a claim/evidence manifest. Never treat user-entered text as proof."""
    missing = []
    if path is None:
        return {"present": False, "complete_fields": False,
                "missing": ["Original EE project, completed tasks and links, polygon import, independent rerun, reviewer sign-off"],
                "note": "No Earth Engine provenance evidence was supplied"}
    if not path.is_file():
        raise ValueError(f"Evidence manifest missing: {path}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError("Evidence manifest must be a JSON object")
    for name in ("earth_engine_project", "export_utc", "original_polygon_asset"):
        if not str(doc.get(name) or "").strip():
            missing.append(name)
    tasks = doc.get("tasks") or {}
    for name in ("ndvi_annual", "rainfall_annual", "study_areas"):
        entry = tasks.get(name) or {}
        if (
            not str(entry.get("task_id") or "").strip()
            or entry.get("state") != "COMPLETED"
            or not str(entry.get("drive_file_url") or "").strip()
        ):
            missing.append(f"tasks.{name} (completed ID + original export URL)")
    rerun = doc.get("independent_rerun") or {}
    if rerun.get("completed") is not True or not str(rerun.get("evidence_link") or "").strip():
        missing.append("independent_rerun (completed + evidence link)")
    review = doc.get("review") or {}
    if not str(review.get("reviewer") or "").strip() or not str(review.get("reviewed_utc") or "").strip():
        missing.append("review (named reviewer + UTC review date)")
    return {
        "present": True, "complete_fields": not missing, "missing": missing,
        "note": "Manifest fields are self-reported and require independent human inspection; they do not verify source provenance",
    }


def audit(data_dir: Path, original_dir: Path | None = None, evidence: Path | None = None) -> dict:
    """Compile a read-only evidence record; verification status is never upgraded."""
    data_dir = Path(data_dir)
    original_dir = Path(original_dir) if original_dir else None
    data = load_case_data(data_dir)
    polygon_checks = _check_polygons(data.geojson)

    for name, source in EXPECTED_DATASETS.items():
        recorded = (data.metadata.get("datasets") or {}).get(name, {}).get("earth_engine_id")
        if recorded != source:
            raise ValueError(f"Unexpected declared source for {name}: {recorded!r}")
    script = (ROOT / "scripts" / "export_nasa_data.js").read_text(encoding="utf-8")
    for fragment in REQUIRED_SCRIPT_FRAGMENTS:
        if fragment not in script:
            raise ValueError(f"Earth Engine script does not contain expected method: {fragment}")

    source_comparison = (
        compare_exports(data_dir, original_dir)
        if original_dir is not None
        else {"status": "not_provided", "files": {}}
    )
    manifest = evidence_review(evidence)
    blockers = []
    if source_comparison["status"] != "match":
        blockers.append("Original task exports and matching GeoJSON have not been demonstrated by this audit")
    if not manifest["complete_fields"]:
        blockers.append("Completed Earth Engine task/project/polygon/reproduction/reviewer evidence is incomplete")
    # A complete manifest + matching files STILL cannot substitute for manual
    # inspection of EE task state, source assets and QA methodology.
    blockers.append("Independent human inspection and explicit sign-off are required before setting metadata to verified")

    return {
        "schema": "bloom-science-audit-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repository_metadata_status": data.metadata.get("verification_status", "unknown"),
        "audit_status": "PENDING_EXTERNAL_PROVENANCE_AND_REVIEW",
        "scope": "2005–2024, original Area A and B, annual NDVI and rainfall",
        "input_sha256": {name: file_digest(data_dir / name) for name in (*INPUT_FILES, "metadata.json")},
        "structural_validation": {
            "status": "passed", "ndvi_rows": len(data.ndvi),
            "rainfall_rows": len(data.rainfall), "polygon_features": len(polygon_checks),
            "geometry_checks": polygon_checks,
            "declared_data_products_match_export_script": True,
            "upstream_source_authenticated": False,
        },
        "statistics": _series_summary(data),
        "independent_export_comparison": source_comparison,
        "evidence_manifest": manifest,
        "blockers": blockers,
        "cautions": [
            "Significant Mann–Kendall trend is not proof of NASA-file authenticity or causation.",
            "Mann–Kendall assumes independent observations; temporal autocorrelation is not corrected.",
            "NDVI data represent annually averaged polygon-level observations, not individual pixels.",
            "GPM IMERG is spatially coarser than MODIS NDVI; close polygons may share rainfall pixels.",
            "An original Earth Engine project/task ID cannot be invented or recovered from uploaded CSVs.",
        ],
    }


def markdown_report(result: dict) -> str:
    lines = [
        "# BLOOM — Reproducible Scientific Data Audit",
        f"Generated (UTC): {result['generated_utc']}",
        f"Study: {result['scope']}",
        f"Result: **{result['audit_status']}**",
        f"Repository metadata state: **{result['repository_metadata_status']}** (NOT changed)",
        "",
        "## Structural / local verification",
        f"- File checks: **{result['structural_validation']['status']}**.",
        f"- Records: NDVI {result['structural_validation']['ndvi_rows']}; rainfall {result['structural_validation']['rainfall_rows']}.",
        f"- Geometry: {result['structural_validation']['polygon_features']} original polygons, closed rings and Jericho-area coordinate sanity checks.",
        "- Declared dataset identifiers and export-script markers are consistent, but script presence is not a NASA export execution record.",
        "",
        "## Trends reproduced from the uploaded CSV files (NOT source authenticated)",
        "| Area | Variable | Mean | First | Last | Endpoint Δ | Slope / decade | Mann–Kendall p | Significant at 0.05? |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for area, metrics in result["statistics"].items():
        for field, stat in metrics.items():
            lines.append(
                f"| {AREA_NAMES[area]} | {field} | {stat['mean']:.6f} | {stat['first']:.6f} | "
                f"{stat['last']:.6f} | {stat['endpoint_change']:+.6f} | {stat['slope_per_decade']:+.6f} | "
                f"{stat['mann_kendall_p_value']:.6g} | {stat['mann_kendall_significant_at_0_05']} |"
            )
    lines += [
        "",
        "## Comparison with independently supplied Earth Engine exports",
        f"Status: **{result['independent_export_comparison']['status']}**",
    ]
    for filename, detail in result["independent_export_comparison"]["files"].items():
        note = detail.get("detail") or detail.get("error") or ("rows=" + str(detail.get("rows_compared")))
        outcome = "MATCH" if detail.get("match") else "MISMATCH"
        lines.append(f"- {filename}: {outcome}; {note}")
    lines += [
        "",
        "## Upstream provenance and outstanding actions",
        f"Evidence manifest supplied: {result['evidence_manifest']['present']}",
        f"Evidence fields complete: {result['evidence_manifest']['complete_fields']}",
        *[f"- Missing: {item}" for item in result["evidence_manifest"]["missing"]],
        *[f"- Blocker: {item}" for item in result["blockers"]],
        "",
        "## Scientific interpretation limits",
        *[f"- {item}" for item in result["cautions"]],
        "",
        "**Decision:** Do not change metadata.json to verified based on this automated report. "
        "Only an authorized reviewer can sign off after independently examining real Earth Engine tasks, exports, exact polygons, and rerun results.",
        "",
        "## Input SHA-256 checksums (local file identity only)",
        *[f"- {name}: \`{value}\`" for name, value in result["input_sha256"].items()],
        "",
    ]
    return "\n".join(lines)


def _write(path: Path, content: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data", help="Current uploaded files")
    parser.add_argument("--original-dir", type=Path, help="Unmodified original completed Earth Engine task outputs")
    parser.add_argument("--evidence", type=Path, help="Completed provenance evidence manifest")
    parser.add_argument("--report", type=Path, help="Write Markdown report to the specified path")
    parser.add_argument("--json", type=Path, dest="json_file", help="Write JSON audit to the specified path")
    args = parser.parse_args(argv)
    try:
        result = audit(args.data_dir, args.original_dir, args.evidence)
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"BLOOM SCIENCE AUDIT FAILED: {exc}", file=sys.stderr)
        return 2
    report = markdown_report(result)
    if args.report:
        _write(args.report, report)
    if args.json_file:
        _write(args.json_file, json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(report)
    # Pending source evidence is expected and NOT an integrity-test failure.
    # Proven mismatch IS a failure and should halt downstream review.
    return 2 if result["independent_export_comparison"]["status"] == "mismatch" else 0


if __name__ == "__main__":
    raise SystemExit(main())
