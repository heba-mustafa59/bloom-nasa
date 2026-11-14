# BLOOM — خريطة أريحا التفاعلية (بدون بيانات NASA وهمية)

## أي ملفات تعدّلي؟

- **المطلوب الرئيسي:** انسخي `modules/map_view.py` الجديد مكان `modules/map_view.py` على فرع `feature/ui`.
- **الاختبارات:** انسخي `tests/test_map_view.py` إلى `tests/test_map_view.py` (ملف جديد).
- **التكامل:** `integration_example/app.py` مثال كامل مبني على `app.py` الذي تم رفعه في هذه المحادثة؛ **لا تستبدلي app.py الخاص بالبنت المسؤولة عن الدمج بدون مراجعتها**. يمكنها دمج الاستيرادات والاستدعاء منه مع الكود الموجود حاليًا.
- **الاعتماديات:** `requirements.txt` الحالي يحتوي `folium` و`streamlit-folium` و`streamlit`، لا يلزم إضافة مكتبات جديدة.

## تشغيل المشروع من VS Code

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
streamlit run app.py
```

إذا كان `app.py` الأصلي لا يستدعي `render_map`، يجب دمج المثال أو إضافة استدعاء `render_map(areas, selected_area_id)` إليه. إذا كان `load_datasets` يرفع خطأ عند غياب CSV، ضعي الاستدعاء داخل try/except قبل رسم الخريطة، ليظل عرض المواقع يعمل دون بيانات NASA.

## تجربة الخريطة بشكل مستقل دون تغيير app.py

```powershell
streamlit run tests/map_preview.py
```

هذا يعرض علامتي تل السلطان والعوجا (نقطتين جغرافيتين مرجعيتين) حتى عندما يكون `data/study_areas.geojson` غير موجود. إذا وُجد، سيظهر المضلع وفقًا لإحداثيات الملف **دون تعديله**. لا يُعتَبر وجود المضلع إثباتًا أنه رسمي أو موثق.

## المزايا

- تكبير وتصغير بالماوس وأزرار +/−
- 3 خرائط أساسية (OpenStreetMap، CartoDB Light، Esri satellite)
- أزرار Fullscreen وقياس المسافة/المساحة
- MiniMap، إحداثيات الماوس، النقر لمعرفة الإحداثيات
- علامات تل السلطان والعوجا، وروابط مراجع مواقعهما
- إظهار/إخفاء المضلعات الحقيقية عند توفر GeoJSON
- تحديد المنطقة الرئيسية من `app.py` كما في عقد المشروع، والتنقل للمنطقة من داخل الخريطة بصريًا فقط
- لا تعرض NDVI أو Rainfall بدون ملفات NASA الحقيقية والمتحقق منها

## التوثيق العلمي

مواقع العلامات مرجعية: Tell es-Sultan (UNESCO: https://whc.unesco.org/en/list/1687) وAl-Auja (GeoNames: https://www.geonames.org/285112/al-awja.html). **هذه ليست حدودًا إدارية أو زراعية.** يجب اعتماد نفس مضلعات `data/study_areas.geojson` في حساب بيانات NASA وفي عرض الخريطة، وتوثيق المصدر في `metadata.json`. لا تستخدم نقاط العلامات كنوافذ استخراج NDVI أو GPM من تلقاء نفسها.

## أمر رفع GitHub

نفّذي فقط على فرع `feature/ui` بعد مراجعة التعديلات:

```powershell
git status
git branch --show-current
git add modules/map_view.py tests/test_map_view.py tests/map_preview.py
git commit -m "Enhance interactive Jericho map UI"
git push -u origin feature/ui
```

## قيود

الخريطة تحتاج إنترنت لعرض صور خرائط OSM/Esri. إذا لم تظهر الخلفية، تأكدي من الشبكة أو سياسة مزود الخرائط. قياسات المساحات في أداة الواجهة ليست بديلًا عن حساب GIS موثق؛ لا تعرض بيانات صادرة من NASA دون المصدر والتحقق.
