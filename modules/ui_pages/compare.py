"""BLOOM Earth Comparison Explorer — map selection and synchronized evidence."""
from dataclasses import replace
from hashlib import sha256
import json

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from streamlit_folium import st_folium

from modules.comparison import CRITERIA, annual_series, click_selection, compare_regions, select_region
from modules.comparison_map import SLOT_COLORS, build_comparison_map, comparison_geography
from modules.map_view import _valid_features
from modules.ui_components import number, page_header, section_title, stat_card, style_figure
from modules.ui_data import AREA_LABELS, trend_for


def _dropdown_changed(slot):
    pair = st.session_state['earth_pair']
    pair = select_region(pair, slot, st.session_state[f'earth_region_{slot}'])
    st.session_state['earth_pair'] = pair
    for i, area in enumerate(pair):
        st.session_state[f'earth_region_{i}'] = area


def _map_changed(key, available):
    event = st.session_state.get(key, {})
    count = event.get('last_object_clicked_count') if isinstance(event, dict) else None
    token = (key, count)
    if not count or token == st.session_state.get('earth_consumed_click'):
        return
    st.session_state['earth_consumed_click'] = token
    pair = click_selection(event, st.session_state['earth_pair'],
                           0 if st.session_state['earth_target'] == 'Region A' else 1, available)
    st.session_state['earth_pair'] = pair
    for i, area in enumerate(pair):
        st.session_state[f'earth_region_{i}'] = area


