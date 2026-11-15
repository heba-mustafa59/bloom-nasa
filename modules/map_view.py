"""BLOOM Jericho Map — interactive visualization of real study polygons.

Stable integration contract:
    render_map(study_areas: dict, selected_area_id: str) -> None

Extra optional keyword parameters support verified NASA annual observations.
Reference place markers are NOT area boundaries and do NOT assign area IDs.
"""
from __future__ import annotations

from html import escape
from math import isfinite
from typing import Any

import folium
from folium.plugins import Draw, Fullscreen, MeasureControl, MiniMap, MousePosition, Search

AREA_NAMES = {"area_a": "Area A — Study polygon", "area_b": "Area B — Study polygon"}
# Independent reference sites. Never equate these to area_a/area_b without verified geometry.
REFERENCE_SITES = {
    "tell_sultan": {
        "name": "Tell es-Sultan | تل السلطان", "lat": 31.8713056, "lon": 35.4440556,
        "source": "UNESCO World Heritage Centre", "url": "https://whc.unesco.org/en/list/1687",
    },
    "al_auja": {
        "name": "Al-Auja | العوجا", "lat": 31.95069, "lon": 35.46756,
        "source": "GeoNames", "url": "https://www.geonames.org/285112/al-awja.html",
    },
}
COLORS = {"forest": "#163D2E", "leaf": "#4C8B63", "amber": "#D99A56"}
BASEMAPS = ("Streets", "Satellite")
MODES = ("Boundaries", "Annual NDVI")


def _coord(value: Any) -> tuple[float, float] | None:
    """Convert one [longitude, latitude] coordinate into (latitude, longitude)."""
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        return None
    lon, lat = value[:2]
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in (lon, lat)):
        return None
    if not all(map(isfinite, (lon, lat))) or not (-180 <= lon <= 180 and -90 <= lat <= 90):
        return None
    return (float(lat), float(lon))


def _polygon_points(geometry: Any) -> list[tuple[float, float]] | None:
    """Check coordinate structure. This is NOT a provenance/topology certification."""
    if not isinstance(geometry, dict):
        return None
    kind, coords = geometry.get("type"), geometry.get("coordinates")
    if kind == "Polygon":
        polygons = [coords]
    elif kind == "MultiPolygon":
        polygons = coords
    else:
        return None
    if not isinstance(polygons, list) or not polygons:
        return None
    result = []
    for polygon in polygons:
        if not isinstance(polygon, list) or not polygon:
            return None
        for ring in polygon:
            if not isinstance(ring, list) or len(ring) < 4:
                return None
            converted = [_coord(p) for p in ring]
            if any(p is None for p in converted):
                return None
            if converted[0] != converted[-1] or len(set(converted[:-1])) < 3:
                return None
            # Review envelope around Jericho; catches accidental far-away polygons.
            if any(not (31.6 <= lat <= 32.2 and 35.2 <= lon <= 35.75)
                   for lat, lon in converted):
                return None
            result.extend(converted)
    return result


def _valid_features(geojson: Any) -> list[dict]:
    if not isinstance(geojson, dict) or geojson.get("type") != "FeatureCollection":
        return []
    features = geojson.get("features")
    if not isinstance(features, list):
        return []
    result, seen = [], set()
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            continue
        props = feature.get("properties")
        if not isinstance(props, dict):
            continue
        area_id = props.get("area_id")
        geom = feature.get("geometry")
        if area_id not in AREA_NAMES or area_id in seen or _polygon_points(geom) is None:
            continue
        seen.add(area_id)
        # Use exact NASA-exported geometries; only add presentation properties.
        result.append({"type": "Feature", "geometry": geom, "properties": {
            "area_id": area_id,
            "display_name": AREA_NAMES[area_id],
        }})
    return result


def _reading(df: Any, area_id: str, year: int | None, field: str) -> float | None:
    """One finite, non-duplicated NASA measurement; otherwise none."""
    if year is None or df is None:
        return None
    try:
        import pandas as pd
        if not {"year", "area_id", field}.issubset(df.columns):
            return None
        years = pd.to_numeric(df["year"], errors="coerce")
        rows = df.loc[(df["area_id"] == area_id) & (years == year)]
        if len(rows) != 1:
            return None
        row = rows.iloc[0]
        number = float(row[field])
        if not isfinite(number):
            return None
        if field == "ndvi":
            if not -1 <= number <= 1:
                return None
            if "valid_observations" in rows.columns:
                count = float(row["valid_observations"])
                if not isfinite(count) or not (0 < count <= 24 and count.is_integer()):
                    return None
        elif field == "rainfall_mm":
            if number < 0:
                return None
            # Full year means all 12 monthly composites were present.
            if "valid_months" in rows.columns:
                count = float(row["valid_months"])
                if not isfinite(count) or count != 12:
                    return None
        return number
    except (AttributeError, KeyError, ValueError, TypeError, OverflowError):
        return None


