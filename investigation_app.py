"""BLOOM Investigation Pilot — isolated Streamlit preview.

Launch: python -m streamlit run investigation_app.py --server.address 0.0.0.0
This file does not alter app.py or ui_app.py.
"""
from __future__ import annotations

import folium
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from modules.investigation_case import (
    AREA_NAMES,
    annual_series,
    area_at_point,
    case_report,
    investigate,
    load_case_data,
)


st.set_page_config(
    page_title="BLOOM | Earth Investigation Pilot",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """<style>
    .block-container {max-width: 1380px; padding-top: 1.5rem}
    h1,h2,h3 {color: #163d2e}
    div[data-testid="stMetric"] {
      background:#f5f8f3; border:1px solid #e0eadd;
      padding:12px 16px; border-radius:12px
    }
    .hero {background:linear-gradient(110deg,#173e30,#346b49);
      color:white; padding:23px 30px; border-radius:18px; margin-bottom:18px}
    .hero h1 {color:white; margin:0; font-size:2.3rem}
    .hero p {color:#e2f0e3; margin:8px 0 0}
    /* Prevent Arabic/RTL browser settings from reversing the year timeline. */
    div[data-testid="stSlider"], div[data-testid="stSlider"] * {
      direction:ltr !important; text-align:left;
    }
    </style>""",
    unsafe_allow_html=True,
)

st.markdown(
    """<div class="hero"><div style="letter-spacing:.18em;font-size:12px">
    BLOOM / EARTH INVESTIGATION</div>
    <h1>What is changing in Jericho?</h1>
    <p>Explore two study polygons, inspect NASA-derived annual observations,
    and ask whether the evidence supports a trend.</p></div>""",
    unsafe_allow_html=True,
)

try:
    data = load_case_data()
except (FileNotFoundError, ValueError, OSError, KeyError, TypeError) as exc:
    st.error("Cannot load the existing study files. No data were invented.")
    st.code(str(exc))
    st.stop()

st.caption(
    "📁 Data source: the uploaded `data/ndvi_annual.csv`, "
    "`data/rainfall_annual.csv`, and `data/study_areas.geojson`. "
    "The displayed numbers are read directly from these files, without synthetic replacements."
)
if not data.verified:
    with st.expander("Data provenance note", expanded=False):
        st.write(
            "We use the uploaded study data as requested. "
            "The project metadata still marks independent verification of the original "
            "Earth Engine export and polygon provenance as pending. "
            "This does not change the values in your CSV files."
        )

if "pilot_area" not in st.session_state or st.session_state.pilot_area not in AREA_NAMES:
    st.session_state.pilot_area = "area_a"

top_a, top_b, top_c = st.columns([2, 1, 1])
with top_a:
    area = st.selectbox(
        "Study area",
        options=list(AREA_NAMES),
        format_func=AREA_NAMES.get,
        key="pilot_area",
        help="Pick an existing polygon, or click inside it on the map.",
    )
with top_b:
    year = st.slider(
        "Inspection year", min_value=2005, max_value=2024,
        value=2024, step=1, key="pilot_year",
    )
    st.markdown(
        '<div dir="ltr" style="display:flex;justify-content:space-between;'
        'font-size:12px;color:#526458;margin-top:-9px">'
        '<span>2005</span><span>2024</span></div>',
        unsafe_allow_html=True,
    )
with top_c:
    basemap = st.selectbox("Map view", ["Satellite", "Streets"], key="pilot_basemap")

series = annual_series(data, area)
row = series.loc[series.year == year].iloc[0]
findings = investigate(data, area)

map_col, details_col = st.columns([1.65, 1], gap="large")

