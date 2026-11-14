"""BLOOM foundation app: intentionally reports unavailable data rather than fake results."""
import streamlit as st
from modules.data_loader import load_datasets

import pandas as pd
from modules.map_view import render_map

st.set_page_config(page_title="BLOOM — Beyond the Green", page_icon="🌱", layout="wide")
st.title("🌱 BLOOM")
st.caption("Beyond the Green · Jericho, Palestine · NASA Space Apps 2026")
st.markdown("### Can we explain what is changing in Jericho's vegetation?")
st.write("Investigate satellite-measured vegetation, long-term trends, and rainfall-related mysteries. The scientific modules are being built by our team.")

if "started" not in st.session_state:
    st.session_state.started = False
if st.button("Start Investigation", type="primary"):
    st.session_state.started = True

if st.session_state.started:
    ndvi_df, rainfall_df, areas, metadata = load_datasets()
    st.subheader("Case 001 — Jericho")
        selected_area_id = st.radio(
        "Choose study area",
        ["area_a", "area_b"],
        format_func=lambda x: "Area A" if x == "area_a" else "Area B",
        horizontal=True,
    )

    render_map(
        areas,
        selected_area_id,
        ndvi_df=ndvi_df,
        rainfall_df=rain_df,
        metadata=metadata,
    )
    ready = not ndvi_df.empty and not rain_df.empty and bool(areas.get("features"))
    if not ready:
        st.warning("Project setup is ready; verified NASA datasets and study polygons have not yet been imported. No scientific results are available.")
        st.markdown("**Next:** Data team exports NDVI, rainfall and two study-area polygons into `data/`.")
    else:
        st.success("Data files found. The analysis and map modules can now be integrated.")
        st.write(f"NDVI observations: {len(ndvi_df)} · Rainfall observations: {len(rain_df)} · Study areas: {len(areas['features'])}")
else:
    st.info("Select **Start Investigation** to open the case workspace.")

st.divider()
st.caption("Data planned: NASA MODIS NDVI and GPM IMERG. No observations or conclusions are fabricated.")
