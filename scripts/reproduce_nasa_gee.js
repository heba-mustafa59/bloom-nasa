/**
 * BLOOM — REPRODUCIBILITY RE-RUN ONLY; not the original completed export.
 *
 * Study-area coordinates are FROZEN from data/study_areas.geojson as reviewed
 * on 2026-11-15.  This file requires NO "areaA" drawing/import.  It must NOT
 * replace scripts/export_nasa_data.js or data/*.csv in the BLOOM application.
 *
 * Run only in your authenticated Google Earth Engine Code Editor, then start
 * the THREE new BLOOM_RECHECK_* batch tasks from Tasks. The separate folder
 * BLOOM_EE_RECHECK_2026 prevents confusion with original task outputs.
 *
 * The original reduction methodology below is intentionally preserved;
 * this is a reproducibility re-execution, NOT independent method validation.
 */

// Frozen GeoJSON, exact data/study_areas.geojson content (2 source polygons).
var FROZEN_GEOJSON = {"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[35.493478391493326,31.855152527100216],[35.49540958198405,31.847169269768166],[35.512489888990885,31.844872588301175],[35.51364860328532,31.85518897874505],[35.50931415351725,31.86331733562909],[35.503692243422044,31.864738813206344],[35.493478391493326,31.855152527100216]]]},"id":"0","properties":{"area_id":"area_a","description":"Agricultural study area"}},{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[35.46727164986706,31.84869870497238],[35.457572782069214,31.8475321630974],[35.4557703376112,31.843303325126133],[35.46469672921276,31.838199296993103],[35.479631269007676,31.83243869753893],[35.48950179818249,31.8475321630974],[35.49061759713268,31.855624743478405],[35.48126205208874,31.85657247670732],[35.476369702845574,31.847021796387743],[35.46727164986706,31.84869870497238]]]},"id":"1","properties":{"area_id":"area_b","description":"Mixed agricultural comparison area"}}]};

var studyA = ee.Geometry.Polygon(FROZEN_GEOJSON.features[0].geometry.coordinates);
var studyB = ee.Geometry.Polygon(FROZEN_GEOJSON.features[1].geometry.coordinates);
print('RECHECK: source polygon order', 'area_a = eastern', 'area_b = western');
print('RECHECK: 2 frozen original study polygons', studyA, studyB);

// 2. Stable IDs shared by map, CSV files, and statistical analysis.
var areas = ee.FeatureCollection([
  ee.Feature(studyA, {
    area_id: 'area_a',
    description: 'Agricultural study area'
  }),
  ee.Feature(studyB, {
    area_id: 'area_b',
    description: 'Mixed agricultural comparison area'
  })
]);

var years = ee.List.sequence(2005, 2024);
var modisScale = 250;
var gpmScale = 11132;

Map.centerObject(areas, 12);
Map.addLayer(studyA, {color: '00FF00'}, 'Area A (green)');
Map.addLayer(studyB, {color: '0000FF'}, 'Area B (blue)');
print('Polygon count (must be 2):', areas.size());
print('Study areas:', areas);

// 3. NASA MODIS NDVI, 16-day observations, 250 m.
// Only use SummaryQA == 0 (high-quality pixels).
var modis = ee.ImageCollection('MODIS/061/MOD13Q1')
  .filterDate('2005-01-01', '2025-01-01')
  .filterBounds(areas.geometry())
  .select(['NDVI', 'SummaryQA']);

// 4. NASA GPM IMERG Monthly V07: monthly mean rate in mm/hour.
var gpm = ee.ImageCollection('NASA/GPM_L3/IMERG_MONTHLY_V07')
  .filterDate('2005-01-01', '2025-01-01')
  .filterBounds(areas.geometry())
  .select('precipitation');

function ndviYearArea(year, feature) {
  year = ee.Number(year);
  feature = ee.Feature(feature);
  var start = ee.Date.fromYMD(year, 1, 1);
  var end = start.advance(1, 'year');
  var subset = modis.filterDate(start, end);

  var measurements = ee.FeatureCollection(
    subset.toList(subset.size()).map(function(item) {
      var image = ee.Image(item);
      var good = image.select('SummaryQA').eq(0);
      var mean = image.select('NDVI')
        .multiply(0.0001)
        .updateMask(good)
        .reduceRegion({
          reducer: ee.Reducer.mean(),
          geometry: feature.geometry(),
          scale: modisScale,
          maxPixels: 1e8,
          tileScale: 4
        }).get('NDVI');
      return ee.Feature(null, {ndvi: mean});
    })
  ).filter(ee.Filter.notNull(['ndvi']));

  var count = measurements.size();
  return ee.Feature(null, {
    year: year,
    area_id: feature.get('area_id'),
    ndvi: ee.Algorithms.If(count.gt(0), measurements.aggregate_mean('ndvi'), null),
    valid_observations: count
  });
}

function rainYearArea(year, feature) {
  year = ee.Number(year);
  feature = ee.Feature(feature);
  var months = ee.List.sequence(1, 12);

  var monthly = ee.FeatureCollection(months.map(function(month) {
    var first = ee.Date.fromYMD(year, month, 1);
    var next = first.advance(1, 'month');
    var images = gpm.filterDate(first, next);
    var imageCount = images.size();

    // The zero image is ONLY an internal computation fallback.
    // The month's output is NULL unless there is exactly one image.
    var precipitationRate = ee.Image(ee.Algorithms.If(
      imageCount.eq(1),
      images.first(),
      ee.Image.constant(0).rename('precipitation')
    ));

    var hours = next.difference(first, 'hour');
    var mm = precipitationRate.select('precipitation')
      .multiply(hours)
      .rename('rainfall_mm')
      .reduceRegion({
        reducer: ee.Reducer.mean(),
        geometry: feature.geometry(),
        scale: gpmScale,
        maxPixels: 1e8,
        tileScale: 4
      }).get('rainfall_mm');

    return ee.Feature(null, {
      rainfall_mm: ee.Algorithms.If(imageCount.eq(1), mm, null)
    });
  }));

  var valid = monthly.filter(ee.Filter.notNull(['rainfall_mm']));
  var validMonths = valid.size();
  return ee.Feature(null, {
    year: year,
    area_id: feature.get('area_id'),
    rainfall_mm: ee.Algorithms.If(
      validMonths.eq(12), valid.aggregate_sum('rainfall_mm'), null
    ),
    valid_months: validMonths
  });
}

// 5. Annual time series for each of the two study areas.
var areaList = areas.toList(areas.size());
var ndviTable = ee.FeatureCollection(years.map(function(year) {
  return ee.FeatureCollection(areaList.map(function(area) {
    return ndviYearArea(year, ee.Feature(area));
  }));
})).flatten();

var rainfallTable = ee.FeatureCollection(years.map(function(year) {
  return ee.FeatureCollection(areaList.map(function(area) {
    return rainYearArea(year, ee.Feature(area));
  }));
})).flatten();

print('NDVI preview (check numbers):', ndviTable.limit(5));
print('Rainfall preview (check numbers):', rainfallTable.limit(5));
print('Missing values remain NULL, not zero. Annual rain requires 12 valid months.');

// 6. RECHECK tasks: Run to queue, then manually start THREE new tasks.
// Do NOT overwrite the archived ORIGINAL Earth Engine exports.
Export.table.toDrive({
  collection: ndviTable,
  description: 'BLOOM_RECHECK_ndvi_annual',
  folder: 'BLOOM_EE_RECHECK_2026',
  fileNamePrefix: 'ndvi_annual',
  fileFormat: 'CSV',
  selectors: ['year', 'area_id', 'ndvi', 'valid_observations']
});

Export.table.toDrive({
  collection: rainfallTable,
  description: 'BLOOM_RECHECK_rainfall_annual',
  folder: 'BLOOM_EE_RECHECK_2026',
  fileNamePrefix: 'rainfall_annual',
  fileFormat: 'CSV',
  selectors: ['year', 'area_id', 'rainfall_mm', 'valid_months']
});

Export.table.toDrive({
  collection: areas,
  description: 'BLOOM_RECHECK_study_areas',
  folder: 'BLOOM_EE_RECHECK_2026',
  fileNamePrefix: 'study_areas',
  fileFormat: 'GeoJSON'
});
