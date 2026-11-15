"""BLOOM main-site Explore integration for the verified-source CSV pilot.

Self-contained presentation layer. Original NASA CSVs, GeoJSON, scientific
modules, and strict data loader are untouched.
"""
from __future__ import annotations

import folium
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from modules.area_advisor import GOAL_LABELS, advise_area, advisor_report
from modules.investigation_case import (
    AREA_NAMES,
    CaseData,
    annual_series,
    area_at_point,
    case_report,
    investigate,
)
from modules.ui_components import page_header, section_title, stat_card, style_figure


def _chart(series, year: int, column: str, title: str, color: str) -> go.Figure:
    selected = series.loc[series["year"] == year, column].iloc[0]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series["year"], y=series[column], name=title,
        mode="lines+markers",
        line={"color": color, "width": 3},
        marker={"size": 6},
    ))
    fig.add_trace(go.Scatter(
        x=[year], y=[selected], name=f"Selected {year}",
        mode="markers",
        marker={"color": "#D99A56", "size": 12},
    ))
    style_figure(fig, title)
    fig.update_layout(height=300, margin=dict(l=14, r=15, t=30, b=20))
    return fig


def _map(data: CaseData, active: str, year: int, basemap: str):
    fmap = folium.Map(location=[31.85, 35.48], tiles=None, zoom_start=12, control_scale=True)
    folium.TileLayer("OpenStreetMap", name="Streets", show=basemap == "Streets").add_to(fmap)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri and imagery providers",
        name="Satellite", show=basemap == "Satellite",
    ).add_to(fmap)
    all_points = []
    for feature in data.geojson["features"]:
        area_id = feature["properties"]["area_id"]
        geom = feature["geometry"]
        polygons = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        for polygon in polygons:
            all_points.extend((point[1], point[0]) for point in polygon[0])
        readings = annual_series(data, area_id).set_index("year").loc[year]
        enriched = {
            **feature,
            "properties": {
                **feature["properties"],
                "name": AREA_NAMES[area_id],
                "year": str(year),
                "ndvi": f"{float(readings['ndvi']):.4f}",
                "rain": f"{float(readings['rainfall_mm']):.1f} mm",
            },
        }
        folium.GeoJson(
            enriched,
            name=AREA_NAMES[area_id],
            style_function=lambda _, selected=(area_id == active): {
                "color": "#163D2E" if selected else "#398562",
                "weight": 4 if selected else 2,
                "fillColor": "#D99A56" if selected else "#65AF81",
                "fillOpacity": .38 if selected else .22,
            },
            highlight_function=lambda _: {"weight": 5, "fillOpacity": .55},
            tooltip=folium.GeoJsonTooltip(
                fields=["name", "year", "ndvi", "rain"],
                aliases=["Area", "Year", "NDVI", "Rainfall"],
            ),
            popup=folium.GeoJsonPopup(
                fields=["name", "year", "ndvi", "rain"],
                aliases=["Area", "Year", "NDVI", "Rainfall"],
            ),
        ).add_to(fmap)
    if all_points:
        fmap.fit_bounds(
            [[min(p[0] for p in all_points), min(p[1] for p in all_points)],
             [max(p[0] for p in all_points), max(p[1] for p in all_points)]]
        )
    folium.LayerControl(collapsed=True).add_to(fmap)
    return fmap


