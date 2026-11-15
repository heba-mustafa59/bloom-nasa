"""Load and validate real BLOOM NASA observations. Never generate surrogate data."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
YEARS = set(range(2005, 2025))
AREAS = {'area_a', 'area_b'}


def _validate_table(df: pd.DataFrame, value_col: str, other_cols: set[str]) -> pd.DataFrame:
    required = {'year', 'area_id', value_col} | other_cols
    if not required.issubset(df.columns):
        raise ValueError(f'Missing columns: {sorted(required - set(df.columns))}')
    if len(df) != 40:
        raise ValueError(f'Expected 40 records (2 areas x 20 years), got {len(df)}')
    if df[list(required)].isna().any().any():
        raise ValueError('Null/blank values found; do not replace missing NASA measurements with zero')
    result = df.copy()
    for col in ('year', value_col, *other_cols):
        result[col] = pd.to_numeric(result[col], errors='raise')
    if not (result['year'] % 1 == 0).all():
        raise ValueError('Years must be integers')
    if set(result['year'].astype(int)) != YEARS or set(result['area_id']) != AREAS:
        raise ValueError('Unexpected years or study areas')
    if result.duplicated(['year', 'area_id']).any():
        raise ValueError('Duplicate (year, area_id) pairs')
    if not (result.groupby('area_id')['year'].nunique() == 20).all():
        raise ValueError('Each study area requires all 20 years')
    if value_col == 'ndvi':
        if not result['ndvi'].between(-1, 1).all():
            raise ValueError('NDVI values must be between -1 and 1')
        n = result['valid_observations']
        if not ((n > 0) & (n <= 24) & (n % 1 == 0)).all():
            raise ValueError('Invalid NDVI composite counts')
    else:
        if not (result['rainfall_mm'] >= 0).all():
            raise ValueError('Annual precipitation cannot be negative')
        if 'valid_months' in result.columns and not (result['valid_months'] == 12).all():
            raise ValueError('Rainfall includes incomplete years')
    result['year'] = result['year'].astype(int)
    return result.sort_values(['area_id', 'year']).reset_index(drop=True)


def load_datasets(data_dir: str | Path | None = None, *, require_verified: bool = True):
    """Return the original uploaded observations, polygons and metadata.

    By default, reject exports whose provenance is not independently verified.
    UI review mode may set require_verified=False to *inspect* documented
    pending data, but must identify all results as provisional.
    """
    folder = Path(data_dir) if data_dir is not None else ROOT / 'data'
    paths = {name: folder / name for name in
             ('ndvi_annual.csv', 'rainfall_annual.csv', 'study_areas.geojson', 'metadata.json')}
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError('Missing NASA data exports: ' + ', '.join(missing))
    ndvi = _validate_table(pd.read_csv(paths['ndvi_annual.csv']), 'ndvi', {'valid_observations'})
    rainfall = _validate_table(pd.read_csv(paths['rainfall_annual.csv']), 'rainfall_mm', set())
    with open(paths['study_areas.geojson'], encoding='utf-8') as f:
        shapes = json.load(f)
    if shapes.get('type') != 'FeatureCollection' or len(shapes.get('features', [])) != 2:
        raise ValueError('GeoJSON must contain exactly two features')
    for feat in shapes['features']:
        if feat.get('geometry', {}).get('type') not in ('Polygon', 'MultiPolygon'):
            raise ValueError('Study areas must be polygon geometries')
        if not feat['geometry'].get('coordinates'):
            raise ValueError('Study polygons cannot have empty coordinates')
    ids = {f.get('properties', {}).get('area_id') for f in shapes['features']}
    if ids != AREAS:
        raise ValueError('GeoJSON area_id must match area_a and area_b')
    with open(paths['metadata.json'], encoding='utf-8') as f:
        metadata = json.load(f)
    if not isinstance(metadata, dict):
        raise ValueError('metadata.json must contain an object')
    status = metadata.get('verification_status')
    if status not in ('pending', 'verified'):
        raise ValueError('metadata.json must declare a known verification_status')
    if require_verified and status != 'verified':
        raise ValueError('metadata.json must explicitly mark independently verified exports')
    return ndvi, rainfall, shapes, metadata