with map_col:
    st.subheader("01 / Select the landscape")
    st.caption("Click inside a highlighted polygon to switch the case. These boundaries come from data/study_areas.geojson.")
    fmap = folium.Map(
        location=[31.85, 35.48], tiles=None, zoom_start=12, control_scale=True
    )
    folium.TileLayer("OpenStreetMap", name="Streets", show=basemap == "Streets").add_to(fmap)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri and imagery providers",
        name="Satellite",
        show=basemap == "Satellite",
    ).add_to(fmap)
    all_points = []
    for feature in data.geojson["features"]:
        area_id = feature["properties"]["area_id"]
        active = area_id == area
        geometry = feature["geometry"]
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        for polygon in polygons:
            all_points += [(p[1], p[0]) for p in polygon[0]]
        # Attach values to the actual GeoJSON feature so polygon clicks show
        # measurements immediately inside the map, independent of the top menu.
        polygon_row = annual_series(data, area_id).set_index("year").loc[year]
        display_feature = {
            **feature,
            "properties": {
                **feature["properties"],
                "display_name": AREA_NAMES[area_id],
                "inspection_year": str(year),
                "ndvi_display": f"{float(polygon_row['ndvi']):.4f}",
                "rain_display": f"{float(polygon_row['rainfall_mm']):.1f} mm",
            },
        }
        folium.GeoJson(
            display_feature,
            name=AREA_NAMES[area_id],
            style_function=lambda _, selected=active: {
                "color": "#163d2e" if selected else "#56a36e",
                "weight": 4 if selected else 2,
                "fillColor": "#eca86b" if selected else "#68b37a",
                "fillOpacity": 0.4 if selected else 0.22,
            },
            highlight_function=lambda _: {"weight": 5, "fillOpacity": 0.56},
            tooltip=folium.GeoJsonTooltip(
                fields=["display_name", "inspection_year", "ndvi_display", "rain_display"],
                aliases=["Area:", "Year:", "NDVI:", "Rainfall:"],
                sticky=True,
            ),
            popup=folium.GeoJsonPopup(
                fields=["display_name", "inspection_year", "ndvi_display", "rain_display"],
                aliases=["Area:", "Year:", "NDVI:", "Rainfall:"],
            ),
        ).add_to(fmap)
    if all_points:
        fmap.fit_bounds(
            [[min(x[0] for x in all_points), min(x[1] for x in all_points)],
             [max(x[0] for x in all_points), max(x[1] for x in all_points)]]
        )
    folium.LayerControl(collapsed=True).add_to(fmap)
    map_state = st_folium(
        fmap, key=f"pilot_map_v2_{area}_{year}_{basemap}", height=430,
        use_container_width=True,
        returned_objects=[
            "last_clicked", "last_object_clicked",
            "last_object_clicked_count",
        ],
    )
    # Clicking a GeoJSON feature is a layer event (last_object_clicked),
    # not necessarily a map-background event (last_clicked).
    # Both are supported, and duplicate widget reruns are ignored.
    if isinstance(map_state, dict):
        event = map_state.get("last_object_clicked") or map_state.get("last_clicked")
        if isinstance(event, dict) and "lat" in event and "lng" in event:
            signature = (
                round(float(event["lat"]), 7),
                round(float(event["lng"]), 7),
                map_state.get("last_object_clicked_count"),
            )
            if signature != st.session_state.get("pilot_processed_click"):
                st.session_state.pilot_processed_click = signature
                chosen = area_at_point(
                    data.geojson, float(event["lat"]), float(event["lng"])
                )
                if chosen and chosen != area:
                    st.session_state.pilot_area = chosen
                    st.rerun()