def render(ctx, navigate) -> None:
    page_header(
        "01 / THE LANDSCAPE",
        "Explore. Investigate. Decide.",
        "Select a real study polygon in Jericho, inspect its annual observations "
        "and compare areas for a question you choose.",
    )

    if not ctx.ready:
        st.info("Study data are currently unavailable for this pilot; no observations are invented.")
        if ctx.error:
            with st.expander("Data loading information"):
                st.code(ctx.error)
        return

    data = CaseData(ctx.ndvi_df, ctx.rainfall_df, ctx.geojson, ctx.metadata)

    if not data.verified:
        with st.expander("📁 Uploaded study observations — source information", expanded=False):
            st.write(
                "Values are read from the uploaded NDVI and rainfall CSV files. "
                "The original Earth Engine export provenance remains pending independent review. "
                "This does not change or replace the recorded measurements."
            )

    year = st.slider(
        "📅 Inspection year", 2005, 2024,
        value=ctx.end_year, key="bloom_explore_year",
        help="The selected year controls the map, its values and year-specific recommendations.",
    )
    basemap = st.selectbox(
        "🗺️ Map background", ["Satellite", "Streets"], key="bloom_explore_basemap",
    )

    section_title(
        "01 / INTERACTIVE MAP",
        "Choose a study area",
        "Click either polygon directly, or use the Study Area selector in the sidebar.",
    )
    l, r = st.columns([1.65, 1], gap="large")
    with l:
        fmap = _map(data, ctx.area_id, year, basemap)
        state = st_folium(
            fmap,
            key=f"bloom_main_explore_{ctx.area_id}_{year}_{basemap}",
            height=440,
            use_container_width=True,
            returned_objects=[
                "last_clicked", "last_object_clicked", "last_object_clicked_count"
            ],
        )
        if isinstance(state, dict):
            event = state.get("last_object_clicked") or state.get("last_clicked")
            if isinstance(event, dict) and "lat" in event and "lng" in event:
                signature = (
                    round(float(event["lat"]), 7),
                    round(float(event["lng"]), 7),
                    state.get("last_object_clicked_count"),
                )
                if signature != st.session_state.get("bloom_main_map_click"):
                    st.session_state.bloom_main_map_click = signature
                    area = area_at_point(
                        data.geojson, float(event["lat"]), float(event["lng"])
                    )
                    if area and area != ctx.area_id:
                        # The main sidebar selectbox already exists on this run.
                        # Queue its new value for application BEFORE widget creation.
                        st.session_state.bloom_pending_area = area
                        st.rerun()

    series = annual_series(data, ctx.area_id)
    current = series.loc[series.year == year].iloc[0]
    with r:
        st.markdown("#### 02 / Current evidence")
        st.caption(f"{AREA_NAMES[ctx.area_id]} · {year}")
        n, rain = st.columns(2)
        with n:
            st.metric("NDVI", f"{float(current['ndvi']):.4f}")
        with rain:
            st.metric("Rainfall", f"{float(current['rainfall_mm']):.1f} mm")
        stat_card(
            "OBSERVATIONS",
            str(len(series)),
            "Annual observations per variable · 2005–2024",
            "leaf",
        )
        st.caption(
            "Polygon-mean annual values, not pixel-resolution vegetation or rainfall maps. "
            "MODIS NDVI is much finer resolution than GPM rainfall."
        )

    section_title(
        "02 / EVIDENCE",
        "The long view",
        "Use the graphs to explore changes over time; source values are unchanged.",
    )
    a, b = st.columns(2, gap="large")
    with a:
        st.plotly_chart(_chart(series, year, "ndvi", "NDVI", "#2E7254"), use_container_width=True)
    with b:
        st.plotly_chart(_chart(series, year, "rainfall_mm", "Annual rainfall (mm)", "#5083A7"), use_container_width=True)

    section_title(
        "03 / AREA ADVISOR",
        "Which area should you choose?",
        "There is no single 'best' area. Select your goal and BLOOM explains the comparison.",
    )
    goal = st.selectbox(
        "My investigation goal",
        list(GOAL_LABELS),
        format_func=GOAL_LABELS.get,
        key="bloom_advisor_goal",
    )
    recommendation = advise_area(data, goal, int(year))

    left, right = st.columns([1.2, 1], gap="large")
    with left:
        if recommendation.winner:
            st.markdown(f"#### Suggested: {AREA_NAMES[recommendation.winner]}")
        else:
            st.markdown("#### No clear recommendation")

        st.write(recommendation.explanation)
        st.caption(f"Comparison: {recommendation.metric} · {recommendation.period}")
        if recommendation.winner and st.button(
            "🧭 Show suggested area on map", key="bloom_advisor_focus", type="primary"
        ):
            st.session_state.bloom_pending_area = recommendation.winner
            st.rerun()
    with right:
        fig = go.Figure(go.Bar(
            x=[AREA_NAMES[area_id] for area_id in recommendation.values],
            y=list(recommendation.values.values()),
            marker_color=[
                "#4C8B63" if area_id == recommendation.winner else "#A9C7B4"
                for area_id in recommendation.values
            ],
            text=[
                f"{value:+.4f}" if goal == "long_term_greening" else f"{value:.4f}"
                for value in recommendation.values.values()
            ],
            textposition="outside",
        ))
        fig.update_layout(
            height=295,
            margin={"l": 10, "r": 12, "t": 25, "b": 15},
            yaxis_title=recommendation.metric,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("How was this suggestion calculated?"):
        st.markdown(
            "Recommendations compare only the **two existing study polygons**, "
            "using recorded NDVI. Rainfall is context, not a farming suitability score."
        )
        for note in recommendation.cautions:
            st.write("• " + note)

    section_title(
        "04 / ACTION BRIEF",
        "Carry the evidence forward",
        "Download a report explaining the selected area's observations and the advisor recommendation.",
    )
    findings = investigate(data, ctx.area_id)
    report = (
        case_report(data, ctx.area_id, findings)
        + "\n---\n\n"
        + advisor_report(data, recommendation)
    )
    st.download_button(
        "⬇️ Download investigation + recommendation (.md)",
        data=report.encode("utf-8"),
        file_name=f"BLOOM_{ctx.area_id}_{goal}_{year}.md",
        mime="text/markdown",
        key="bloom_explore_report_download",
        type="primary",
    )
    with st.expander("Preview the investigation brief"):
        st.code(report, language="markdown")

    a, b = st.columns(2, gap="medium")
    with a:
        if st.button("View detailed analytics ↗", use_container_width=True, key="bloom_explore_to_analytics"):
            navigate("Analytics")
    with b:
        if st.button("Open Reports ↗", use_container_width=True, key="bloom_explore_to_reports"):
            navigate("Reports")
