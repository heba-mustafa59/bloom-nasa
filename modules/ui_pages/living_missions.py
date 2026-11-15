"""BLOOM Living Earth Missions — integrated research investigation page.

Reuse render(ctx, navigate), shared BLOOM styles and real annual CSV data.
No scientifically unsupported alert, forecast or digital-twin claim.
"""
from __future__ import annotations

from datetime import date
import hmac
import os

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from modules.ui_components import page_header, section_title, style_figure
from modules.living_data import load_mission_data
from modules.living_missions import (
    ACTIONS, HYPOTHESES, mission_catalog, new_case, record_case_step,
    endpoint_change, evidence_cards, trends, impact_passport,
)
from modules.living_ai import connected_key, interrogate
from modules.living_groundtruth import (
    CATEGORIES, impact_metrics, list_pending, local_submissions_enabled,
    record_activity, report_status, review_report, submit_report,
)
from modules.living_webxr import scene_html


@st.cache_data(ttl=300, show_spinner=False)
def _data():
    return load_mission_data()


def _selected_polygon_map(data, area):
    features = [feature for feature in data.geojson["features"]
                if feature["properties"]["area_id"] == area]
    ring = features[0]["geometry"]["coordinates"][0]
    lat = sum(p[1] for p in ring[:-1]) / (len(ring) - 1)
    lon = sum(p[0] for p in ring[:-1]) / (len(ring) - 1)
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="OpenStreetMap",
                   control_scale=True)
    folium.GeoJson({"type": "FeatureCollection", "features": features},
                   name=f"Study area {area}", style_function=lambda _: {
                       "color": "#4C8B63", "weight": 4,
                       "fillColor": "#4C8B63", "fillOpacity": 0.18,
                   }).add_to(m)
    m.fit_bounds([[min(p[1] for p in ring), min(p[0] for p in ring)],
                  [max(p[1] for p in ring), max(p[0] for p in ring)]])
    st_folium(m, height=360, use_container_width=True, returned_objects=[],
              key=f"mission_map_{area}")


def _activity(case):
    try:
        record_activity(case["case_id"], "INVESTIGATION_COMPLETED", case["mission_id"])
    except OSError:
        st.warning("Private activity storage unavailable; report download still works.")


def _active_case():
    return st.session_state.get("living_case")


def _change(item, value):
    st.session_state["living_case"] = record_case_step(_active_case(), item, value)


