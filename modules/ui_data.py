
"""Read BLOOM UI inputs without changing scientific back-end contracts.

Synthetic values are generated only in the explicitly marked demo mode.
The verified mode delegates to the existing strict data loader.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

import pandas as pd

AREA_LABELS = {
    "area_a": "Area A",
    "area_b": "Area B"
}

YEARS = (2005, 2024)


@dataclass
class UIContext:
    mode: str
    area_id: str
    start_year: int
    end_year: int
    ndvi_df: pd.DataFrame
    rainfall_df: pd.DataFrame
    geojson: dict
    metadata: dict
    error: str | None = None

    @property
    def is_demo(self) -> bool:
        return self.mode == "demo"

    @property
    def ready(self) -> bool:
        return (
            not self.ndvi_df.empty
            and not self.rainfall_df.empty
        )

    def area_data(
        self,
        value: str,
        area_id: str | None = None,
        *,
        full_period: bool = False
    ) -> pd.DataFrame:

        data = (
            self.ndvi_df
            if value == "ndvi"
            else self.rainfall_df
        )

        if (
            data.empty
            or not {"year", "area_id"}.issubset(data.columns)
        ):
            return pd.DataFrame(
                columns=["year", "area_id", value]
            )

        aid = area_id or self.area_id

        subset = data.loc[
            data["area_id"] == aid
        ].copy()

        if not full_period:
            subset = subset.loc[
                subset["year"].between(
                    self.start_year,
                    self.end_year
                )
            ]

        return subset.sort_values("year")


def synthetic_demo() -> tuple[
    pd.DataFrame,
    pd.DataFrame
]:
    """Deterministic test values, never NASA data."""

    ndvi_rows = []
    rain_rows = []

    for area_id in AREA_LABELS:
        offset = (
            0.0
            if area_id == "area_a"
            else 0.55
        )

        for index, year in enumerate(
            range(YEARS[0], YEARS[1] + 1)
        ):
            rainfall = (
                148
                + 51 * math.sin(index * 1.63 + offset)
                + 29 * math.cos(index * 0.72 + offset)
                + (15 if offset else 0)
            )

            ndvi = (
                0.19
                + 0.00064 * rainfall
                + 0.0018 * index
                + 0.009 * math.sin(index * 2.4 + offset)
                - (0.036 if offset else 0)
            )

            ndvi_rows.append({
                "year": year,
                "area_id": area_id,
                "ndvi": round(ndvi, 5),
                "valid_observations": 21
            })

            rain_rows.append({
                "year": year,
                "area_id": area_id,
                "rainfall_mm": round(rainfall, 2),
                "valid_months": 12
            })

    return (
        pd.DataFrame(ndvi_rows),
        pd.DataFrame(rain_rows)
    )


def load_ui_context(
    mode: str,
    area_id: str,
    start_year: int,
    end_year: int,
    data_dir: str | Path | None = None
) -> UIContext:

    if mode not in ("demo", "local", "verified"):
        raise ValueError(
            "mode must be demo, local or verified"
        )

    if (
        area_id not in AREA_LABELS
        or start_year < YEARS[0]
        or end_year > YEARS[1]
        or start_year > end_year
    ):
        raise ValueError(
            "invalid area or year range"
        )

    if mode == "demo":
        ndvi, rain = synthetic_demo()

        return UIContext(
            mode,
            area_id,
            start_year,
            end_year,
            ndvi,
            rain,
            {},
            {
                "verification_status": "synthetic_demo",
                "study_location": (
                    "Jericho — synthetic interface preview"
                )
            }
        )

    if mode == "local":
        from modules.living_data import load_mission_data

        try:
            mission = load_mission_data(data_dir)
            return UIContext(
                mode, area_id, start_year, end_year,
                mission.ndvi, mission.rainfall, mission.geojson,
                {**mission.metadata, "verification_status": mission.verification}
            )
        except (FileNotFoundError, ValueError, TypeError, KeyError, OSError) as exc:
            return UIContext(
                mode, area_id, start_year, end_year,
                pd.DataFrame(), pd.DataFrame(), {}, {}, str(exc)
            )

    from modules.data_loader import load_datasets

    try:
        if data_dir is None:
            ndvi, rain, geojson, metadata = (
                load_datasets()
            )
        else:
            ndvi, rain, geojson, metadata = (
                load_datasets(data_dir)
            )

        return UIContext(
            mode,
            area_id,
            start_year,
            end_year,
            ndvi,
            rain,
            geojson,
            metadata
        )

    except (
        FileNotFoundError,
        ValueError,
        TypeError,
        KeyError,
        OSError
    ) as exc:
        return UIContext(
            mode,
            area_id,
            start_year,
            end_year,
            pd.DataFrame(),
            pd.DataFrame(),
            {},
            {},
            str(exc)
        )


def trend_for(
    ctx: UIContext,
    field: str,
    area_id: str | None = None
) -> dict:

    from modules.trend_analysis import analyze_trend

    area = ctx.area_data(
        field,
        area_id
    )

    if area.empty:
        return {
            "variable": field,
            "direction": "insufficient_data",
            "significant": None,
            "status": "not_analyzed",
            "n_observations": 0
        }

    return analyze_trend(
        area,
        field,
        ctx.start_year,
        ctx.end_year
    )


def mystery_for(
    ctx: UIContext,
    area_id: str | None = None
) -> dict:
    """Model always uses the full 2005-2024 series."""

    if not ctx.ready:
        return {
            "area_id": area_id or ctx.area_id,
            "model_status": "not_evaluated",
            "validation_r2": None,
            "validation_mae": None,
            "anomalies": [],
            "opposing_trends": None,
            "verdict": "Data unavailable",
            "limitations": []
        }

    from modules.mystery_engine import analyze_mystery

    return analyze_mystery(
        ctx.ndvi_df,
        ctx.rainfall_df,
        area_id or ctx.area_id
    )

