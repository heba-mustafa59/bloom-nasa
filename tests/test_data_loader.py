import json
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.data_loader import load_datasets


def _write_data(folder):
    years = range(2005, 2025)
    rows = [{'year': y, 'area_id': a, 'ndvi': .2, 'valid_observations': 20}
            for a in ('area_a', 'area_b') for y in years]
    pd.DataFrame(rows).to_csv(folder / 'ndvi_annual.csv', index=False)
    rain = [{'year': y, 'area_id': a, 'rainfall_mm': 100.0, 'valid_months': 12}
            for a in ('area_a', 'area_b') for y in years]
    pd.DataFrame(rain).to_csv(folder / 'rainfall_annual.csv', index=False)
    # Test fixture coordinates are synthetic and MUST NEVER be used for actual NASA export.
    geojson = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'properties': {'area_id': a},
         'geometry': {'type': 'Polygon', 'coordinates': [[[0, 0], [0, 1], [1, 1], [0, 0]]]}}
        for a in ('area_a', 'area_b')]}
    (folder / 'study_areas.geojson').write_text(json.dumps(geojson))
    (folder / 'metadata.json').write_text(json.dumps({'verification_status': 'verified'}))


def test_load_valid_fixture(tmp_path):
    _write_data(tmp_path)
    ndvi, rain, geo, meta = load_datasets(tmp_path)
    assert len(ndvi) == len(rain) == 40
    assert len(geo['features']) == 2


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_datasets(tmp_path)


def test_reject_invalid_ndvi(tmp_path):
    _write_data(tmp_path)
    path = tmp_path / 'ndvi_annual.csv'
    df = pd.read_csv(path)
    df.loc[0, 'ndvi'] = 2.3
    df.to_csv(path, index=False)
    with pytest.raises(ValueError, match='NDVI'):
        load_datasets(tmp_path)


def test_reject_incomplete_rainfall(tmp_path):
    _write_data(tmp_path)
    path = tmp_path / 'rainfall_annual.csv'
    df = pd.read_csv(path)
    df.loc[0, 'valid_months'] = 11
    df.to_csv(path, index=False)
    with pytest.raises(ValueError, match='incomplete'):
        load_datasets(tmp_path)


def test_reject_duplicate(tmp_path):
    _write_data(tmp_path)
    path = tmp_path / 'ndvi_annual.csv'
    df = pd.read_csv(path)
    df.loc[0, ['year', 'area_id']] = df.loc[1, ['year', 'area_id']]
    df.to_csv(path, index=False)
    with pytest.raises(ValueError, match='Duplicate'):
        load_datasets(tmp_path)

def test_pending_upload_rejected_in_strict_mode_but_available_for_review(tmp_path):
    """Pending NASA provenance is not a reason to fabricate or erase CSV rows."""
    _write_data(tmp_path)
    path = tmp_path / "metadata.json"
    metadata = json.loads(path.read_text())
    metadata["verification_status"] = "pending"
    path.write_text(json.dumps(metadata))

    with pytest.raises(ValueError, match="independently verified"):
        load_datasets(tmp_path)

    ndvi, rainfall, polygons, loaded_metadata = load_datasets(
        tmp_path, require_verified=False
    )
    assert len(ndvi) == len(rainfall) == 40
    assert len(polygons["features"]) == 2
    assert loaded_metadata["verification_status"] == "pending"
