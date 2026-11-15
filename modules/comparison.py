"""Comparison policy; shared analytics own trend estimation and significance."""
from __future__ import annotations

from math import isclose
import pandas as pd

from modules.map_view import _reading
from modules.trend_analysis import analyze_trend
from modules.ui_data import AREA_LABELS

CRITERIA = {
    'ndvi': 'Highest average NDVI',
    'improvement': 'Strongest vegetation improvement',
    'rainfall': 'Highest annual rainfall',
}


def select_region(pair, slot, area):
    """Assign a slot, swapping when the other region is already selected."""
    if slot not in (0, 1) or area not in AREA_LABELS:
        raise ValueError('Invalid region selection')
    if len(pair) != 2 or set(pair) != set(AREA_LABELS):
        raise ValueError('Choose two distinct contract regions')
    result = list(pair)
    if area != result[slot]:
        result.reverse()
    return tuple(result)


def click_selection(event, pair, slot, available):
    """Consume only exact polygon tooltip IDs from supported component events."""
    if not isinstance(event, dict):
        return tuple(pair)
    area = event.get('last_object_clicked_tooltip')
    area = area.strip() if isinstance(area, str) else None
    if area not in available or area not in AREA_LABELS:
        return tuple(pair)
    return select_region(pair, slot, area)


def annual_series(ctx, field, area, start, end):
    """Preserve gaps and reject ambiguous/invalid annual measurements."""
    source = ctx.ndvi_df if field == 'ndvi' else ctx.rainfall_df
    # Research-preview CSVs have already passed the shared strict local loader.
    # They may be examined as observations while provenance remains PENDING.
    authorized = (
        ctx.is_demo
        or ctx.metadata.get('verification_status') == 'verified'
        or (
            ctx.mode == 'local'
            and ctx.ready
            and ctx.metadata.get('verification_status') == 'pending'
        )
    )
    return pd.DataFrame({
        'year': range(start, end + 1),
        'area_id': area,
        field: [_reading(source, area, y, field) if authorized else None
                for y in range(start, end + 1)],
    })


def compare_regions(ctx, pair, criterion, start, end):
    if criterion not in CRITERIA:
        raise ValueError('Unknown comparison criterion')
    select_region(pair, 0, pair[0])
    if not 2005 <= start <= end <= 2024:
        raise ValueError('Comparison window must be within 2005–2024')
    field = 'rainfall_mm' if criterion == 'rainfall' else 'ndvi'
    series = [annual_series(ctx, field, area, start, end) for area in pair]
    common = set(series[0].dropna(subset=[field]).year) & set(series[1].dropna(subset=[field]).year)
    trends, scores = [], []
    for frame in series:
        matched = frame.loc[frame.year.isin(common)]
        trend = analyze_trend(matched, field, start, end)
        trends.append(trend)
        scores.append(trend['slope_per_decade'] if criterion == 'improvement'
                      else float(matched[field].mean()) if common else None)
    result = dict(status='unavailable', winner=None, scores=scores, trends=trends,
                  common_years=sorted(common), field=field,
                  text='Data unavailable — comparable, validated observations are required for both regions.')
    prefix = 'DEMO — synthetic comparison. ' if ctx.is_demo else ''
    if any(value is None for value in scores):
        result['text'] = prefix + result['text']
        return result
    if isclose(scores[0], scores[1], rel_tol=1e-9, abs_tol=1e-9):
        result.update(status='tie', text=prefix + 'Tie within numerical tolerance on the matched years; neither region leads.')
        return result
    leader = 0 if scores[0] > scores[1] else 1
    label = AREA_LABELS[pair[leader]]
    if criterion == 'improvement' and (scores[leader] <= 0 or trends[leader]['direction'] != 'increasing'):
        result.update(status='inconclusive', text=prefix + 'Statistically inconclusive: no leading positive slope has a significant increasing trend. Non-significance is not stability.')
        return result
    units = 'NDVI / decade' if criterion == 'improvement' else 'mm/year' if criterion == 'rainfall' else 'NDVI'
    detail = ('larger estimated positive NDVI slope' if criterion == 'improvement'
              else 'higher mean of annual rainfall totals' if criterion == 'rainfall'
              else 'higher average NDVI')
    result.update(status='descriptive_lead', winner=pair[leader], text=(
        f'{prefix}{label} leads descriptively with the {detail}: {scores[leader]:.4f} versus '
        f'{scores[1-leader]:.4f} {units}, across {len(common)} matching years ({start}–{end}). '
        'This does not establish a statistically significant difference between regions.'
    ))
    return result
