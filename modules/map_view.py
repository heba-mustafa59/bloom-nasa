
"""BLOOM interactive study-area map."""

from __future__ import annotations

from math import isfinite

import folium
import streamlit as st
from streamlit_folium import st_folium


AREA_NAMES = {
    "area_a": "Area A",
    "area_b": "Area B",
}

# Approximate Jericho map center, not a study polygon.
JERICHO_CENTER = [31.86, 35.45]


def _coordinates(value):
    """Extract valid latitude/longitude pairs from GeoJSON."""
    if not isinstance(value, (list, tuple)):
        return

    if (
        len(value) >= 2
        and all(
            isinstance(v, (int, float)) and not isinstance(v, bool)
            for v in value[:2]
        )
    ):
        lon, lat = value[:2]
        if (
            isfinite(lon)
            and isfinite(lat)
            and -180 <= lon <= 180
            and -90 <= lat <= 90
        ):
            yield (lat, lon)
    else:
        for item in value:
            yield from _coordinates(item)


def _valid_features(geojson):
    """Return supported study-area features."""
    if not isinstance(geojson, dict):
        return []

    if geojson.get("type") != "FeatureCollection":
        return []

    features = geojson.get("features", [])
    if not isinstance(features, list):
        return []

    valid = []

    for feature in features:
        if not isinstance(feature, dict):
            continue

        if feature.get("type") != "Feature":
            continue

        props = feature.get("properties")
        geometry = feature.get("geometry")

        if not isinstance(props, dict):
            continue

        if not isinstance(geometry, dict):
            continue

        if props.get("area_id") not in AREA_NAMES:
            continue

        if geometry.get("type") not in ("Polygon", "MultiPolygon"):
            continue

        if list(_coordinates(geometry.get("coordinates"))):
            valid.append(feature)

    return valid


def render_map(study_areas: dict, selected_area_id: str) -> None:
    """Render the Jericho map and verified study polygons."""

    st.markdown("### 01 / Choose Your Case")
    st.caption(
        "Explore vegetation study areas in Jericho, Palestine."
    )

    # Always show the basemap, even without GeoJSON.
    fmap = folium.Map(
        location=JERICHO_CENTER,
        zoom_start=12,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    # Satellite imagery basemap.
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/"
            "services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Tiles © Esri and its imagery providers",
        name="Satellite",
        overlay=False,
        control=True,
    ).add_to(fmap)

    features = _valid_features(study_areas)

    if not features:
        st.info(
            "Verified study-area boundaries are not available yet. "
            "Showing the Jericho base map."
        )
    else:
        all_points = []

        for feature in features:
            props = feature["properties"]
            area_id = props["area_id"]

            selected = area_id == selected_area_id

            all_points.extend(
                _coordinates(feature["geometry"]["coordinates"])
            )

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
                highlight_function=lambda _: {
                    "weight": 5,
                    "fillOpacity": 0.5,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["area_id"],
                    aliases=["Study area:"],
                ),
            ).add_to(fmap)

        if all_points:
            south = min(p[0] for p in all_points)
            north = max(p[0] for p in all_points)
            west = min(p[1] for p in all_points)
            east = max(p[1] for p in all_points)

            fmap.fit_bounds([
                [south, west],
                [north, east],
            ])

        if selected_area_id not in AREA_NAMES:
            st.warning("Please select Area A or Area B.")

    folium.LayerControl(
        collapsed=False
    ).add_to(fmap)

    st_folium(
        fmap,
        height=500,
        use_container_width=True,
        returned_objects=[],
        key="bloom_study_map",
    )

    if features and selected_area_id in AREA_NAMES:
        st.caption(
            f"Selected study area: {AREA_NAMES[selected_area_id]}"
        )
