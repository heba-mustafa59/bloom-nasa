"""Synthetic fixtures only: never observed NASA data or certified boundaries."""
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from modules.comparison import annual_series, click_selection, compare_regions, select_region
from modules.comparison_map import build_comparison_map, comparison_geography
from modules.ui_data import load_ui_context
from modules.ui_pages.compare import _map_changed


@pytest.fixture
def ctx():
    return load_ui_context('demo', 'area_a', 2005, 2024)


@pytest.mark.parametrize('slot,area,expected', [
    (0, 'area_b', ('area_b', 'area_a')),
    (1, 'area_a', ('area_b', 'area_a')),
    (0, 'area_a', ('area_a', 'area_b')),
])
def test_selection_swaps_without_duplicates(slot, area, expected):
    assert select_region(('area_a', 'area_b'), slot, area) == expected


def test_invalid_and_non_polygon_events():
    pair = ('area_a', 'area_b')
    for event in (None, {}, {'last_object_clicked_tooltip': 'Tell es-Sultan'},
                  {'last_object_clicked_tooltip': '<b>area_b</b>'}):
        assert click_selection(event, pair, 0, pair) == pair
    assert click_selection({'last_object_clicked_tooltip': 'area_b'}, pair, 0, ['area_a']) == pair
    assert click_selection({'last_object_clicked_tooltip': 'area_b'}, pair, 0, pair) == pair[::-1]
    with pytest.raises(ValueError):
        select_region(('area_a', 'area_a'), 0, 'area_a')


def test_map_callback_updates_widgets_and_consumes_once(monkeypatch):
    state = {'earth_pair': ('area_a', 'area_b'), 'earth_target': 'Region A',
             'map': {'last_object_clicked_tooltip': 'area_b', 'last_object_clicked_count': 1}}
    monkeypatch.setattr('modules.ui_pages.compare.st.session_state', state)
    _map_changed('map', ['area_a', 'area_b'])
    assert state['earth_pair'] == ('area_b', 'area_a')
    assert state['earth_region_0'] == 'area_b'
    assert state['earth_region_1'] == 'area_a'
    state['earth_target'] = 'Region B'
    _map_changed('map', ['area_a', 'area_b'])
    assert state['earth_pair'] == ('area_b', 'area_a')  # cached event must not replay
    state['map']['last_object_clicked_count'] = 2
    _map_changed('map', ['area_a', 'area_b'])
    assert state['earth_pair'] == ('area_a', 'area_b')


@pytest.mark.parametrize('criterion,field', [('ndvi', 'ndvi'), ('rainfall', 'rainfall_mm')])
def test_matching_year_means(ctx, criterion, field):
    frame = ctx.ndvi_df if field == 'ndvi' else ctx.rainfall_df
    frame.loc[(frame.area_id == 'area_a') & (frame.year == 2005), field] = None
    result = compare_regions(ctx, ('area_a', 'area_b'), criterion, 2005, 2024)
    assert result['common_years'] == list(range(2006, 2025))
    for i, area in enumerate(('area_a', 'area_b')):
        expected = frame.loc[(frame.area_id == area) & (frame.year > 2005), field].mean()
        assert result['scores'][i] == pytest.approx(expected)
    assert result['winner'] == ('area_a' if result['scores'][0] > result['scores'][1] else 'area_b')
    assert 'DEMO' in result['text']
    assert 'does not establish' in result['text']


def test_tie(ctx):
    ctx.ndvi_df.loc[:, 'ndvi'] = .3
    result = compare_regions(ctx, ('area_b', 'area_a'), 'ndvi', 2005, 2024)
    assert result['status'] == 'tie'
    assert result['winner'] is None


def test_improvement_reuses_trend_engine(ctx):
    for area, slope in [('area_a', .005), ('area_b', .001)]:
        mask = ctx.ndvi_df.area_id == area
        ctx.ndvi_df.loc[mask, 'ndvi'] = .2 + slope * (ctx.ndvi_df.loc[mask, 'year']-2005)
    result = compare_regions(ctx, ('area_a', 'area_b'), 'improvement', 2005, 2024)
    assert result['winner'] == 'area_a'
    assert result['scores'] == pytest.approx([.05, .01])
    assert result['trends'][0]['significant'] is True
    assert compare_regions(ctx, ('area_a', 'area_b'), 'improvement', 2020, 2024)['status'] == 'unavailable'


