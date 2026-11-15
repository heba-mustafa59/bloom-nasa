"""BLOOM map UI: renders supplied GeoJSON polygons; provenance is tracked separately."""
from __future__ import annotations

from math import isfinite

import folium
import streamlit as st
from streamlit_folium import st_folium

AREA_NAMES = {"area_a": "Area A", "area_b": "Area B"}


def _coordinates(value):
    """Walk nested GeoJSON coordinates; return (latitude, longitude) pairs."""
    if not isinstance(value, (list, tuple)):
        return
    if len(value) >= 2 and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) for v in value[:2]
    ):
        lon, lat = value[:2]
        if isfinite(lon) and isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90:
            yield (lat, lon)
    else:
        for item in value:
            yield from _coordinates(item)


def _valid_features(geojson):
    if not isinstance(geojson, dict) or geojson.get("type") != "FeatureCollection":
        return []
    features = geojson.get("features")
    if not isinstance(features, list):
        return []
    valid = []
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            continue
        props, geometry = feature.get("properties"), feature.get("geometry")
        if not isinstance(props, dict) or not isinstance(geometry, dict):
            continue
        if props.get("area_id") not in AREA_NAMES:
            continue
        if geometry.get("type") not in ("Polygon", "MultiPolygon"):
            continue
        if list(_coordinates(geometry.get("coordinates"))):
            valid.append(feature)
    return valid


def render_map(study_areas: dict, selected_area_id: str) -> None:
    """Display the exact GeoJSON study polygons and highlight the selected one.

    This function intentionally does NOT modify area selection or return a value.
    The integration developer controls selected_area_id inside app.py.
    """
    st.markdown("### 01 / Choose Your Case")
    st.caption("Explore supplied study-area boundaries near Jericho, Palestine. Source verification is tracked separately.")

    if selected_area_id not in AREA_NAMES:
        st.warning("Please select Area A or Area B.")
        return

    features = _valid_features(study_areas)
    if not features:
        st.info("Study-area boundaries are unavailable for this data source.")
        return

    points = [point for f in features for point in _coordinates(f["geometry"]["coordinates"])]
    south, north = min(p[0] for p in points), max(p[0] for p in points)
    west, east = min(p[1] for p in points), max(p[1] for p in points)

    try:
        fmap = folium.Map(
            location=[(south + north) / 2, (west + east) / 2],
            tiles="CartoDB positron", zoom_start=12, control_scale=True,
        )
        for feature in features:
            area_id = feature["properties"]["area_id"]
            selected = area_id == selected_area_id

            def style_fn(_feature, active=selected):
                return {
                    "color": "#163D2E" if active else "#4C8B63",
                    "weight": 4 if active else 2,
                    "fillColor": "#D99A56" if active else "#4C8B63",
                    "fillOpacity": 0.38 if active else 0.12,
                }

            folium.GeoJson(
                feature,
                name=AREA_NAMES[area_id],
                style_function=style_fn,
                highlight_function=lambda _: {"weight": 5, "fillOpacity": 0.5},
                tooltip=folium.GeoJsonTooltip(fields=["area_id"], aliases=["Study area:"]),
            ).add_to(fmap)

        fmap.fit_bounds([[south, west], [north, east]])
        folium.LayerControl(collapsed=True).add_to(fmap)
        st_folium(
            fmap, height=430, use_container_width=True,
            returned_objects=[], key="bloom_study_map",
        )
        st.caption(
            f"Selected: {AREA_NAMES[selected_area_id]}. "
            "Polygon source and verification status are documented separately."
        )
    except (ValueError, TypeError, KeyError, AttributeError):
        st.error("Unable to render the study-area map. Please check the GeoJSON file.")