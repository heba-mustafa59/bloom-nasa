"""BLOOM Action Pathway: evidence → field check → conditional response → monitoring.

A goal-driven decision-support prototype. It never diagnoses causes from
NDVI/rainfall, recommends field interventions as settled facts, generates
unobserved future measurements, or treats user reports as verified evidence.
"""
from __future__ import annotations

from dataclasses import dataclass

from modules.area_advisor import GOAL_LABELS, Recommendation
from modules.investigation_case import AREA_NAMES, CaseData, START_YEAR, END_YEAR, annual_series

FIELD_SIGNALS = {
    "not_checked": "Not checked on the ground",
    "water_access": "Possible water-access or irrigation issue (user observation)",
    "crop_cycle": "Possible harvest or seasonal crop cycle (user observation)",
    "land_use": "Possible land-use change (user observation)",
    "unclear": "Observation made, cause still unclear",
}

GENERAL_CHECKS = (
    "Confirm GPS location and that the field site lies inside the selected study polygon.",
    "Photograph vegetation and record a date, crop type and growing/harvest stage.",
    "Check whether the annual MODIS NDVI composites are usable and compare matching seasons.",
    "Ask a local farmer/field expert about irrigation, harvest dates and recent land-use changes.",
)
FOLLOW_UP = (
    "Save a dated, georeferenced field note and photographs as baseline context.",
    "Revisit at the same crop stage and season; collect comparable field observations.",
    "When genuinely new satellite observations are available, re-extract NDVI using the same polygon and quality method, then compare with a suitable baseline.",
    "Record what was actually implemented. Do not claim improved outcomes without new measurements.",
)


@dataclass(frozen=True)
class ActionPlan:
    area_id: str
    goal: str
    year: int
    field_signal: str
    advisor_winner: str | None
    ndvi: float
    rainfall_mm: float
    baseline_ndvi: float
    recent_mean_ndvi: float
    measured_change: float
    evidence: tuple[str, ...]
    ground_checks: tuple[str, ...]
    conditional_action: str
    monitoring: tuple[str, ...]
    interpretation: str
    status: str


def _response(signal: str) -> tuple[tuple[str, ...], str]:
    if signal == "water_access":
        return (
            GENERAL_CHECKS + (
                "With a qualified local expert, examine water supply records and signs of soil moisture stress.",
            ),
            "Only if a local assessment confirms water stress: consult water/agriculture specialists about a small, lawful, water-efficient intervention before any wider rollout.",
        )
    if signal == "crop_cycle":
        return (
            GENERAL_CHECKS + (
                "Compare the satellite observation window with documented sowing, harvest and fallow dates.",
            ),
            "If the difference is explained by a normal crop cycle, document the seasonal context and do not label the area degraded or propose restoration solely from NDVI.",
        )
    if signal == "land_use":
        return (
            GENERAL_CHECKS + (
                "Inspect dated land-use records and historical imagery for the same study boundary.",
            ),
            "If land conversion is independently confirmed, refer the case to local planning/environmental specialists before suggesting any land-management response.",
        )
    if signal == "unclear":
        return (
            GENERAL_CHECKS + (
                "Collect additional field and land-management context before choosing a specific action.",
            ),
            "The appropriate intervention is unknown; collect evidence and request a local expert review before proposing one.",
        )
    return (
        GENERAL_CHECKS,
        "No intervention is prescribed yet. Complete the field checks, confirm a cause independently, and only then design a locally appropriate response.",
    )


