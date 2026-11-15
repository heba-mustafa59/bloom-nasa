"""Transparent, goal-specific area comparisons using the repository's annual NDVI CSV.

This is decision support over two sampled polygons, not a causal model or
a crop-suitability assessment. Rainfall is reported as context, not a score.
"""
from __future__ import annotations

from dataclasses import dataclass

from modules.investigation_case import (
    AREA_NAMES,
    START_YEAR,
    END_YEAR,
    CaseData,
    annual_series,
)
from modules.trend_analysis import analyze_trend

GOAL_LABELS = {
    "current_greenness": "Greener vegetation in the selected year",
    "long_term_greening": "Stronger supported long-term greening",
    "field_followup": "First area to review: lower recent vegetation",
}
# Tolerance is a comparison/display precision guard, NOT a significance test.
NDVI_TOLERANCE = 1e-6
SLOPE_TOLERANCE = 1e-9


@dataclass(frozen=True)
class Recommendation:
    goal: str
    year: int
    winner: str | None
    values: dict[str, float]
    metric: str
    period: str
    explanation: str
    cautions: tuple[str, ...]

    @property
    def difference(self) -> float:
        a, b = self.values.values()
        return abs(a - b)


def advise_area(data: CaseData, goal: str, year: int) -> Recommendation:
    """Compare existing study areas without fabricating external data or weights.

    A long-term-greening recommendation is withheld unless the winning area's
    own Mann–Kendall p-value < 0.05 and its estimated slope is positive.
    That DOES NOT test the difference between the two area's slopes.
    """
    if goal not in GOAL_LABELS:
        raise ValueError(f"Unsupported comparison goal: {goal}")
    if type(year) is not int or not START_YEAR <= year <= END_YEAR:
        raise ValueError(f"Year must be in {START_YEAR}–{END_YEAR}")

    both = {area: annual_series(data, area) for area in AREA_NAMES}
    values: dict[str, float] = {}
    period = str(year)
    winner = None
    explanation = ""
    metric = "Annual NDVI (unitless)"
    common_cautions = (
        "This compares only Area A and Area B, using uploaded annual polygon averages.",
        "Original NASA extraction provenance and area-to-export correspondence remain pending independent review."
        if not data.verified else "Confirm source provenance and methodology before applying results in the field.",
        "Higher NDVI alone does not prove healthier land, better yields, irrigation access, or suitability for farming.",
        "The two polygons may contain different land uses; GPM rainfall pixels are coarser than MODIS NDVI.",
    )

    if goal == "current_greenness":
        values = {
            area: float(frame.loc[frame["year"] == year, "ndvi"].iloc[0])
            for area, frame in both.items()
        }
        a, b = list(values.values())
        if abs(a - b) > NDVI_TOLERANCE:
            winner = max(values, key=values.get)
            explanation = (
                f"{AREA_NAMES[winner]} has the higher recorded polygon-mean NDVI in {year}. "
                "It is the greener of these two observed areas on this specific annual indicator."
            )
        else:
            explanation = f"The two areas have essentially equal recorded NDVI in {year} at this comparison precision."

    elif goal == "field_followup":
        first_year = max(START_YEAR, year - 2)
        period = f"{first_year}–{year}"
        metric = "Mean annual NDVI over the selected window"
        values = {
            area: float(frame.loc[frame["year"].between(first_year, year), "ndvi"].mean())
            for area, frame in both.items()
        }
        a, b = list(values.values())
        if abs(a - b) > NDVI_TOLERANCE:
            winner = min(values, key=values.get)
            explanation = (
                f"Review {AREA_NAMES[winner]} first: it has the lower average NDVI "
                f"over {period} among the two study polygons. "
                "This is a screening priority for field investigation, NOT proof of damage."
            )
        else:
            explanation = f"Neither area stands out by mean NDVI over {period}; consider both for field review."

    else:  # long_term_greening
        period = f"{START_YEAR}–{END_YEAR}"
        metric = "Linear NDVI slope per decade"
        trends = {
            area: analyze_trend(
                data.ndvi.loc[data.ndvi["area_id"] == area],
                "ndvi",
                START_YEAR,
                END_YEAR,
            )
            for area in AREA_NAMES
        }
        for area, result in trends.items():
            if result.get("status") != "success" or result.get("slope_per_decade") is None:
                raise ValueError(f"Not enough valid observations to assess {AREA_NAMES[area]}")
            values[area] = float(result["slope_per_decade"])
        a, b = list(values.values())
        top = max(values, key=values.get)
        top_result = trends[top]
        if (
            abs(a - b) > SLOPE_TOLERANCE
            and values[top] > 0
            and top_result.get("direction") == "increasing"
            and top_result.get("significant") is True
        ):
            winner = top
            explanation = (
                f"{AREA_NAMES[top]} has the larger positive estimated NDVI slope "
                f"over {period}, and its own Mann–Kendall test supports an increasing trend "
                "(p < 0.05). This does NOT establish that its trend is significantly "
                "different from the other area's trend."
            )
        else:
            explanation = (
                "No defensible positive-trend recommendation under this rule: "
                "the strongest estimated slope does not also pass the "
                "area-specific increasing-trend significance check, or the estimates are tied."
            )
        common_cautions += (
            "The Mann–Kendall test is area-specific; no statistical between-area trend-difference test was performed.",
            "Serial dependence and multiple comparisons can affect prototype p-values.",
        )

    return Recommendation(
        goal=goal, year=year, winner=winner, values=values, metric=metric,
        period=period, explanation=explanation, cautions=common_cautions,
    )


def advisor_report(data: CaseData, choice: Recommendation) -> str:
    """Downloadable transparent recommendation supporting rationale."""
    lines = [
        "# BLOOM — Area Advisor",
        f"Question: {GOAL_LABELS[choice.goal]}",
        f"Period: {choice.period}",
        f"Metric: {choice.metric}",
        f"Data status: {'verified in metadata' if data.verified else 'repository CSVs; provenance verification pending'}",
        "",
        "## Comparison",
    ]
    for area, value in choice.values.items():
        lines.append(f"- {AREA_NAMES[area]}: {value:+.6f}" if choice.goal == "long_term_greening" else f"- {AREA_NAMES[area]}: {value:.6f}")
    lines += [
        "",
        f"## Suggested area: {AREA_NAMES[choice.winner] if choice.winner else 'No recommendation'}",
        choice.explanation,
        "",
        "## Scientific boundaries",
        *[f"- {item}" for item in choice.cautions],
    ]
    return "\n".join(lines) + "\n"
