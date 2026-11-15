"""Explore research geography without inventing study polygons."""

import pandas as pd
import streamlit as st

from modules.map_view import render_map
from modules.ui_components import (
    page_header,
    section_title,
    stat_card,
)
from modules.ui_data import AREA_LABELS


def render(ctx, navigate):
    page_header(
        "01 / THE LANDSCAPE",
        "See the terrain. Understand the context.",
        "A grounded view of the study geography, "
        "before we interpret its signals.",
    )

    left, mid, right = st.columns(3, gap="medium")

    with left:
        stat_card(
            "FOCUS AREA",
            AREA_LABELS[ctx.area_id],
            "Select a region in Research controls",
        )

    with mid:
        stat_card(
            "YEAR WINDOW",
            f"{ctx.start_year}–{ctx.end_year}",
            "Annual observations",
            "amber",
        )

    with right:
        stat_card(
            "STUDY BOUNDARIES",
            (
                "Available"
                if ctx.geojson.get("features")
                else "Pending"
            ),
            "Verified GeoJSON polygons only",
            "sky",
        )

    section_title(
        "THE MAP",
        "Geography comes first",
        "The map does not imply exact boundaries until "
        "the verified polygons are supplied.",
    )

    # Draw-enabled map remains available even when NASA data is missing.
    # Never pass synthetic demonstration values as NASA observations.
    render_map(
        ctx.geojson,
        ctx.area_id,
        ndvi_df=ctx.ndvi_df if not ctx.is_demo else None,
        rainfall_df=ctx.rainfall_df if not ctx.is_demo else None,
        metadata=ctx.metadata if not ctx.is_demo else {},
    )

    section_title(
        "THE PROFILE",
        "Evidence, not assumptions",
        "What is actually documented for the "
        "selected study area?",
    )

    col_a, col_b = st.columns([1.3, 1], gap="large")

    with col_a:
        st.markdown("#### Selected area")
        st.markdown(f"**{AREA_LABELS[ctx.area_id]}**")

        description = (
            ctx.metadata.get("study_areas") or {}
        ).get(ctx.area_id)

        if ctx.is_demo or not description:
            st.caption(
                "Exact polygon extent, land use, "
                "location, and surface area are pending "
                "verified metadata."
            )
        else:
            st.write(str(description))

    with col_b:
        st.markdown("#### Satellite layers")

        st.markdown(
            "**MODIS MOD13Q1 v6.1**  \n"
            "Vegetation NDVI · 250 m approximate "
            "native resolution"
        )

        st.markdown(
            "**GPM IMERG Monthly V07**  \n"
            "Rainfall · ~11 km approximate "
            "native resolution"
        )

        st.caption(
            "Rainfall estimates are spatially "
            "coarser than vegetation pixels."
        )

    if ctx.ready:
        with st.expander("Inspect observations for this area"):
            if ctx.is_demo:
                st.info("Demo data only — synthetic values, not NASA observations.")

            nd = ctx.area_data("ndvi")[["year", "ndvi"]]
            ra = ctx.area_data("rainfall_mm")[["year", "rainfall_mm"]]

            combined = pd.merge(
                nd,
                ra,
                on="year",
                how="outer",
            ).sort_values("year")

            st.dataframe(
                combined,
                hide_index=True,
                use_container_width=True,
            )

    if st.button(
        "Continue to analytics ↗",
        type="primary",
        key="explore_next",
    ):
        navigate("Analytics")
