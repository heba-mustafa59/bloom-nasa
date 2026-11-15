"""Optional A-Frame evidence stations with accessible desktop controls.

The geometry is illustrative only; each displayed number is read from
validated annual records. For headset mode host the exported HTML on HTTPS;
embedded iframe XR permissions vary across browsers.
"""
from __future__ import annotations

import json
from .living_data import MissionData, AREAS


def scene_html(data: MissionData, area: str, selected_year: int) -> str:
    if area not in AREAS or selected_year not in range(2005, 2025):
        raise ValueError("Invalid area or observation year")
    by_year = {str(year): data.observation(area, year) for year in range(2005, 2025)}
    payload = json.dumps(by_year, ensure_ascii=True).replace("<", "\\u003c")
    body = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BLOOM / Illustrative 3D Evidence Stations</title>
<script src="https://aframe.io/releases/1.6.0/aframe.min.js"></script>
<style>
body{margin:0;background:#102B22;color:#F7F6EF;font:14px system-ui}
#panel{position:absolute;z-index:5;top:12px;left:12px;max-width:390px;
background:rgba(11,32,24,.96);padding:16px;border:1px solid #4C8B63;border-radius:12px}
#panel h2{font-size:16px;margin:0 0 10px}
#panel p{margin:5px 0;line-height:1.5}
#panel button,#panel select{background:#EDF1E8;color:#163D2E;border:0;border-radius:5px;
padding:7px;margin:3px;cursor:pointer}
#year{accent-color:#5FA273;width:95%}
#stations{display:flex;flex-wrap:wrap;gap:3px}
#detail{min-height:44px;max-width:340px}
#note{font-size:11px;color:#D8E4D8}
</style></head><body>
<div id="panel" role="region" aria-label="Evidence station controls">
  <h2>BLOOM / Living Earth 3D</h2>
  <p>Illustrative landscape — NOT a satellite image or accurate digital twin.</p>
  <label for="year">Observation year: <strong id="yr"></strong></label>
  <input type="range" min="2005" max="2024" step="1" id="year">
  <div id="stations"></div>
  <p id="detail" aria-live="polite"></p>
  <p id="note">Mouse drag + WASD for desktop. Click a station or use the buttons.
  VR is available only on supported HTTPS browser/headset configurations.</p>
</div>
<a-scene background="color:#C9DDCE" renderer="antialias:true" vr-mode-ui="enabled:true">
<a-entity camera look-controls wasd-controls position="0 1.65 7">
 <a-entity cursor="rayOrigin: mouse" raycaster="objects: .station"></a-entity>
</a-entity>
<a-plane rotation="-90 0 0" width="24" height="24" color="#B8CFB3"></a-plane>
<a-sky color="#C9DDCE"></a-sky>
<a-cylinder position="0 .07 -3" radius="4.4" height=".14" color="#204F38"></a-cylinder>
<a-entity id="trees">
<a-cylinder position="-3 .5 -3" radius=".12" height="1" color="#6D5840"></a-cylinder>
<a-cone position="-3 1.35 -3" radius-bottom=".63" radius-top="0" height="1.6" color="#4C8B63"></a-cone>
<a-cylinder position="3 .5 -3" radius=".12" height="1" color="#6D5840"></a-cylinder>
<a-cone position="3 1.35 -3" radius-bottom=".55" radius-top="0" height="1.6" color="#4C8B63"></a-cone>
</a-entity>
<a-box class="station" data-station="ndvi" position="-3 .7 -1" width="1.2" height="1" depth=".25" color="#4C8B63"></a-box>
<a-box class="station" data-station="gpm" position="0 .7 -1.5" width="1.2" height="1" depth=".25" color="#62AFC8"></a-box>
<a-box class="station" data-station="power" position="3 .7 -1" width="1.2" height="1" depth=".25" color="#D99A56"></a-box>
<a-box class="station" data-station="uncertainty" position="-2 .7 -5" width="1.2" height="1" depth=".25" color="#718A7D"></a-box>
<a-box class="station" data-station="decision" position="2 .7 -5" width="1.2" height="1" depth=".25" color="#163D2E"></a-box>
<a-text value="Vegetation" position="-3.8 1.5 -1" width="2.5" color="#102B22"></a-text>
<a-text value="GPM rainfall" position="-.8 1.5 -1.5" width="2.5" color="#102B22"></a-text>
<a-text value="POWER point" position="2.2 1.5 -1" width="2.5" color="#102B22"></a-text>
<a-text value="Uncertainty" position="-2.8 1.5 -5" width="2.5" color="#FFFFFF"></a-text>
<a-text value="Decision Room" position="1.2 1.5 -5" width="2.5" color="#FFFFFF"></a-text>
<a-light type="ambient" intensity=".75"></a-light>
<a-light type="directional" position="2 6 3" intensity=".6"></a-light>
</a-scene>
<script>
const DATA = __BLOOM_DATA__;
const start = __BLOOM_YEAR__;
const select = document.getElementById("year");
select.value=String(start);
const labels = {
ndvi:"Vegetation History",gpm:"GPM Polygon Rainfall",power:"NASA POWER Point Reference",
uncertainty:"Scientific Uncertainty",decision:"Decision Laboratory"};
let active="ndvi";
function show(which){
  active=which;
  const o=DATA[select.value];
  const desc={
    ndvi:"Measured annual polygon NDVI: "+o.ndvi.toFixed(4)+
      " | "+o.ndvi_valid_observations+" valid MODIS composites.",
    gpm:"Estimated annual GPM polygon rainfall: "+o.gpm_rainfall_mm.toFixed(1)+
      " mm | "+o.gpm_valid_months+" complete months. Coarse spatial pixels.",
    power:"NASA POWER point rainfall reference: "+o.power_point_rainfall_mm.toFixed(1)+
      " mm. This is NOT a polygon precipitation observation.",
    uncertainty:"NDVI is an annual polygon average. Irrigation, temperature, crop history and "+
      "plant locations are not measured in the supplied data. Source verification: "+o.verification_status+".",
    decision:"Choose a real-world next step in BLOOM's non-VR Decision Room. This scene "+
      "does not claim an intervention is effective."
  };
  document.getElementById("yr").textContent=select.value;
  document.getElementById("detail").textContent=labels[which]+": "+desc[which];
}
Object.entries(labels).forEach(([id,label])=>{
 const b=document.createElement("button");
 b.textContent=label;b.type="button";b.addEventListener("click",()=>show(id));
 document.getElementById("stations").appendChild(b);
});
select.addEventListener("input",()=>show(active));
document.querySelectorAll(".station").forEach(el=>el.addEventListener("click",()=>show(el.dataset.station)));
show("ndvi");
</script></body></html>"""
    return body.replace("__BLOOM_DATA__", payload).replace("__BLOOM_YEAR__", str(selected_year))
