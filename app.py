"""BLOOM — Jericho investigation: show verified observations only."""

import pandas as pd
import streamlit as st

from modules.data_loader import load_datasets
from modules.map_view import render_map

st.set_page_config(
    page_title="BLOOM — Beyond the Green",
    page_icon="🌱",
    layout="wide",
)

st.title("🌱 BLOOM")
st.caption("Beyond the Green · Jericho, Palestine · NASA Space Apps 2026")
st.markdown("### Can we explain what is changing in Jericho's vegetation?")
st.write(
    "Investigate satellite-measured vegetation, long-term trends, "
    "and rainfall-related mysteries."
)

if "started" not in st.session_state:
    st.session_state.started = False

if st.button("Start Investigation", type="primary"):
    st.session_state.started = True

if st.session_state.started:
    st.subheader("Case 001 — Jericho")
    selected_area_id = st.radio(
        "Choose study area",
        ["area_a", "area_b"],
        format_func=lambda area: "Area A" if area == "area_a" else "Area B",
        horizontal=True,
    )

    try:
        ndvi_df, rainfall_df, areas, metadata = load_datasets()
    except (FileNotFoundError, ValueError, OSError, pd.errors.ParserError) as exc:
        st.warning("NASA data unavailable or invalid. Showing reference locations only.")
        st.caption(f"Data load issue: {exc}")
        ndvi_df = pd.DataFrame()
        rainfall_df = pd.DataFrame()
        areas = {"type": "FeatureCollection", "features": []}
        metadata = {"verification_status": "pending"}

    render_map(
        areas,
        selected_area_id,
        ndvi_df=ndvi_df,
        rainfall_df=rainfall_df,
        metadata=metadata,
    )

    data_ready = (
        not ndvi_df.empty
        and not rainfall_df.empty
        and isinstance(areas, dict)
        and bool(areas.get("features"))
        and isinstance(metadata, dict)
        and metadata.get("verification_status") == "verified"
    )
    if data_ready:
        st.success("Verified NASA files loaded. Analysis modules can now be integrated.")
        st.write(
            f"NDVI records: {len(ndvi_df)} · "
            f"Rainfall records: {len(rainfall_df)} · "
            f"Study areas: {len(areas['features'])}"
        )
    else:
        st.info(
            "Verified NASA measurements are not available yet. "
            "The map shows reference locations and any available study geometry."
        )
else:
    st.info("Select **Start Investigation** to open the case workspace.")

st.divider()
st.caption(
    "Data sources planned: NASA MODIS NDVI and GPM IMERG. "
    "No observations or scientific conclusions are fabricated."
)