def build_action_plan(
    data: CaseData,
    recommendation: Recommendation,
    area_id: str,
    field_signal: str = "not_checked",
) -> ActionPlan:
    """Build a transparent action path from uploaded measurements and user input."""
    if area_id not in AREA_NAMES:
        raise ValueError("Unknown study area")
    if recommendation.goal not in GOAL_LABELS:
        raise ValueError("Unknown advisor goal")
    if type(recommendation.year) is not int or not START_YEAR <= recommendation.year <= END_YEAR:
        raise ValueError("Advisor year outside the observed study window")
    if field_signal not in FIELD_SIGNALS:
        raise ValueError("Unknown field signal")

    series = annual_series(data, area_id).set_index("year")
    year = recommendation.year
    readings = series.loc[year]
    ndvi = float(readings["ndvi"])
    rain = float(readings["rainfall_mm"])
    baseline = float(series.loc[START_YEAR, "ndvi"])
    start = max(START_YEAR, year - 2)
    recent = float(series.loc[start:year, "ndvi"].mean())
    difference = ndvi - baseline

    # The goal changes what to investigate, not how the source numbers are read.
    if recommendation.goal == "current_greenness":
        motivation = (
            f"Compare the selected year's NDVI against the other study polygon, "
            f"then check land cover and crop-stage comparability for {year}."
        )
    elif recommendation.goal == "long_term_greening":
        motivation = (
            "Investigate the long-run vegetation trajectory, using annual observations "
            "and ground information. A fitted slope cannot identify the cause."
        )
    else:
        motivation = (
            f"Screen the area for a field visit using the {start}–{year} "
            "annual mean NDVI, without diagnosing degradation."
        )

    priority_note = (
        f"Area Advisor selected {AREA_NAMES[area_id]} for this specific goal."
        if recommendation.winner == area_id
        else (
            "Area Advisor did not establish a winner for this goal. "
            "This area is a user-selected investigation focus."
            if recommendation.winner is None
            else f"This is a user-selected focus, not Area Advisor's suggested area ({AREA_NAMES[recommendation.winner]})."
        )
    )
    checks, intervention = _response(field_signal)
    return ActionPlan(
        area_id=area_id,
        goal=recommendation.goal,
        year=year,
        field_signal=field_signal,
        advisor_winner=recommendation.winner,
        ndvi=ndvi,
        rainfall_mm=rain,
        baseline_ndvi=baseline,
        recent_mean_ndvi=recent,
        measured_change=difference,
        evidence=(
            f"Uploaded polygon-mean NDVI ({year}): {ndvi:.4f}; rainfall: {rain:.1f} mm.",
            f"Uploaded NDVI at {START_YEAR}: {baseline:.4f}; endpoint difference: {difference:+.4f} NDVI units.",
            f"NDVI mean over {start}–{year}: {recent:.4f}.",
            motivation,
            priority_note,
        ),
        ground_checks=checks,
        conditional_action=intervention,
        monitoring=FOLLOW_UP,
        interpretation=(
            "The observed values describe these two polygons but cannot verify "
            "crop suitability, degradation, cause of change or efficacy of any intervention."
        ),
        status="FIELD VERIFICATION NEEDED",
    )


def action_plan_markdown(data: CaseData, plan: ActionPlan, completed: tuple[str, ...] = ()) -> str:
    """Export a transparent field checklist; ticks indicate USER input, not validation."""
    unknown = set(completed) - set(plan.ground_checks)
    if unknown:
        raise ValueError("Completed checks must be from the prescribed checklist")
    lines = [
        "# BLOOM — From Discovery to Action",
        f"Area: {AREA_NAMES[plan.area_id]}",
        f"Investigation goal: {GOAL_LABELS[plan.goal]}",
        f"Selected year: {plan.year}",
        f"Status: {plan.status}",
        f"Source status: {'verified in metadata' if data.verified else 'uploaded CSVs, independent export provenance review pending'}",
        "",
        "## 1 — DETECT: observations and rationale",
        *[f"- {item}" for item in plan.evidence],
        "",
        "## 2 — VERIFY: field checklist",
        *[f"- [{'x' if item in completed else ' '}] {item}" for item in plan.ground_checks],
        "",
        "## 3 — ACT: conditional response",
        f"User-reported field clue (not independently verified): {FIELD_SIGNALS[plan.field_signal]}",
        plan.conditional_action,
        "",
        "## 4 — MEASURE: impact verification",
        *[f"- {item}" for item in plan.monitoring],
        "",
        "## Scientific boundaries",
        f"- {plan.interpretation}",
        "- User-checked tasks are self-reported and are not field-verification proof.",
        "- The database currently ends in 2024; no later impact values have been collected.",
        "- Coarse GPM rainfall estimates may not distinguish neighboring polygons.",
    ]
    return "\n".join(lines) + "\n"
