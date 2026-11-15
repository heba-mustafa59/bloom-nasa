"""Exact-boundary comparison layer, independent of science and annotation tools."""
import json
from pathlib import Path

import folium
from folium.plugins import Fullscreen
from modules.map_view import _valid_features

SLOT_COLORS = ('#2E7254', '#D99A56')


def comparison_geography(ctx):
    """Retain supplied polygons when science loading fails, without certifying them."""
    if ctx.geojson.get('features'):
        return ctx.geojson, ctx.metadata.get('verification_status') == 'verified' and not ctx.is_demo
    try:
        source = Path(__file__).resolve().parents[1] / 'data' / 'study_areas.geojson'
        return json.loads(source.read_text(encoding='utf-8')), False
    except (OSError, ValueError):
        return {}, False


def build_comparison_map(geography, pair, basemap='Streets', verified=False):
    if basemap not in ('Streets', 'Satellite'):
        raise ValueError('Unknown basemap')
    features = _valid_features(geography)
    fmap = folium.Map(location=[31.87, 35.46], zoom_start=12, tiles=None, control_scale=True)
    # This layer uses no Bootstrap, jQuery or icon markers. Load only Leaflet
    # plus the fullscreen plugin, reducing external dependencies.
    fmap.default_js = [item for item in fmap.default_js if item[0] == 'leaflet']
    fmap.default_css = [item for item in fmap.default_css if item[0] == 'leaflet_css']
    folium.TileLayer('OpenStreetMap', name='Streets', show=basemap == 'Streets').add_to(fmap)
    folium.TileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles © Esri and contributors', name='Satellite', show=basemap == 'Satellite',
    ).add_to(fmap)
    for feature in features:
        area = feature['properties']['area_id']
        color = SLOT_COLORS[pair.index(area)]
        # Plain tooltip IDs are intentional: streamlit-folium returns their text.
        # No spatial guessing, bounding-box hits or fabricated geometry.
        folium.GeoJson(
            feature, name=area, tooltip=folium.Tooltip(area),
            style_function=lambda _, c=color: dict(color=c, fillColor=c, weight=4,
                                                    fillOpacity=.28, dashArray=None if verified else '7 5'),
            highlight_function=lambda _: dict(weight=6, fillOpacity=.48),
        ).add_to(fmap)
    if features:
        bounds = folium.GeoJson({'type': 'FeatureCollection', 'features': features}).get_bounds()
        fmap.fit_bounds(bounds, padding=(30, 30))
    Fullscreen().add_to(fmap)
    folium.LayerControl(collapsed=True).add_to(fmap)
    return fmap