def render(ctx, navigate):
    page_header('04 / EARTH COMPARISON EXPLORER', 'Two regions. One frame of evidence.',
                'Select exact study boundaries, align the years, and compare what the observations support.')
    if ctx.is_demo:
        st.warning('DEMO · All comparisons below use synthetic values, not NASA observations. '
                   'The map shows supplied geography only, with no synthetic spatial measurements.')
    st.session_state.setdefault('earth_pair', ('area_a', 'area_b'))
    pair = st.session_state['earth_pair']
    left, right = st.columns(2, gap='large')
    for slot, col in enumerate((left, right)):
        st.session_state.setdefault(f'earth_region_{slot}', pair[slot])
        with col:
            st.selectbox(f'Region {"A" if slot == 0 else "B"} · {"green" if slot == 0 else "amber"}',
                         list(AREA_LABELS), format_func=AREA_LABELS.get, key=f'earth_region_{slot}',
                         on_change=_dropdown_changed, args=(slot,),
                         help='Selecting the other region swaps the pair. Regions always remain distinct.')
    pair = st.session_state['earth_pair']
    geography, verified_geo = comparison_geography(ctx)
    available = [f['properties']['area_id'] for f in _valid_features(geography)]
    section_title('01 / SELECT', 'The landscape, in context',
                  'Region A · green / Region B · amber. Choose a slot, then click a boundary. Dropdowns work with keyboard navigation.')
    a, b = st.columns([2, 1])
    with a:
        st.radio('Map click assigns', ['Region A', 'Region B'], horizontal=True, key='earth_target')
    with b:
        basemap = st.selectbox('Basemap', ['Streets', 'Satellite'], key='earth_basemap')
    if not available:
        st.info('Study boundaries unavailable. No polygons have been invented; use the region selectors to inspect data availability.')
    elif not verified_geo:
        st.warning('UNVERIFIED GEOGRAPHY · Dashed outlines reproduce the supplied GeoJSON exactly. '
                   'Their provenance and suitability as NASA study boundaries have not been verified.')
    else:
        st.caption('Verified study geography · exact exported GeoJSON boundaries.')
    if len(available) < 2:
        st.caption('Some regions cannot be selected on the map because their boundaries are missing or invalid.')
    identity = sha256(json.dumps([geography, pair, basemap, verified_geo, ctx.mode], sort_keys=True).encode()).hexdigest()[:16]
    map_key = f'earth_map_{identity}'
    st_folium(build_comparison_map(geography, pair, basemap, verified_geo),
              height=470, use_container_width=True, key=map_key,
              returned_objects=['last_object_clicked_tooltip', 'last_object_clicked_count'],
              on_change=lambda: _map_changed(map_key, available))
    st.caption('Map tiles © OpenStreetMap / Esri. Basemaps provide context, not vegetation classifications. '
               'Map access depends on your browser reaching the tile providers.')

    section_title('02 / ALIGN', 'A shared observation window',
                  'The sidebar sets the comparison period. The year cursor explores annual values without changing the verdict window.')
    start, end = ctx.start_year, ctx.end_year
    if start < end:
        cursor = st.session_state.get('earth_cursor', end)
        st.session_state['earth_cursor'] = min(end, max(start, cursor))
        year = st.slider('Explore year', start, end, key='earth_cursor')
    else:
        year = start
        st.caption(f'Explore year · {year}')
    criterion = st.selectbox('Comparison criterion', list(CRITERIA), format_func=CRITERIA.get,
                            key='earth_criterion')
    st.caption('Highest annual rainfall compares the mean of annual totals over matching years, not the single wettest year.')
    result = compare_regions(ctx, pair, criterion, start, end)
    if result['status'] == 'unavailable':
        st.info(result['text'])
        if ctx.error:
            with st.expander('Why verified observations are unavailable'):
                st.text(ctx.error)
        st.caption('Supply independently verified observations, exact polygons and data/metadata.json per docs/CONTRACT.md. '
                   'Unverified values are never substituted into scientific comparisons.')
    else:
        st.markdown('<div class="earth-verdict"><span>DEMO / COMPARISON VERDICT</span></div>'
                    if ctx.is_demo else '<div class="earth-verdict"><span>COMPARISON VERDICT</span></div>',
                    unsafe_allow_html=True)
        st.write(result['text'])
    prefix = 'DEMO · ' if ctx.is_demo else ''
    cards = st.columns(2, gap='large')
    for slot, col in enumerate(cards):
        with col:
            nd = annual_series(ctx, 'ndvi', pair[slot], year, year).iloc[0]['ndvi']
            rain = annual_series(ctx, 'rainfall_mm', pair[slot], year, year).iloc[0]['rainfall_mm']
            stat_card(f'{prefix}REGION {"A" if slot == 0 else "B"} / {AREA_LABELS[pair[slot]]}',
                      f'{number(nd, 4)} NDVI', f'{year} · {number(rain, 1)} mm annual rainfall',
                      'leaf' if slot == 0 else 'amber')
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=.12,
                        subplot_titles=(prefix + 'Vegetation · NDVI', prefix + 'Rainfall · mm/year'))
    for slot, area in enumerate(pair):
        for row, field in enumerate(('ndvi', 'rainfall_mm'), 1):
            frame = annual_series(ctx, field, area, start, end)
            fig.add_trace(go.Scatter(x=frame.year, y=frame[field], mode='lines+markers',
                                    connectgaps=False, name=prefix + f'Region {"A" if slot == 0 else "B"} · {AREA_LABELS[area]}',
                                    legendgroup=area, showlegend=row == 1,
                                    line=dict(color=SLOT_COLORS[slot], width=3),
                                    hovertemplate='%{x}: %{y:.4f}<extra>%{fullData.name}</extra>'), row=row, col=1)
    style_figure(fig)
    fig.update_layout(height=650, title=prefix + f'Aligned annual observations · {start}–{end}')
    fig.update_xaxes(range=[start-.4, end+.4], tickformat='d', matches='x')
    fig.update_yaxes(title_text='NDVI · unitless', row=1, col=1)
    fig.update_yaxes(title_text='Rainfall · mm/year', row=2, col=1)
    fig.add_vline(x=year, line_dash='dot', line_color='#87919A')
    if ctx.is_demo:
        fig.add_annotation(text='DEMO · SYNTHETIC', xref='paper', yref='paper', x=.5, y=.5,
                           showarrow=False, opacity=.28, font=dict(size=28, color='#163D2E'))
    st.plotly_chart(fig, use_container_width=True)

    section_title('03 / INTERPRET', 'Evidence & limits',
                  'A descriptive lead is a starting point for investigation, not a causal explanation.')
    st.write(f'{prefix}{len(result["common_years"])} matching valid years for the selected criterion; '
             f'{end-start+1-len(result["common_years"])} years excluded from the verdict. '
             'Charts retain individual observations and show gaps; verdicts use only matching years.')
    rows = []
    for slot, area in enumerate(pair):
        # Reuse the shared trend engine on the same matched years used by the verdict.
        for field in ('ndvi', 'rainfall_mm'):
            frames = [annual_series(ctx, field, a, start, end) for a in pair]
            common = set(frames[0].dropna(subset=[field]).year) & set(frames[1].dropna(subset=[field]).year)
            frame = frames[slot].loc[frames[slot].year.isin(common)]
            matched_ctx = replace(ctx, ndvi_df=frame if field == 'ndvi' else pd.DataFrame(),
                                  rainfall_df=frame if field == 'rainfall_mm' else pd.DataFrame())
            trend = trend_for(matched_ctx, field, area)
            rows.append({'Region': prefix + f'{"A" if slot == 0 else "B"} · {AREA_LABELS[area]}',
                         'Variable': field, 'Matched years': len(common),
                         'Direction': trend.get('direction'), 'Slope / decade': trend.get('slope_per_decade'),
                         'Mann–Kendall p': trend.get('p_value')})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption('Trend estimates require at least 10 usable years. Mann–Kendall uses α=0.05 and assumes '
               'independent observations; serial correlation, missing years and multiple testing affect interpretation. '
               'Individual trend p-values do not test the difference between regions or their slopes.')
    st.info('Higher NDVI does not automatically indicate better ecosystem health. Rainfall–NDVI correlation '
            'does not establish causation, irrigation, or land-use type. MODIS (~250 m) and GPM (~11 km) '
            'have different spatial support; small polygons may share rainfall pixels. '
            'Missing values remain missing and are never replaced with zero.')
    if ctx.metadata.get('limitations'):
        with st.expander('Source-specific limitations'):
            st.write(ctx.metadata['limitations'])
    if st.button('Generate a report ↗', type='primary', key='compare_next'):
        navigate('Reports')