def test_improvement_inconclusive_and_decline(ctx):
    for area, sign in [('area_a', 1), ('area_b', -1)]:
        mask = ctx.ndvi_df.area_id == area
        ctx.ndvi_df.loc[mask, 'ndvi'] = [.3 + sign*.02*(-1)**i for i in range(20)]
    result = compare_regions(ctx, ('area_a', 'area_b'), 'improvement', 2005, 2024)
    assert result['status'] == 'inconclusive'
    assert result['winner'] is None
    ctx.ndvi_df.loc[:, 'ndvi'] = .4 - (ctx.ndvi_df.year-2005)*.001
    ctx.ndvi_df.loc[ctx.ndvi_df.area_id == 'area_b', 'ndvi'] -= (ctx.ndvi_df.loc[ctx.ndvi_df.area_id == 'area_b', 'year']-2005)*.001
    assert compare_regions(ctx, ('area_a', 'area_b'), 'improvement', 2005, 2024)['status'] == 'inconclusive'


def test_unverified_never_produces_claims(ctx):
    unverified = replace(ctx, mode='verified', metadata={})
    for criterion in ('ndvi', 'rainfall', 'improvement'):
        result = compare_regions(unverified, ('area_a', 'area_b'), criterion, 2005, 2024)
        assert result['status'] == 'unavailable'
        assert result['winner'] is None
    verified_fixture = replace(ctx, mode='verified', metadata={'verification_status': 'verified'})
    assert 'DEMO' not in compare_regions(verified_fixture, ('area_a', 'area_b'), 'ndvi', 2005, 2024)['text']


def test_missing_duplicates_quality_and_infinite_values(ctx):
    ctx.ndvi_df = pd.concat([ctx.ndvi_df, ctx.ndvi_df.iloc[[0]]], ignore_index=True)
    ctx.ndvi_df.loc[ctx.ndvi_df.year == 2006, 'ndvi'] = float('inf')
    ctx.ndvi_df.loc[ctx.ndvi_df.year == 2007, 'valid_observations'] = 0
    series = annual_series(ctx, 'ndvi', 'area_a', 2005, 2008)
    assert series.ndvi.isna().tolist() == [True, True, True, False]
    ctx.rainfall_df.loc[:, 'valid_months'] = 11
    assert compare_regions(ctx, ('area_a', 'area_b'), 'rainfall', 2005, 2024)['status'] == 'unavailable'
    with pytest.raises(ValueError):
        compare_regions(ctx, ('area_a', 'area_b'), 'unknown', 2005, 2024)


def test_exact_geometry_and_slot_colors(ctx):
    geography, verified = comparison_geography(ctx)
    assert not verified
    fmap = build_comparison_map(geography, ('area_b', 'area_a'))
    layers = [c for c in fmap._children.values() if isinstance(c, __import__('folium').GeoJson)]
    assert len(layers) == 2
    originals = {f['properties']['area_id']: f['geometry'] for f in geography['features']}
    for layer in layers:
        feature = layer.data['features'][0]
        area = feature['properties']['area_id']
        assert feature['geometry'] == originals[area]
        style = layer.style_function(feature)
        assert style['color'] == ('#2E7254' if area == 'area_b' else '#D99A56')
        assert style['dashArray'] == '7 5'
    assert 'area_a' in fmap.get_root().render()
    assert build_comparison_map({}, ('area_a', 'area_b'))


def test_streamlit_selection_criteria_and_missing_data():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / 'ui_app.py', default_timeout=40).run()
    app.sidebar.selectbox[0].select('Compare').run()
    assert not app.exception
    assert len(app.get('plotly_chart')) == 1
    app.selectbox(key='earth_region_0').select('area_b').run()
    assert app.session_state['earth_pair'] == ('area_b', 'area_a')
    assert app.selectbox(key='earth_region_1').value == 'area_a'
    app.selectbox(key='earth_criterion').select('improvement').run()
    app.slider(key='earth_cursor').set_value(2010).run()
    app.sidebar.slider[0].set_value((2018, 2024)).run()
    assert app.slider(key='earth_cursor').value == 2018
    assert not app.exception
    app.sidebar.radio[0].set_value('Verified NASA').run()
    assert not app.exception
    assert any('Data unavailable' in v.value for v in app.info)
    assert any('UNVERIFIED GEOGRAPHY' in v.value for v in app.warning)
    app.sidebar.slider[0].set_value((2024, 2024)).run()
    assert not app.exception
