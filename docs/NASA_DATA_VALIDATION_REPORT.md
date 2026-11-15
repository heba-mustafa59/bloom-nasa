# BLOOM — Data file validation report

**Performed:** 2026-11-15 (UTC)  
**Scope:** Structural checks of the **current GitHub files**, not verification of their upstream NASA extraction.

## Results

| Test | NDVI CSV | Rainfall CSV |
| --- | ---: | ---: |
| Records | 40 | 40 |
| Study area IDs | `area_a`, `area_b` | `area_a`, `area_b` |
| Years per area | 20 (2005–2024) | 20 (2005–2024) |
| Unique `(year, area_id)` records | 40/40 | 40/40 |
| Non-finite values | 0 | 0 |
| Field constraints | NDVI in [-1,1]; `valid_observations` integral and 1–24 | Rainfall >=0; `valid_months=12` in all rows |
| Status | PASS for checked file structure | PASS for checked file structure |

### Descriptive summaries from committed files (not verified source measurements)

| Measure | Area A | Area B |
| --- | ---: | ---: |
| Mean NDVI over 2005–2024 | 0.224069 | 0.216464 |
| Mean annual rainfall, mm/year | 339.529 | 348.949 |

NDVI values across both polygons range from 0.157141 to 0.351735. Annual rainfall values range from 177.616 to 450.240 mm. These summaries merely reproduce committed numbers and **must not** be presented as authenticated NASA findings.

## GeoJSON structural inspection

- `FeatureCollection` with exactly two polygon features, IDs `area_a` and `area_b`.
- Both outer rings closed. Each feature is located within the expected Jericho region.
- Area A bounds (lon, lat): 35.493478–35.513649 E; 31.844873–31.864739 N.
- Area B bounds (lon, lat): 35.455770–35.490618 E; 31.832439–31.856572 N.
- Polygon structure checks do not certify field use, land-cover type, spatial overlap topology, or matching extraction footprints.

## NASA POWER point reference

`data/nasa_power_jericho_point_rainfall.csv` contains 20 annual rows, 2005–2024. All rows list `complete` and the expected number of days (365/366), with annual totals ranging 168.82–442.09 mm. This is a single approximate Jericho **point** series and is **not** a substitute for GPM area means. The original API response was not inspected in this review.

## Open blockers for verified status

1. Original Earth Engine task IDs, project/account and timestamp are not recorded.
2. Original task output and byte- or value-level comparison to uploaded NDVI/rainfall files have not been obtained.
3. Original polygon import and its correspondence to `study_areas.geojson` has not been independently established.
4. Land-use descriptions in GeoJSON are not substantiated with external evidence.
5. Independent extraction rerun and scientific QA review remain outstanding.

**Decision:** Leave `data/metadata.json` at `"verification_status": "pending"`. The application should not silently treat these values as verified NASA data until the blockers are closed.

Refer to `docs/NASA_DATA_PROVENANCE.md` for the reproducibility and approval checklist.
