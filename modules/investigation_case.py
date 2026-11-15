"""BLOOM investigation helpers: uploaded observations remain provisional until verified."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from modules.mystery_engine import analyze_mystery
from modules.trend_analysis import analyze_trend

ROOT = Path(__file__).resolve().parents[1]
AREA_NAMES = {"area_a": "Area A · Eastern polygon", "area_b": "Area B · Western polygon"}
START_YEAR, END_YEAR = 2005, 2024


@dataclass
class CaseData:
    ndvi: pd.DataFrame
    rainfall: pd.DataFrame
    geojson: dict
    metadata: dict

    @property
    def verified(self) -> bool:
        return self.metadata.get("verification_status") == "verified"


def _load_table(path: Path, field: str, quality_col: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"year", "area_id", field, quality_col}
    if not required.issubset(df.columns):
        raise ValueError(f"{path.name}: missing columns {sorted(required - set(df.columns))}")
    if df[list(required)].isna().any().any():
        raise ValueError(f"{path.name}: missing observations; they must not be zero-filled")
    df = df.copy()
    for col in ("year", field, quality_col):
        df[col] = pd.to_numeric(df[col], errors="raise")
    if not (df["year"] % 1 == 0).all():
        raise ValueError(f"{path.name}: non-integer year")
    df["year"] = df["year"].astype(int)
    if df.duplicated(["area_id", "year"]).any():
        raise ValueError(f"{path.name}: duplicate area/year rows")
    expected = {(area, year) for area in AREA_NAMES for year in range(START_YEAR, END_YEAR + 1)}
    actual = set(zip(df["area_id"], df["year"]))
    if actual != expected:
        raise ValueError(f"{path.name}: expected exactly 20 years for each original study area")
    if field == "ndvi" and not df[field].between(-1, 1).all():
        raise ValueError("NDVI outside [-1,1]")
    if field == "rainfall_mm" and (df[field] < 0).any():
        raise ValueError("Negative annual rainfall")
    if quality_col == "valid_observations" and not (
        (df[quality_col] >= 1) & (df[quality_col] <= 24) & (df[quality_col] % 1 == 0)
    ).all():
        raise ValueError("Invalid NDVI observation counts")
    if quality_col == "valid_months" and not (df[quality_col] == 12).all():
        raise ValueError("Incomplete rainfall year")
    return df.sort_values(["area_id", "year"]).reset_index(drop=True)


def load_case_data(data_dir: str | Path | None = None) -> CaseData:
    folder = Path(data_dir) if data_dir is not None else ROOT / "data"
    ndvi = _load_table(folder / "ndvi_annual.csv", "ndvi", "valid_observations")
    rainfall = _load_table(folder / "rainfall_annual.csv", "rainfall_mm", "valid_months")
    with (folder / "study_areas.geojson").open(encoding="utf-8") as f:
        geojson = json.load(f)
    with (folder / "metadata.json").open(encoding="utf-8") as f:
        metadata = json.load(f)
    if not isinstance(metadata, dict):
        raise ValueError("metadata.json must be an object")
    features = geojson.get("features", []) if isinstance(geojson, dict) else []
    if not isinstance(geojson, dict) or geojson.get("type") != "FeatureCollection" or len(features) != len(AREA_NAMES):
        raise ValueError("Expected GeoJSON FeatureCollection with Area A/B")
    ids = {f.get("properties", {}).get("area_id") for f in features}
    if ids != set(AREA_NAMES):
        raise ValueError("GeoJSON area identifiers do not match CSVs")
    for f in features:
        if f.get("geometry", {}).get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError("Invalid polygon geometry")
    return CaseData(ndvi, rainfall, geojson, metadata)


def annual_series(data: CaseData, area_id: str) -> pd.DataFrame:
    if area_id not in AREA_NAMES:
        raise ValueError("Unknown study area")
    nd = data.ndvi.loc[data.ndvi.area_id == area_id, ["year", "ndvi"]]
    ra = data.rainfall.loc[data.rainfall.area_id == area_id, ["year", "rainfall_mm"]]
    return nd.merge(ra, on="year", how="inner", validate="one_to_one").sort_values("year")


def _in_ring(lon: float, lat: float, ring: list) -> bool:
    """Ray casting for GeoJSON [longitude, latitude] ring, boundary inclusive."""
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        x1, y1 = ring[j][:2]
        x2, y2 = ring[i][:2]
        cross = (x2 - x1) * (lat - y1) - (y2 - y1) * (lon - x1)
        if abs(cross) < 1e-11 and min(x1, x2) - 1e-11 <= lon <= max(x1, x2) + 1e-11 and min(y1, y2) - 1e-11 <= lat <= max(y1, y2) + 1e-11:
            return True
        if ((y1 > lat) != (y2 > lat)) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            inside = not inside
        j = i
    return inside


def _in_geometry(lon: float, lat: float, geometry: dict) -> bool:
    kind = geometry.get("type")
    coords = geometry.get("coordinates")
    polygons = [coords] if kind == "Polygon" else coords if kind == "MultiPolygon" else []
    for polygon in polygons or []:
        if polygon and _in_ring(lon, lat, polygon[0]) and not any(
            _in_ring(lon, lat, hole) for hole in polygon[1:]
        ):
            return True
    return False


def area_at_point(geojson: dict, lat: float, lon: float) -> str | None:
    """Map click selection by exact supplied polygon, not made-up boundaries."""
    for feature in geojson.get("features", []):
        area_id = feature.get("properties", {}).get("area_id")
        if area_id in AREA_NAMES and _in_geometry(lon, lat, feature.get("geometry", {})):
            return area_id
    return None


def investigate(data: CaseData, area_id: str) -> dict:
    if area_id not in AREA_NAMES:
        raise ValueError("Unknown study area")
    nd = data.ndvi.loc[data.ndvi.area_id == area_id]
    ra = data.rainfall.loc[data.rainfall.area_id == area_id]
    return {
        "ndvi_trend": analyze_trend(nd, "ndvi", START_YEAR, END_YEAR),
        "rainfall_trend": analyze_trend(ra, "rainfall_mm", START_YEAR, END_YEAR),
        "mystery": analyze_mystery(data.ndvi, data.rainfall, area_id),
    }


def _describe_trend(result: dict) -> str:
    if result.get("status") != "success":
        return "Insufficient observations to estimate a trend."
    slope = result.get("slope_per_decade")
    rate = "not available" if slope is None else f"{slope:+.4f} per decade"
    if result.get("significant") is True:
        return f"Statistically supported {result.get('direction')} trend (linear slope {rate}; exploratory p-value {result.get('p_value'):.4g})."
    return f"No statistically supported monotonic trend detected (linear slope {rate}); this does not establish stability."


def case_report(data: CaseData, area_id: str, findings: dict) -> str:
    annual = annual_series(data, area_id)
    first, last = annual.iloc[0], annual.iloc[-1]
    mystery = findings["mystery"]
    verification = "VERIFIED" if data.verified else "PROVISIONAL — source provenance not independently verified"
    lines = [
        "# BLOOM — Investigation Brief",
        f"Study area: {AREA_NAMES[area_id]} ({area_id})",
        f"Study period: {START_YEAR}–{END_YEAR}",
        f"Data status: {verification}",
        "",
        "## What changed?",
        f"Recorded endpoint NDVI: {first['ndvi']:.4f} ({int(first['year'])}) → {last['ndvi']:.4f} ({int(last['year'])}).",
        "Endpoint comparison is not a trend-significance test.",
        f"NDVI: {_describe_trend(findings['ndvi_trend'])}",
        f"Rainfall: {_describe_trend(findings['rainfall_trend'])}",
        "",
        "## Can rainfall alone explain the pattern?",
        f"Model status: {mystery.get('model_status', 'unknown')}.",
        f"Model verdict: {mystery.get('verdict', 'Not evaluated')}.",
        "A rainfall-only model is not evidence of causation or irrigation.",
        "",
        "## Suggested field checks (not verified explanations)",
        "- Review crop types, irrigation access, land-use changes, and field photos.",
        "- Compare seasonal imagery and MODIS quality masks before interpreting endpoints.",
        "- Confirm the original Earth Engine polygon and export task provenance.",
        "",
        "## Caveats",
        "- MODIS 250 m and GPM roughly 11 km resolutions differ; nearby polygons can share precipitation pixels.",
        "- Annual aggregation can hide seasonality; serial correlation can affect unmodified Mann–Kendall p-values.",
        "- Findings are exploratory and should not be treated as field-validated conclusions.",
    ]
    return "\n".join(lines) + "\n"