def _ndvi_color(value: float | None) -> str:
    if value is None:
        return "#87919A"
    if value < 0:
        return "#B9745B"
    if value < 0.2:
        return "#D99A56"
    if value < 0.4:
        return "#BDD36E"
    if value < 0.6:
        return "#4C8B63"
    return "#163D2E"


def build_map(
    study_areas: dict | None,
    selected_area_id: str = "area_a",
    *, ndvi_df: Any = None, rainfall_df: Any = None,
    metadata: dict | None = None, selected_year: int | None = None,
    focus: str = "overview", basemap: str = "Streets",
    mode: str = "Boundaries", show_reference_points: bool = True,
    show_boundaries: bool = True, show_mini_map: bool = False,
    candidate_features: list[dict] | None = None, enable_drawing: bool = False,
) -> folium.Map:
    """Build Folium map; no synthetic observations or artificial study polygons."""
    if selected_area_id not in AREA_NAMES:
        raise ValueError("Invalid area ID")
    if basemap not in BASEMAPS or mode not in MODES:
        raise ValueError("Invalid basemap or data overlay")
    if focus not in {"overview", "selected", "tell_sultan", "al_auja"}:
        raise ValueError("Invalid focus")
    if selected_year is not None and (type(selected_year) is not int or not 2005 <= selected_year <= 2024):
        raise ValueError("Year must be 2005–2024")

    verified = isinstance(metadata, dict) and metadata.get("verification_status") == "verified"
    features = _valid_features(study_areas)
    locations = list(REFERENCE_SITES.values())
    center = [sum(p["lat"] for p in locations) / len(locations),
              sum(p["lon"] for p in locations) / len(locations)]
    fmap = folium.Map(location=center, tiles=None, zoom_start=12, control_scale=True,
                      zoom_control=True, scrollWheelZoom=True, min_zoom=7, max_zoom=19)

    folium.TileLayer("OpenStreetMap", name="Streets", show=basemap == "Streets").add_to(fmap)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri and contributors", name="Satellite", show=basemap == "Satellite"
    ).add_to(fmap)

    pins = folium.FeatureGroup(name="Reference places (NOT polygon boundaries)", show=show_reference_points)
    for place in locations:
        popup = (f"<b>{escape(place['name'])}</b><br>Reference location only; "
                 "NOT a NASA extraction polygon.<br>"
                 f"<a target='_blank' rel='noopener noreferrer' "
                 f"href='{escape(place['url'], quote=True)}'>"
                 f"Source: {escape(place['source'])}</a>")
        folium.Marker(
            [place["lat"], place["lon"]], tooltip=place["name"],
            popup=folium.Popup(popup, max_width=300),
            icon=folium.Icon(color="orange", icon="info-sign")
        ).add_to(pins)
    pins.add_to(fmap)

    enhanced = []
    for feat in features:
        item = dict(feat)
        props = dict(feat["properties"])
        area_id = props["area_id"]
        ndvi = _reading(ndvi_df, area_id, selected_year, "ndvi") if verified else None
        rain = _reading(rainfall_df, area_id, selected_year, "rainfall_mm") if verified else None
        props.update({
            "ndvi_value": ndvi,
            "ndvi_label": f"{ndvi:.4f}" if ndvi is not None else "Unavailable / unverified",
            "rainfall_label": f"{rain:.1f} mm" if rain is not None else "Unavailable / unverified",
            "year_label": str(selected_year) if selected_year else "No year selected",
        })
        item["properties"] = props
        enhanced.append(item)

    if enhanced:
        layer = folium.FeatureGroup(name="Study polygons (exported GeoJSON)", show=show_boundaries)

        def style_fn(feature):
            props = feature["properties"]
            active = props["area_id"] == selected_area_id
            fill = (_ndvi_color(props["ndvi_value"])
                    if mode == "Annual NDVI" and verified and selected_year is not None
                    else COLORS["amber"] if active else COLORS["leaf"])
            return {
                "color": COLORS["forest"] if active else COLORS["leaf"],
                "weight": 4 if active else 2, "fillColor": fill,
                "fillOpacity": (0.56 if mode == "Annual NDVI" and verified and selected_year is not None
                                else 0.34 if active else 0.16),
            }

        geo_layer = folium.GeoJson(
            {"type": "FeatureCollection", "features": enhanced},
            name="Annual data" if verified else "Unverified study polygons",
            style_function=style_fn,
            highlight_function=lambda _: {"weight": 5, "fillOpacity": 0.72},
            tooltip=folium.GeoJsonTooltip(
                fields=["display_name", "year_label", "ndvi_label", "rainfall_label"],
                aliases=["Area:", "Year:", "NDVI:", "Rainfall:"]
            ),
            popup=folium.GeoJsonPopup(
                fields=["display_name", "area_id", "ndvi_label", "rainfall_label"],
                aliases=["Area:", "ID:", "NDVI:", "Rainfall:"]
            ),
        )
        geo_layer.add_to(layer)
        layer.add_to(fmap)
        try:
            Search(layer=geo_layer, search_label="display_name", geom_type="Polygon",
                   placeholder="Search study polygon", collapsed=True).add_to(fmap)
        except (TypeError, ValueError, AttributeError):
            pass

    # Candidate land-cover areas are USER ANNOTATIONS, not NASA classifications.
    if candidate_features:
        candidates_layer = folium.FeatureGroup(name="Candidate patches (unverified)", show=True)
        for item in candidate_features:
            geometry = item.get("geometry") if isinstance(item, dict) else None
            if _polygon_points(geometry) is None:
                continue
            props = item.get("properties", {})
            kind = props.get("candidate_type")
            if kind not in ("vegetated_candidate", "dry_candidate"):
                continue
            candidate_color = "#2E9B56" if kind == "vegetated_candidate" else "#BD8244"
            title = escape(str(props.get("label") or "Candidate patch"))
            folium.GeoJson(
                {"type": "Feature", "geometry": geometry, "properties": props},
                style_function=lambda _, color=candidate_color: {
                    "color": color, "weight": 3, "fillColor": color,
                    "fillOpacity": 0.3, "dashArray": "6,4"},
                tooltip=f"{title} — USER MARKED, NOT VERIFIED",
            ).add_to(candidates_layer)
        candidates_layer.add_to(fmap)

    if enable_drawing:
        Draw(
            export=False,
            position="topleft",
            show_geometry_on_click=False,
            draw_options={"polyline": False, "marker": False,
                          "circle": False, "circlemarker": False,
                          "rectangle": False, "polygon": {"allowIntersection": False}},
            edit_options={"edit": False, "remove": True},
        ).add_to(fmap)

    # Keep site markers and region geometry distinct: focus does not infer that
    # Tell es-Sultan equals area_a or Al-Auja equals area_b.
    if focus in REFERENCE_SITES:
        p = REFERENCE_SITES[focus]
        fmap.location = [p["lat"], p["lon"]]
        fmap.options["zoom"] = 14
    elif focus == "selected":
        chosen = next((f for f in features if f["properties"]["area_id"] == selected_area_id), None)
        if chosen:
            pts = _polygon_points(chosen["geometry"])
            fmap.fit_bounds([[min(p[0] for p in pts), min(p[1] for p in pts)],
                             [max(p[0] for p in pts), max(p[1] for p in pts)]],
                            padding=(30, 30), max_zoom=15)
        else:
            fmap.fit_bounds([[min(p["lat"] for p in locations), min(p["lon"] for p in locations)],
                             [max(p["lat"] for p in locations), max(p["lon"] for p in locations)]],
                            padding=(35, 35), max_zoom=13)
    else:
        points = [(p["lat"], p["lon"]) for p in locations]
        for f in features:
            points.extend(_polygon_points(f["geometry"]) or [])
        fmap.fit_bounds([[min(p[0] for p in points), min(p[1] for p in points)],
                         [max(p[0] for p in points), max(p[1] for p in points)]],
                        padding=(38, 38), max_zoom=13)

    Fullscreen(position="topleft").add_to(fmap)
    MeasureControl(position="topright", primary_length_unit="meters",
                   secondary_length_unit="kilometers", primary_area_unit="sqmeters",
                   secondary_area_unit="hectares").add_to(fmap)
    MousePosition(position="bottomright", prefix="Lat/Lon:", num_digits=6).add_to(fmap)
    if show_mini_map:
        MiniMap(position="bottomleft", toggle_display=True, width=140, height=105).add_to(fmap)
    folium.LayerControl(collapsed=True, position="topright").add_to(fmap)
    if mode == "Annual NDVI" and verified and selected_year is not None and enhanced:
        legend = """<div style="position:fixed;bottom:22px;right:16px;z-index:9999;
        background:white;padding:10px 12px;border-radius:10px;
        box-shadow:0 3px 14px #3336;font:12px Arial;max-width:185px">
        <b>Annual NDVI (polygon mean)</b><br>
        <span style='color:#B9745B'>■</span> &lt; 0<br>
        <span style='color:#D99A56'>■</span> 0 – 0.2<br>
        <span style='color:#BDD36E'>■</span> 0.2 – 0.4<br>
        <span style='color:#4C8B63'>■</span> 0.4 – 0.6<br>
        <span style='color:#163D2E'>■</span> ≥ 0.6<br>
        <span style='color:#87919A'>■</span> Missing</div>"""
        fmap.get_root().html.add_child(folium.Element(legend))
    return fmap


