"""Deterministic Living Earth investigation, decisions and evidence trail.

Numbers come from MissionData or existing audited scientific functions.
Hypothesis language is intentionally non-causal.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from uuid import uuid4

from .living_data import AREAS, MissionData
from .trend_analysis import analyze_trend
from .mystery_engine import analyze_mystery

HYPOTHESES = {
    "rainfall": "Rainfall variability might contribute",
    "irrigation": "Irrigation practices might contribute",
    "land_use": "Land-use or harvest changes might contribute",
    "unknown": "Available satellite data may be insufficient",
}
ACTIONS = {
    "field_visit": {
        "name": "Request a field inspection",
        "purpose": "Verify the surface conditions behind the satellite signal",
        "needs": "Access permission, local observer, field notes",
        "benefit": "Adds independent ground observations",
        "limits": "A visit may not explain earlier years",
        "risk": "Privacy, travel and land-access constraints",
    },
    "water_check": {
        "name": "Verify irrigation infrastructure",
        "purpose": "Check whether water management helps explain a hypothesis",
        "needs": "Infrastructure records and authorized site access",
        "benefit": "Tests an unmeasured potential driver",
        "limits": "Satellite NDVI alone cannot establish irrigation",
        "risk": "Avoid inferring private farm practices",
    },
    "soil_moisture": {
        "name": "Collect soil-moisture measurements",
        "purpose": "Add a missing environmental variable",
        "needs": "Appropriate sensors and repeat measurements",
        "benefit": "Helps distinguish precipitation from soil-water availability",
        "limits": "Site readings are not a historical time series",
        "risk": "Measurements may not represent an entire polygon",
    },
    "crop_records": {
        "name": "Review crop and harvest records",
        "purpose": "Explore seasonal or land-management explanations",
        "needs": "Consensually shared, dated land-use records",
        "benefit": "Adds temporal information missing from annual NDVI",
        "limits": "Records may be incomplete or inaccessible",
        "risk": "Commercial confidentiality",
    },
    "hires": {
        "name": "Request higher-resolution observations",
        "purpose": "Investigate sub-polygon spatial variability",
        "needs": "Quality-controlled higher-resolution imagery",
        "benefit": "Tests patterns obscured by MODIS mixed pixels",
        "limits": "Needs additional cloud masking and provenance review",
        "risk": "False spatial precision if processing is weak",
    },
    "monitor": {
        "name": "Continue observing",
        "purpose": "Avoid premature intervention when evidence is uncertain",
        "needs": "Future observations and predefined review threshold",
        "benefit": "Separates short-term fluctuation from sustained change",
        "limits": "May delay identification of a real local problem",
        "risk": "Inaction has opportunity costs",
    },
}


def trends(data: MissionData, area: str, start_year: int = 2005, end_year: int = 2024) -> dict:
    if area not in AREAS or start_year not in range(2005, 2025) or end_year not in range(start_year, 2025):
        raise ValueError("Invalid study selection")
    n = data.ndvi.loc[data.ndvi.area_id == area]
    r = data.rainfall.loc[data.rainfall.area_id == area]
    return {
        "ndvi": analyze_trend(n, "ndvi", start_year, end_year),
        "rainfall": analyze_trend(r, "rainfall_mm", start_year, end_year),
        "mystery": analyze_mystery(data.ndvi, data.rainfall, area),
    }


def endpoint_change(data: MissionData, area: str, year_a: int, year_b: int) -> dict:
    if year_a >= year_b:
        raise ValueError("First year must precede second year")
    a, b = data.observation(area, year_a), data.observation(area, year_b)
    delta = b["ndvi"] - a["ndvi"]
    return {
        "area": area, "start_year": year_a, "end_year": year_b,
        "ndvi_start": a["ndvi"], "ndvi_end": b["ndvi"],
        "ndvi_delta": delta,
        "rainfall_start_mm": a["gpm_rainfall_mm"],
        "rainfall_end_mm": b["gpm_rainfall_mm"],
        "rainfall_delta_mm": b["gpm_rainfall_mm"] - a["gpm_rainfall_mm"],
        "source_ndvi": "data/ndvi_annual.csv (MODIS annual polygon means)",
        "source_rainfall": "data/rainfall_annual.csv (GPM annual polygon means)",
        "verification": data.verification,
    }


def mission_catalog(data: MissionData) -> list[dict]:
    a, b = (endpoint_change(data, area, 2005, 2024) for area in ("area_a", "area_b"))
    # Mission labels are derived from actual endpoints, not unverified causal alerts.
    b_title = ("The Mystery of the Fading Green" if b["ndvi_delta"] < 0
               else "The Changing Green")
    a_title = ("The Greening Mystery" if a["ndvi_delta"] > 0
               else "The Changing Green")
    return [
        {"id": "mission_b", "area": "area_b", "title": b_title, "change": b["ndvi_delta"],
         "question": "What might explain Area B's observed endpoint difference?"},
        {"id": "mission_a", "area": "area_a", "title": a_title, "change": a["ndvi_delta"],
         "question": "What might explain Area A's observed endpoint difference?"},
        {"id": "mission_compare", "area": "area_a", "title": "Two Lands, Different Stories",
         "change": a["ndvi_delta"] - b["ndvi_delta"],
         "question": "Why did the two polygons show different endpoint changes?"},
    ]


def evidence_cards(data: MissionData, area: str, year_a: int, year_b: int) -> list[dict]:
    change = endpoint_change(data, area, year_a, year_b)
    end = data.observation(area, year_b)
    trend = trends(data, area, year_a, year_b)
    return [
        {"id": "ndvi", "label": "OBSERVED / MODIS NDVI",
         "value": f"{change['ndvi_start']:.4f} → {change['ndvi_end']:.4f}",
         "detail": f"Calculated endpoint difference: {change['ndvi_delta']:+.4f}. Mann–Kendall direction: {trend['ndvi']['direction']}.",
         "source": "data/ndvi_annual.csv — polygon average, annual, 250 m native pixels",
         "quality": f"{end['ndvi_valid_observations']} valid composites in {year_b}"},
        {"id": "gpm", "label": "OBSERVED / GPM POLYGON RAINFALL",
         "value": f"{end['gpm_rainfall_mm']:.1f} mm ({year_b})",
         "detail": f"Endpoint rainfall difference: {change['rainfall_delta_mm']:+.1f} mm; annual GPM estimate, not measured field rain.",
         "source": "data/rainfall_annual.csv — polygon aggregation, ~11.1 km pixels",
         "quality": f"{end['gpm_valid_months']} valid months in {year_b}"},
        {"id": "power", "label": "REFERENCE / NASA POWER POINT",
         "value": f"{end['power_point_rainfall_mm']:.1f} mm ({year_b})",
         "detail": "Jericho point reference; a different footprint, NOT substituted for GPM polygon rainfall.",
         "source": "data/nasa_power_jericho_point_rainfall.csv — single point",
         "quality": f"{end['power_point_valid_days']}/{end['power_point_expected_days']} days"},
        {"id": "comparison", "label": "CALCULATED / OTHER AREA",
         "value": f"{('area_b' if area == 'area_a' else 'area_a').upper()}",
         "detail": f"Other polygon endpoint NDVI delta: {endpoint_change(data, 'area_b' if area == 'area_a' else 'area_a', year_a, year_b)['ndvi_delta']:+.4f}.",
         "source": "Both area_id groups in data/ndvi_annual.csv",
         "quality": "Observations are polygon means, not individual plants"},
        {"id": "limits", "label": "UNKNOWN / DATA GAPS",
         "value": "Causal explanation unavailable",
         "detail": "Temperature, irrigation schedules, crop types, soil moisture and field verification are not in the supplied annual CSVs.",
         "source": "data/metadata_TEMPLATE.json and study data schema",
         "quality": f"Provenance status: {data.verification}"},
    ]


def evaluate_hypothesis(data: MissionData, area: str, hypothesis: str, years: tuple[int, int]) -> dict:
    if hypothesis not in HYPOTHESES:
        raise ValueError("Unknown hypothesis")
    trend = trends(data, area, *years)
    d = endpoint_change(data, area, *years)
    if hypothesis == "rainfall":
        support = (f"Observed GPM endpoint difference {d['rainfall_delta_mm']:+.1f} mm; "
                   f"Mann–Kendall rainfall direction: {trend['rainfall']['direction']}.")
        contrary = "Annual GPM and NDVI trends alone do not establish a rainfall mechanism; spatial scales differ."
        missing = "Soil moisture, seasonal rainfall, evapotranspiration and field records."
    elif hypothesis == "irrigation":
        support = "Irrigation could affect NDVI, but no irrigation measurements are supplied."
        contrary = "No measured irrigation data; a rising NDVI is not evidence of irrigation."
        missing = "Permission-based irrigation records and field verification."
    elif hypothesis == "land_use":
        support = "Crop cycles and land management can affect annual vegetation indices."
        contrary = "No dated land-use or harvest observations exist in this dataset."
        missing = "Crop records and validated higher-resolution land-cover time series."
    else:
        support = "Only annual polygon NDVI and rainfall, plus a point-based reference, are present."
        contrary = "Some observable changes are statistically assessable even without causal data."
        missing = "Independent field and contextual measurements."
    return {
        "hypothesis": hypothesis, "label": HYPOTHESES[hypothesis],
        "support": support, "counter_evidence": contrary, "missing": missing,
        "conclusion": "HYPOTHESIS ONLY — causal explanation is not verified.",
        "source": "Validated annual mission datasets and deterministic statistics",
    }


def explain_investigation(data: MissionData, area: str, hypothesis: str,
                          years: tuple[int, int]) -> dict:
    """Rule-based investigation fallback; NOT a remote language model."""
    h = evaluate_hypothesis(data, area, hypothesis, years)
    d = endpoint_change(data, area, *years)
    t = trends(data, area, *years)
    return {
        "engine": "Deterministic evidence interpreter (no external LLM)",
        "observed": f"{area}: NDVI endpoint delta {d['ndvi_delta']:+.4f} from {years[0]} to {years[1]}.",
        "supported_by": ("Annual MODIS NDVI observations in data/ndvi_annual.csv; "
                         f"Mann–Kendall direction {t['ndvi']['direction']} "
                         f"(p={t['ndvi']['p_value']!r})."),
        "plausible": h["support"],
        "counter_evidence": h["counter_evidence"],
        "unknown": h["missing"],
        "next_data": "Verify satellite processing and gather independent field observations.",
        "next_action": "Review decision-room actions and request ground truth before intervention.",
        "source": h["source"],
    }


def new_case(mission_id: str, area: str, years: tuple[int, int]) -> dict:
    if mission_id not in {"mission_a", "mission_b", "mission_compare"} or area not in AREAS:
        raise ValueError("Unknown mission selection")
    if not (2005 <= years[0] < years[1] <= 2024):
        raise ValueError("Invalid investigation period")
    return {
        "case_id": uuid4().hex, "mission_id": mission_id, "area": area,
        "years": list(years), "evidence": [], "hypothesis": None,
        "decision": None, "field_report_id": None, "field_status": "NOT_SUBMITTED",
        "trail": [{"type": "SATELLITE_OBSERVATION", "label": "Investigation opened"}],
    }


def record_case_step(case: dict, item: str, value: str) -> dict:
    """Update a case without mutating the caller; stable across Streamlit reruns."""
    if item not in {"evidence", "hypothesis", "decision", "field_report_id", "field_status"}:
        raise ValueError("Invalid case event")
    updated = {**case, "trail": list(case["trail"]), "evidence": list(case["evidence"])}
    if item == "evidence":
        if value not in {"ndvi", "gpm", "power", "comparison", "limits"}:
            raise ValueError("Unknown evidence card")
        if value not in updated["evidence"]:
            updated["evidence"].append(value)
            updated["trail"].append({"type": "SCIENTIFIC_EVIDENCE", "label": value})
    else:
        if item == "hypothesis" and value not in HYPOTHESES:
            raise ValueError("Unknown hypothesis")
        if item == "decision" and value not in ACTIONS:
            raise ValueError("Unknown action")
        updated[item] = value
        updated["trail"].append({"type": item.upper(), "label": value})
    return updated


def impact_passport(case: dict, data: MissionData) -> str:
    """Self-contained, downloadable HTML; escapes untrusted text."""
    area, a, b = case["area"], *case["years"]
    d = endpoint_change(data, area, a, b)
    evidence = ", ".join(case["evidence"]) or "None collected"
    h = HYPOTHESES.get(case.get("hypothesis"), "Not selected")
    action = ACTIONS.get(case.get("decision"), {}).get("name", "Not selected")
    rows = {
        "Mission ID": case["case_id"],
        "Mission": case["mission_id"],
        "Study area": area, "Years": f"{a}–{b}",
        "NDVI start": f"{d['ndvi_start']:.6f}",
        "NDVI end": f"{d['ndvi_end']:.6f}",
        "Calculated NDVI endpoint delta": f"{d['ndvi_delta']:+.6f}",
        "GPM rainfall endpoint delta (mm)": f"{d['rainfall_delta_mm']:+.3f}",
        "Evidence collected": evidence,
        "Hypothesis (unverified)": h,
        "Proposed next action (not an intervention)": action,
        "Field verification status": case["field_status"],
        "Satellite dataset verification": data.verification,
        "Sources": "ndvi_annual.csv (MODIS); rainfall_annual.csv (GPM); NASA POWER point reference",
        "Limitations": "Annual polygon averages; spatial mismatch; no causal attribution or measured impact",
        "Generated UTC": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    cells = "".join(f"<tr><th>{escape(str(k))}</th><td>{escape(str(v))}</td></tr>" for k, v in rows.items())
    return ("<!doctype html><html lang='en'><meta charset='utf-8'><title>BLOOM Impact Passport</title>"
            "<style>body{font:16px system-ui;max-width:850px;margin:4rem auto;color:#163D2E;"
            "background:#F7F6EF}h1{font-size:2.5rem}table{border-collapse:collapse;width:100%}"
            "th,td{padding:13px;text-align:left;border-bottom:1px solid #d8e4d8}"
            "th{width:40%}</style><h1>BLOOM / Impact Passport</h1><p>"
            "Evidence-to-action investigation record, not proof of environmental impact.</p>"
            f"<table>{cells}</table></html>")