with details_col:
    st.subheader("02 / Inspect the evidence")
    st.caption(f"{AREA_NAMES[area]} · {year} · annual polygon averages")
    a, b = st.columns(2)
    with a:
        st.metric("NDVI", f"{row['ndvi']:.4f}")
    with b:
        st.metric("Rainfall", f"{row['rainfall_mm']:.1f} mm")
    st.caption(
        "NDVI: NASA MODIS MOD13Q1 (approx. 250 m). Rainfall: "
        "GPM IMERG V07 (approx. 11 km). Annual summaries, not pixel maps."
    )
    nd_trend = findings["ndvi_trend"]
    rain_trend = findings["rainfall_trend"]
    x, y = st.columns(2)
    with x:
        st.metric(
            "NDVI slope / decade",
            f"{nd_trend['slope_per_decade']:+.4f}" if nd_trend["slope_per_decade"] is not None else "N/A",
        )
    with y:
        st.metric(
            "Rain slope / decade",
            f"{rain_trend['slope_per_decade']:+.1f} mm" if rain_trend["slope_per_decade"] is not None else "N/A",
        )
    def label_trend(r: dict) -> str:
        if r["status"] != "success":
            return "Insufficient observations"
        if r["significant"]:
            return "Statistically supported " + r["direction"]
        return "Not statistically significant"
    st.write(f"**NDVI:** {label_trend(nd_trend)}")
    st.write(f"**Rainfall:** {label_trend(rain_trend)}")
    st.caption(
        "Significance uses a prototype Mann–Kendall test (α = 0.05). "
        "Its assumptions and limitations matter; significance does not prove a cause."
    )

st.divider()
st.subheader("03 / Travel through time")
st.caption("Time series are built from uploaded CSVs. A highlighted point marks the inspection year.")
plots = st.columns(2, gap="large")
for target, field, label, color in [
    (plots[0], "ndvi", "NDVI (unitless)", "#2b7954"),
    (plots[1], "rainfall_mm", "Annual rainfall (mm)", "#5083a7"),
]:
    with target:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=series["year"], y=series[field], mode="lines+markers",
            line=dict(color=color, width=3), marker=dict(size=6),
            name=label,
        ))
        fig.add_trace(go.Scatter(
            x=[year], y=[float(row[field])], mode="markers",
            marker=dict(color="#d78d4b", size=14, line=dict(color="white", width=2)),
            name=f"Selected {year}",
        ))
        fig.update_layout(
            title=label, height=320, margin=dict(l=10, r=10, t=45, b=10),
            xaxis_title="Year", yaxis_title=label,
            legend=dict(orientation="h", y=-0.22),
        )
        st.plotly_chart(fig, use_container_width=True)

st.subheader("04 / The environmental mystery")
mystery = findings["mystery"]
status = mystery.get("model_status", "insufficient_evidence")
if status == "validated":
    st.info(
        "The rainfall-only model passed its holdout validation gate. "
        "Any flagged years are exploratory leads, not proof of irrigation."
    )
else:
    st.warning(
        "The rainfall-only model did not provide sufficient validated evidence "
        "to flag anomalies. This is a useful scientific result, not an application error."
    )
c1, c2 = st.columns(2)
with c1:
    st.write(f"**Model status:** {status.replace('_',' ').title()}")
    st.write(f"**Validation R²:** {mystery['validation_r2']:.3f}" if mystery["validation_r2"] is not None else "**Validation R²:** N/A")
with c2:
    st.write(f"**Validation MAE:** {mystery['validation_mae']:.4f}" if mystery["validation_mae"] is not None else "**Validation MAE:** N/A")
    st.write(f"**Flagged years:** {len(mystery.get('anomalies') or [])}")
with st.expander("Scientific limitations and validation"):
    for item in mystery.get("limitations") or []:
        st.write("• " + str(item))
    st.write("The original study-area boundaries and NASA export history must be confirmed before asserting source provenance.")

st.subheader("05 / Generate an investigation brief")
report = case_report(data, area, findings)
st.download_button(
    "Download case brief (.md)",
    data=report.encode("utf-8"),
    file_name=f"BLOOM_case_{area}_2005_2024.md",
    mime="text/markdown",
    type="primary",
)
with st.expander("Preview case brief"):
    st.code(report, language="markdown")
st.caption(
    "Pilot only · reads existing study polygons and annual observations · "
    "no AI causal claims · no changes to the main BLOOM application."
)