def render_map(
    study_areas: dict, selected_area_id: str,
    *, ndvi_df: Any = None, rainfall_df: Any = None,
    metadata: dict | None = None, selected_year: int | None = None,
) -> None:
    """Render Streamlit controls; app.py continues to own selected_area_id."""
    import streamlit as st
    from streamlit_folium import st_folium

    st.markdown("### 01 / BLOOM Earth Explorer · مستكشف أريحا")
    st.caption("ارسمِي بقعة مرشحة خضراء أو جافة، واحفظيها للمراجعة. التصنيف اليدوي ليس نتيجة NASA.")
    st.caption("Tell es-Sultan & Al-Auja are reference pins. Polygons come only from the supplied GeoJSON.")
    if selected_area_id not in AREA_NAMES:
        st.warning("Choose a valid study polygon in the main application.")
        return
    features = _valid_features(study_areas)
    raw_count = (len(study_areas.get("features", [])) if isinstance(study_areas, dict)
                 and isinstance(study_areas.get("features"), list) else 0)
    verified = isinstance(metadata, dict) and metadata.get("verification_status") == "verified"
    if not features:
        st.info("No valid study polygons loaded. Showing reference locations only — not NASA sampling areas.")
    elif raw_count != len(features) or len(features) < 2:
        st.warning("Some study polygons are missing or invalid. Confirm NASA GeoJSON exports.")
    if not verified:
        st.warning("Annual NASA observations are unavailable/unverified; no numerical values are shown.")

    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        focus_name = st.selectbox("🧭 الانتقال إلى", ["Both sites", "Selected polygon", "Tell es-Sultan", "Al-Auja"],
                                  key="bloom_map_focus")
    with col2:
        basemap = st.selectbox("🗺️ نمط الخريطة", BASEMAPS, key="bloom_map_basemap")
    with col3:
        mode = st.selectbox("🌱 طبقة البيانات", MODES, key="bloom_map_mode")
    a, b, c = st.columns(3)
    with a:
        pins = st.checkbox("Show place pins", value=True, key="bloom_map_pins")
    with b:
        outlines = st.checkbox("Show polygons", value=True, key="bloom_map_polygons")
    with c:
        mini = st.checkbox("Show mini-map", value=False, key="bloom_map_minimap")

    if selected_year is None:
        year = st.slider("📅 السنة", 2005, 2024, 2024, key="bloom_map_year")
    else:
        year = int(selected_year)
        st.caption(f"Year selected in app.py: {year}")
    focus = {"Both sites": "overview", "Selected polygon": "selected",
             "Tell es-Sultan": "tell_sultan", "Al-Auja": "al_auja"}[focus_name]
    if "bloom_candidate_patches" not in st.session_state:
        st.session_state["bloom_candidate_patches"] = []
    patches = st.session_state["bloom_candidate_patches"]
    st.markdown("#### ✏️ تحديد بقع خضراء أو جافة (يدويًا)")
    choose_col, name_col = st.columns(2)
    with choose_col:
        class_choice = st.selectbox(
            "نوع البقعة التي تريدين حفظها",
            ["vegetated_candidate", "dry_candidate"],
            format_func=lambda c: "🌿 خضراء مرشحة" if c == "vegetated_candidate" else "🏜️ جافة مرشحة",
            key="bloom_candidate_kind",
        )
    with name_col:
        patch_name = st.text_input("اسم البقعة (اختياري)", key="bloom_candidate_name")
    st.caption("اضغطي أداة المضلع في الخريطة (شكل خماسي)، ارسمي حدود البقعة، ثم اضغطي حفظ آخر مضلع. البقع لا تُرسل إلى GitHub تلقائيًا.")

    fmap = build_map(study_areas, selected_area_id, ndvi_df=ndvi_df,
                     rainfall_df=rainfall_df, metadata=metadata, selected_year=year,
                     focus=focus, basemap=basemap, mode=mode,
                     show_reference_points=pins, show_boundaries=outlines,
                     show_mini_map=mini, candidate_features=patches, enable_drawing=True)
    # Controls reset map only on deliberate changes, not on passive mouse moves.
    key = (f"bloom_jmap_{selected_area_id}_{focus}_{basemap}_{mode}_{year}_"
           f"{int(pins)}_{int(outlines)}_{int(mini)}_{len(patches)}")
    state = st_folium(
        fmap, height=550, use_container_width=True,
        returned_objects=["last_clicked", "last_active_drawing"], key=key,
    )

    save_col, clear_col = st.columns(2)
    with save_col:
        if st.button("💾 حفظ آخر بقعة مرسومة", key="bloom_patch_save"):
            drawing = state.get("last_active_drawing") if isinstance(state, dict) else None
            geometry = drawing.get("geometry") if isinstance(drawing, dict) else None
            if _polygon_points(geometry) is None:
                st.warning("ارسمي مضلعًا داخل منطقة أريحا أولًا. النقاط والخطوط وحدها لا تكفي.")
            else:
                new_feature = {
                    "type": "Feature", "geometry": geometry,
                    "properties": {
                        "candidate_type": class_choice,
                        "label": patch_name.strip() or f"Candidate {len(patches) + 1}",
                        "verification_status": "unverified_user_annotation",
                    },
                }
                if any(item["geometry"] == geometry for item in patches):
                    st.warning("هذه البقعة محفوظة سابقًا. ارسمي بقعة جديدة.")
                else:
                    patches.append(new_feature)
                    st.rerun()
    with clear_col:
        if st.button("🗑️ مسح البقع المحفوظة", key="bloom_patch_clear", disabled=not patches):
            st.session_state["bloom_candidate_patches"] = []
            st.rerun()

    if patches:
        import json
        st.download_button(
            "⬇️ تنزيل البقع المرشحة للمراجعة (GeoJSON)",
            data=json.dumps({"type": "FeatureCollection", "features": patches},
                            ensure_ascii=False, indent=2),
            file_name="candidate_patches_FOR_REVIEW.geojson",
            mime="application/geo+json",
            key="bloom_patch_download",
        )
        st.caption(f"عدد البقع المحفوظة: {len(patches)} — بقع يدوية غير موثّقة؛ لا تستخدميها كملف study_areas.geojson قبل المراجعة.")

    st.caption("Zoom +/− · Satellite · Fullscreen · Measure distance/area · Coordinate finder · Layer control")
    if isinstance(state, dict) and isinstance(state.get("last_clicked"), dict):
        click = state["last_clicked"]
        try:
            st.code(f"Latitude: {float(click['lat']):.6f}, Longitude: {float(click['lng']):.6f}")
        except (TypeError, ValueError, KeyError):
            pass

    st.markdown("##### Selected polygon: " + AREA_NAMES[selected_area_id])
    if verified:
        v_ndvi = _reading(ndvi_df, selected_area_id, year, "ndvi")
        v_rain = _reading(rainfall_df, selected_area_id, year, "rainfall_mm")
        left, right = st.columns(2)
        with left:
            st.metric(f"NDVI · {year}", f"{v_ndvi:.4f}" if v_ndvi is not None else "N/A")
        with right:
            st.metric(f"Rainfall · {year}", f"{v_rain:.1f} mm" if v_rain is not None else "N/A")
        st.caption("Numbers are annual polygon aggregates, NOT pixel-resolution NDVI or rainfall maps.")
    else:
        st.caption("Upload verified NDVI/rainfall CSV + metadata and exported GeoJSON to enable yearly measurements.")
