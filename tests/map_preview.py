import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.map_view import render_map

st.set_page_config(
    page_title="BLOOM Map Preview",
    layout="wide"
)

st.title("🌸 BLOOM")
st.subheader("Jericho Interactive Map")

selected = st.selectbox(
    "Choose study area",
    ["area_a", "area_b"]
)

geojson_path = ROOT / "data" / "study_areas.geojson"

if geojson_path.exists():
    with open(geojson_path, encoding="utf-8") as f:
        study_areas = json.load(f)
else:
    study_areas = {
        "type": "FeatureCollection",
        "features": []
    }

render_map(study_areas, selected)