def render(ctx, navigate):
    page_header(
        "05 / LIVING EARTH MISSIONS",
        "From evidence to action.",
        "Discover → Investigate → Question → Decide → Verify. "
        "No fictitious emergencies, measurements or environmental impact."
    )
    if ctx.mode == "demo":
        st.info("Switch DATA SOURCE to Local CSV — research preview to investigate real annual exports. Demo observations cannot support research missions.")
        return
    try:
        data = _data()
    except (ValueError, FileNotFoundError, OSError, KeyError, TypeError) as exc:
        st.error("Mission datasets could not pass validation. No substituted data will be displayed.")
        with st.expander("Validation details"):
            st.code(str(exc))
        return

    if data.verification != "verified":
        st.warning("RESEARCH PREVIEW — dataset verification is pending. CSV values are actual local exports, but independent scientific provenance checks are incomplete.")
    else:
        st.info("Dataset marked verified in metadata; review source methods before drawing conclusions.")

    mission_list = mission_catalog(data)
    st.caption("Based on actual annual polygon records (2005–2024). Endpoint changes are not proven causes or continuous trends.")

    case = _active_case()
    if case is None:
        section_title("MISSION CONTROL", "Choose your investigation",
                      "Each mission is derived from measured endpoint differences.")
        cols = st.columns(3, gap="medium")
        for col, item in zip(cols, mission_list):
            with col:
                with st.container(border=True):
                    st.caption(item["id"].upper())
                    st.subheader(item["title"])
                    st.metric("Endpoint NDVI difference", f"{item['change']:+.4f}")
                    st.caption(item["question"])
                    if st.button("Start investigation", key=f"start_{item['id']}",
                                 type="primary", use_container_width=True):
                        st.session_state["living_case"] = new_case(
                            item["id"], item["area"], (2005, 2024))
                        st.rerun()
        st.info("Mission labels refer to endpoint differences; an Area B decline is not assumed statistically significant.")
        return

    with st.container(border=True):
        heading = next((m for m in mission_list if m["id"] == case["mission_id"]), None)
        st.markdown(f"### {heading['title'] if heading else 'Living Earth Investigation'}")
        st.caption(f"Case ID: {case['case_id']}  |  Active polygon: {case['area'].upper()}  |  Period: {case['years'][0]}–{case['years'][1]}")
        completed = sum([len(case["evidence"]) >= 2, case["hypothesis"] is not None,
                         case["decision"] is not None, case["field_report_id"] is not None])
        st.progress(completed / 4, text=f"Investigation milestones: {completed}/4 (field observations are optional)")
        if st.button("Back to Mission Control / new case", key="close_mission"):
            st.session_state.pop("living_case", None)
            st.rerun()

    period = st.slider("Observation period (resets investigation when changed)",
                       min_value=2005, max_value=2024,
                       value=tuple(case["years"]), key="mission_period")
    if tuple(case["years"]) != period:
        st.warning("Changing years starts a new investigation so earlier evidence cannot silently carry over.")
        if st.button("Start new case with selected period", key="mission_reset_years"):
            st.session_state["living_case"] = new_case(
                case["mission_id"], case["area"], period)
            st.rerun()
    area, year_a, year_b = case["area"], *case["years"]
    change = endpoint_change(data, area, year_a, year_b)
    observation_year = st.select_slider("Examine observation year",
                                       options=list(range(year_a, year_b + 1)),
                                       value=year_b, key="mission_observation_year")
    obs = data.observation(area, observation_year)

    t_explore, t_evidence, t_ai, t_decide, t_truth, t_report, t_impact = st.tabs([
        "01 / Explore", "02 / Evidence Lab", "03 / AI Investigator",
        "04 / Decision Room", "05 / Ground Truth", "06 / Impact Passport",
        "07 / Impact Tracking"
    ])

    with t_explore:
        section_title("01 / ENTER THE EVIDENCE", "One study polygon, many observations",
                      "The polygon is geographic evidence. The 3D environment is illustrative.")
        c1, c2, c3 = st.columns(3)
        c1.metric(f"NDVI · {observation_year}", f"{obs['ndvi']:.4f}")
        c2.metric(f"GPM polygon rainfall · {observation_year}", f"{obs['gpm_rainfall_mm']:.1f} mm")
        c3.metric("NDVI endpoint change", f"{change['ndvi_delta']:+.4f}")
        _selected_polygon_map(data, area)
        st.caption("GeoJSON boundaries: data/study_areas.geojson, WGS84 lon/lat. Map polygons are real boundaries; validation of their provenance is pending.")
        st.markdown("#### Interactive 3D Evidence Stations / WebXR")
        st.caption("This is NOT reconstructed vegetation or a pixel-accurate landscape. Scientific numbers are passed from validated observations.")
        html = scene_html(data, area, observation_year)
        st.components.v1.html(html, height=520, scrolling=False)
        st.download_button("Export standalone 3D / WebXR scene (HTML)", html,
                           file_name=f"bloom_{area}_living_scene.html", mime="text/html",
                           key="mission_webxr_download")
        st.caption("Desktop mouse/WASD works when A-Frame CDN is reachable. For headset XR host the standalone HTML on HTTPS; embedded iframe permissions may block VR.")

    with t_evidence:
        section_title("02 / GATHER EVIDENCE", "Evidence before explanation",
                      "Collect source-attributed cards; do not conflate a point with a polygon.")
        frame_ndvi = data.ndvi.loc[(data.ndvi.area_id == area)
                                   & data.ndvi.year.between(year_a, year_b)]
        frame_rain = data.rainfall.loc[(data.rainfall.area_id == area)
                                       & data.rainfall.year.between(year_a, year_b)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=frame_ndvi.year, y=frame_ndvi.ndvi,
                                 name="MODIS NDVI", mode="lines+markers",
                                 line=dict(color="#4C8B63", width=3)))
        style_figure(fig, "Annual NDVI / unitless")
        st.plotly_chart(fig, use_container_width=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=frame_rain.year, y=frame_rain.rainfall_mm,
                              name="GPM polygon", marker_color="#62AFC8"))
        style_figure(fig2, "Annual precipitation, mm")
        st.plotly_chart(fig2, use_container_width=True)
        for card in evidence_cards(data, area, year_a, year_b):
            with st.container(border=True):
                st.caption(card["label"])
                st.markdown(f"**{card['value']}**")
                st.write(card["detail"])
                st.caption(f"Source: {card['source']}")
                st.caption(f"Quality: {card['quality']}")
                already = card["id"] in case["evidence"]
                if st.button("Collected ✓" if already else "Collect evidence",
                             key=f"collect_{card['id']}", disabled=already):
                    _change("evidence", card["id"])
                    st.rerun()
        st.caption(f"Collected {len(case['evidence'])}/5 evidence items. Missing temperature data: UNAVAILABLE.")

    with t_ai:
        section_title("03 / CHALLENGE THE AI", "Question the explanation",
                      "Deterministic scientific facts first, then optional restricted model critique.")
        choice = st.selectbox("Working hypothesis", list(HYPOTHESES),
                              format_func=HYPOTHESES.get,
                              index=list(HYPOTHESES).index(case["hypothesis"]) if case["hypothesis"] else 0)
        if st.button("Investigate hypothesis", type="primary", key="challenge_hypothesis"):
            _change("hypothesis", choice)
            st.rerun()
        selected = case["hypothesis"] or choice
        explanation = interrogate(data, area, selected, (year_a, year_b), key=None)
        st.caption(f"Engine: {explanation['engine']}")
        for key, heading_label in [
            ("observed", "OBSERVED"), ("supported_by", "EVIDENCE / SOURCE"),
            ("plausible", "HYPOTHESIS"), ("counter_evidence", "COUNTER-EVIDENCE"),
            ("unknown", "UNKNOWN"), ("next_data", "WHAT TO MEASURE"),
            ("next_action", "NEXT JUSTIFIED STEP"),
        ]:
            with st.container(border=True):
                st.caption(heading_label)
                st.write(explanation[key])
        st.caption(explanation["source"])
        if connected_key():
            consent = st.checkbox("I consent to send aggregated annual observations and the selected hypothesis to the configured AI provider. No private field reports or photos are transmitted.", key="living_llm_consent")
            if st.button("Ask connected AI for a critical reading", disabled=not consent,
                         key="living_llm_button"):
                answer = interrogate(data, area, selected, (year_a, year_b))
                if answer["llm_status"] == "connected":
                    st.success("Connected model critique — speculative discussion, not scientific proof")
                    for key, val in answer["llm_notes"].items():
                        st.write(f"**{key.replace('_', ' ').title()}:** {val}")
                else:
                    st.warning("Remote model unavailable or output invalid; deterministic evidence remains authoritative.")
        else:
            st.info("No AI API key configured. This is a deterministic evidence interpreter, not a connected language model.")

    with t_decide:
        section_title("04 / DECISION ROOM", "Choose what to verify next",
                      "These are information-gathering actions, not prescribed farm interventions.")
        action = st.selectbox("Proposed next action", list(ACTIONS),
                              format_func=lambda k: ACTIONS[k]["name"],
                              index=list(ACTIONS).index(case["decision"]) if case["decision"] else 0)
        details = ACTIONS[action]
        for name, field in [("Purpose", "purpose"), ("Information required", "needs"),
                            ("Expected benefit", "benefit"), ("Limitations", "limits"),
                            ("Practical risks", "risk")]:
            st.write(f"**{name}:** {details[field]}")
        st.warning("What-if exercises are educational only. No validated forecast of water savings, NDVI recovery or intervention effectiveness exists.")
        if st.button("Record proposed action", key="living_record_action", type="primary"):
            _change("decision", action)
            record_activity(case["case_id"], "ACTION_RECORDED", action)
            st.success("Proposed evidence-gathering action recorded. No environmental outcome is claimed.")
        st.caption("No numerical priority ranking is asserted without a documented prioritization method.")

    with t_truth:
        section_title("05 / GROUND TRUTH", "Space observations meet field evidence",
                      "Reports are private, unverified until reviewed, and optional.")
        if not local_submissions_enabled():
            st.warning("Field submissions are disabled by default. Set BLOOM_ENABLE_LOCAL_SUBMISSIONS=1 only on a controlled local deployment with persistent private storage.")
        elif case["field_report_id"]:
            current = report_status(case["field_report_id"])
            st.info(f"Existing field report status: {current}. Submitted observations are not verified automatically.")
        else:
            with st.form("ground_truth_report"):
                when = st.date_input("Field observation date", value=date.today(),
                                     min_value=date(2000, 1, 1), max_value=date.today())
                cat = st.selectbox("Observation category", sorted(CATEGORIES))
                desc = st.text_area("What did you actually observe? (10–2000 characters)", max_chars=2000)
                source = st.text_input("Source of this observation (optional)", max_chars=300)
                img = st.file_uploader("Optional photo (JPEG/PNG, max 2 MB; metadata stripped)",
                                       type=["jpg", "jpeg", "png"])
                location = st.checkbox("I choose to provide approximate coordinates (rounded to ~1 km)")
                lat = lon = None
                location_ok = False
                if location:
                    lat = st.number_input("Approx. latitude", 31.6, 32.2, 31.85, step=0.01)
                    lon = st.number_input("Approx. longitude", 35.2, 35.75, 35.46, step=0.01)
                    location_ok = st.checkbox("I consent to storing approximate location privately.")
                consent = st.checkbox("I consent to storing this report privately for moderation. It will not be published or treated as verified until reviewed.")
                submit = st.form_submit_button("Submit for review", type="primary")
            if submit:
                try:
                    report_id = submit_report(
                        case_id=case["case_id"], area=area,
                        observed_date=when.isoformat(), category=cat,
                        description=desc, source_note=source, consent=consent,
                        approx_location=(lat, lon) if location else None,
                        location_consent=location_ok,
                        photo=img.getvalue() if img is not None else None,
                        photo_filename=img.name if img is not None else "")
                except (ValueError, OSError) as exc:
                    st.error(str(exc))
                else:
                    _change("field_report_id", report_id)
                    _change("field_status", "PENDING")
                    st.success("Report submitted privately with PENDING status.")
                    st.rerun()
        reviewer_token = os.environ.get("BLOOM_REVIEWER_TOKEN")
        if reviewer_token and local_submissions_enabled():
            with st.expander("Authorized field review"):
                supplied = st.text_input("Reviewer access token", type="password",
                                         key="living_reviewer_token")
                if supplied and hmac.compare_digest(supplied, reviewer_token):
                    pending = list_pending()
                    st.caption(f"Pending reports: {len(pending)}")
                    for entry in pending:
                        with st.container(border=True):
                            st.write(f"{entry['id']} | {entry['area']} | {entry['category']}")
                            st.write(entry["description"])
                            st.caption(entry["source_note"])
                            left, right = st.columns(2)
                            if left.button("Verify", key=f"v_{entry['id']}"):
                                review_report(entry["id"], "VERIFIED")
                                st.rerun()
                            if right.button("Reject", key=f"x_{entry['id']}"):
                                review_report(entry["id"], "REJECTED")
                                st.rerun()
                elif supplied:
                    st.error("Reviewer authorization not granted.")

    with t_report:
        section_title("06 / EVIDENCE-TO-ACTION", "Your Impact Passport",
                      "Every row is derived from this case and the current datasets.")
        for step in case["trail"]:
            st.write(f"**{step['type']}:** {step['label']}")
        html_report = impact_passport(case, data)
        st.download_button("Download Impact Passport (HTML)",
                           data=html_report, file_name=f"bloom_passport_{case['case_id']}.html",
                           mime="text/html", key="living_passport_download",
                           on_click=lambda: _activity(case))
        st.caption("A completed report is an investigation record, not a verified environmental improvement.")
        if case["field_report_id"]:
            st.info(f"Ground verification record: {report_status(case['field_report_id'])}")
        else:
            st.info("Ground verification: NOT SUBMITTED")

    with t_impact:
        section_title("07 / IMPACT TRACKING", "Measure the work, not imagined outcomes",
                      "Operational counts come from private persistent records on this deployment.")
        metrics = impact_metrics()
        items = [
            ("Completed investigations", metrics["investigations_completed"]),
            ("Actions recorded", metrics["actions_recorded"]),
            ("Field reports submitted", metrics["field_submissions"]),
            ("Reports verified", metrics["field_verified"]),
            ("Reports awaiting review", metrics["field_pending"]),
            ("Cases re-evaluated", metrics["cases_reevaluated"]),
        ]
        for row_start in (0, 3):
            cols = st.columns(3)
            for col, (label, value) in zip(cols, items[row_start:row_start + 3]):
                col.metric(label, value)
        st.warning(metrics["verified_environmental_impact"])
        st.caption("Storage is SQLite local to this deployment; public/ephemeral hosting needs an authenticated persistent service.")
