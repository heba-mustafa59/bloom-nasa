"""BLOOM Discovery and Time Machine: computed exclusively from uploaded NDVI values.

Colored study polygons represent annual *polygon mean* NDVI, NOT a satellite
raster. Year-to-year comparisons are descriptive and do not establish cause
or a statistically significant trend.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from modules.investigation_case import AREA_NAMES, END_YEAR, START_YEAR, CaseData, annual_series

# A fixed, interpretable scale across every year (no annual re-normalization).
NDVI_BANDS = (
    (0.00, "#A98269"),
    (0.15, "#CDBA85"),
    (0.20, "#C8D99C"),
    (0.25, "#A2C784"),
    (0.30, "#72AD6B"),
    (0.35, "#478D59"),
    (float("inf"), "#1F5F40"),
)


def ndvi_color(value: float) -> str:
    """Return the same color for the same NDVI reading in every year."""
    if not isfinite(value) or not -1 <= value <= 1:
        raise ValueError("NDVI must be a finite number within [-1, 1]")
    for upper, color in NDVI_BANDS:
        if value < upper:
            return color
    raise AssertionError("Unreachable NDVI range")


@dataclass(frozen=True)
class AreaChange:
    area_id: str
    first_ndvi: float
    selected_ndvi: float

    @property
    def difference(self) -> float:
        return self.selected_ndvi - self.first_ndvi


@dataclass(frozen=True)
class Discovery:
    initial_year: int
    final_year: int
    changes: dict[str, AreaChange]
    first_leader: str | None
    final_leader: str | None
    switched_leader: bool


def snapshot(data: CaseData, year: int, baseline_year: int = START_YEAR) -> dict[str, AreaChange]:
    if type(year) is not int or not START_YEAR <= year <= END_YEAR:
        raise ValueError(f"Expected year in {START_YEAR}–{END_YEAR}")
    if type(baseline_year) is not int or not START_YEAR <= baseline_year <= year:
        raise ValueError(f"Expected baseline in {START_YEAR}–{year}")
    result = {}
    for area in AREA_NAMES:
        s = annual_series(data, area).set_index("year")
        if year not in s.index or baseline_year not in s.index:
            raise ValueError("Missing original study observation")
        result[area] = AreaChange(
            area_id=area,
            first_ndvi=float(s.loc[baseline_year, "ndvi"]),
            selected_ndvi=float(s.loc[year, "ndvi"]),
        )
    return result


def _leader(changes: dict[str, AreaChange], field: str) -> str | None:
    vals = {area: getattr(row, field) for area, row in changes.items()}
    ordered = sorted(vals, key=vals.get, reverse=True)
    if len(ordered) < 2 or abs(vals[ordered[0]] - vals[ordered[1]]) < 1e-6:
        return None
    return ordered[0]


def discovery(data: CaseData) -> Discovery:
    changes = snapshot(data, END_YEAR)
    start = _leader(changes, "first_ndvi")
    end = _leader(changes, "selected_ndvi")
    return Discovery(
        initial_year=START_YEAR,
        final_year=END_YEAR,
        changes=changes,
        first_leader=start,
        final_leader=end,
        switched_leader=start is not None and end is not None and start != end,
    )
