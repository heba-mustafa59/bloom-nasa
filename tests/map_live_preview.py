"""Preview actual local NASA files only: python -m streamlit run tests/map_live_preview.py"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from modules.map_view import AREA_NAMES, render_map  # noqa: E402

st.set_page_config(page_title="BLOOM | Jericho Map", page_icon="🌱", layout="wide")
st.title("BLOOM — Jericho Explorer")
st.caption("Direct view of the data/ directory. Missing measurements are NEVER simulated.")
folder = ROOT / "data"


def read_json(name, fallback):
    try:
        return json.loads((folder / name).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return fallback


def read_csv(name):
    try:
        return pd.read_csv(folder / name)
    except (FileNotFoundError, pd.errors.EmptyDataError, OSError):
        return pd.DataFrame()


region = st.radio("Study polygon (not automatically a named locality)", list(AREA_NAMES),
                  format_func=lambda name: AREA_NAMES[name], horizontal=True)
areas = read_json("study_areas.geojson", {"type": "FeatureCollection", "features": []})
metadata = read_json("metadata.json", {})
ndvi = read_csv("ndvi_annual.csv")
rain = read_csv("rainfall_annual.csv")
st.caption(f"GeoJSON features: {len(areas.get('features', [])) if isinstance(areas, dict) else 0}; "
           f"NDVI rows: {len(ndvi)}; rainfall rows: {len(rain)}; "
           f"metadata verification: {metadata.get('verification_status', 'pending') if isinstance(metadata, dict) else 'pending'}")
render_map(areas, region, ndvi_df=ndvi, rainfall_df=rain, metadata=metadata)
