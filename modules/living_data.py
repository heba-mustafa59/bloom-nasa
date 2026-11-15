"""Validated research-preview repository for Living Earth Missions.

This module never promotes pending metadata to verified, never synthesizes
observations, and never substitutes NASA POWER point data for polygon GPM.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
YEARS = set(range(2005, 2025))
AREAS = {"area_a", "area_b"}


@dataclass(frozen=True)
class MissionData:
    ndvi: pd.DataFrame
    rainfall: pd.DataFrame
    power_point: pd.DataFrame
    geojson: dict
    metadata: dict
    verification: str

    def observation(self, area: str, year: int) -> dict:
        if area not in AREAS or year not in YEARS:
            raise ValueError("Unsupported study area or year")
        n = self.ndvi.loc[(self.ndvi.area_id == area) & (self.ndvi.year == year)].iloc[0]
        r = self.rainfall.loc[(self.rainfall.area_id == area) & (self.rainfall.year == year)].iloc[0]
        p = self.power_point.loc[self.power_point.year == year].iloc[0]
        return {
            "area_id": area, "year": year,
            "ndvi": float(n.ndvi), "ndvi_valid_observations": int(n.valid_observations),
            "gpm_rainfall_mm": float(r.rainfall_mm), "gpm_valid_months": int(r.valid_months),
            "power_point_rainfall_mm": float(p.rainfall_mm),
            "power_point_valid_days": int(p.valid_days),
            "power_point_expected_days": int(p.expected_days),
            "verification_status": self.verification,
        }


def _annual_csv(path: Path, value: str, extra: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"year", "area_id", value, extra}
    if not required.issubset(df.columns):
        raise ValueError(f"{path.name}: missing {sorted(required - set(df.columns))}")
    if df[list(required)].isna().any().any() or len(df) != 40:
        raise ValueError(f"{path.name}: expected 40 complete annual records")
    years = pd.to_numeric(df["year"], errors="raise")
    if ((years % 1) != 0).any() or not years.map(lambda x: 2005 <= x <= 2024).all():
        raise ValueError(f"{path.name}: invalid years")
    df["year"] = years.astype(int)
    if set(df.area_id) != AREAS or df.duplicated(["area_id", "year"]).any():
        raise ValueError(f"{path.name}: invalid areas or duplicate records")
    if not all(set(g.year) == YEARS for _, g in df.groupby("area_id")):
        raise ValueError(f"{path.name}: missing study years")
    for col in (value, extra):
        df[col] = pd.to_numeric(df[col], errors="raise")
        if not df[col].map(lambda x: pd.notna(x) and abs(x) != float("inf")).all():
            raise ValueError(f"{path.name}: non-finite measurements")
    if value == "ndvi":
        if not df.ndvi.between(-1, 1).all():
            raise ValueError("NDVI outside [-1, 1]")
        if not ((df.valid_observations > 0) & (df.valid_observations <= 24) & (df.valid_observations % 1 == 0)).all():
            raise ValueError("Invalid MODIS composite count")
    else:
        if (df.rainfall_mm < 0).any() or not (df.valid_months == 12).all():
            raise ValueError("Invalid or incomplete GPM rainfall year")
    return df.sort_values(["area_id", "year"]).reset_index(drop=True)


def _power_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"year", "rainfall_mm", "valid_days", "expected_days", "status"}
    if not required.issubset(df.columns) or len(df) != 20 or df[list(required)].isna().any().any():
        raise ValueError("NASA POWER: expected 20 complete point-reference records")
    for col in ("year", "rainfall_mm", "valid_days", "expected_days"):
        df[col] = pd.to_numeric(df[col], errors="raise")
        if not df[col].map(lambda x: pd.notna(x) and abs(x) != float("inf")).all():
            raise ValueError("NASA POWER: non-finite value")
    if (df.year % 1 != 0).any() or set(df.year.astype(int)) != YEARS:
        raise ValueError("NASA POWER: invalid or missing years")
    df["year"] = df.year.astype(int)
    if df.year.duplicated().any():
        raise ValueError("NASA POWER: duplicate year")
    if (df.rainfall_mm < 0).any() or (df.valid_days % 1 != 0).any() or (df.expected_days % 1 != 0).any():
        raise ValueError("NASA POWER: invalid measurements")
    if ((df.valid_days != df.expected_days) | (df.status != "complete")).any():
        raise ValueError("NASA POWER: incomplete point-reference year")
    return df.sort_values("year").reset_index(drop=True)


def _geojson(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("type") != "FeatureCollection" or len(data.get("features", [])) != 2:
        raise ValueError("Expected exactly two GeoJSON study polygons")
    found = set()
    for feature in data["features"]:
        aid = feature.get("properties", {}).get("area_id")
        geom = feature.get("geometry") or {}
        if aid not in AREAS or aid in found or geom.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError("Invalid area identity or geometry type")
        found.add(aid)
        polys = [geom.get("coordinates")] if geom["type"] == "Polygon" else geom.get("coordinates")
        if not isinstance(polys, list) or not polys:
            raise ValueError("Empty polygon geometry")
        for poly in polys:
            if not isinstance(poly, list) or not poly:
                raise ValueError("Missing polygon rings")
            for ring in poly:
                if not isinstance(ring, list) or len(ring) < 4 or ring[0] != ring[-1]:
                    raise ValueError("Unclosed or malformed GeoJSON ring")
                for point in ring:
                    if not isinstance(point, list) or len(point) < 2:
                        raise ValueError("Invalid geographic coordinate")
                    lon, lat = point[:2]
                    if not all(isinstance(v, (int, float)) and abs(v) != float("inf") for v in (lon, lat)):
                        raise ValueError("Non-numeric coordinate")
                    if not (35.2 <= lon <= 35.75 and 31.6 <= lat <= 32.2):
                        raise ValueError("Geometry outside Jericho review envelope")
    if found != AREAS:
        raise ValueError("Study-area IDs missing")
    # GeoJSON follows WGS84 longitude,latitude order by specification.
    return data


def load_mission_data(data_dir: Path | str | None = None) -> MissionData:
    folder = Path(data_dir) if data_dir is not None else ROOT / "data"
    ndvi = _annual_csv(folder / "ndvi_annual.csv", "ndvi", "valid_observations")
    rain = _annual_csv(folder / "rainfall_annual.csv", "rainfall_mm", "valid_months")
    power = _power_csv(folder / "nasa_power_jericho_point_rainfall.csv")
    polygons = _geojson(folder / "study_areas.geojson")
    meta_path = folder / "metadata.json"
    if not meta_path.exists():
        meta_path = folder / "metadata_TEMPLATE.json"
    with meta_path.open(encoding="utf-8") as fh:
        metadata = json.load(fh)
    if not isinstance(metadata, dict):
        raise ValueError("Invalid dataset metadata")
    verification = metadata.get("verification_status", "pending")
    if verification not in {"verified", "pending"}:
        raise ValueError("Unknown provenance state")
    # A template is NEVER independent evidence of completed verification.
    if meta_path.name == "metadata_TEMPLATE.json":
        verification = "pending"
    return MissionData(ndvi, rain, power, polygons, metadata, verification)
