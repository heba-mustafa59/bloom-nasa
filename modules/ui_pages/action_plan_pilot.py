"""Reusable BLOOM Solution Pathway UI — Explore now, optionally reports later.

The original measurements remain read-only. Ground observations and checkboxes
are user-entered notes, never presented as independently verified evidence.
"""
from __future__ import annotations

import streamlit as st

from modules.action_planner import FIELD_SIGNALS, action_plan_markdown, build_action_plan
from modules.investigation_case import AREA_NAMES, CaseData
from modules.ui_components import section_title


def render_action_pathway(data: CaseData, recommendation, selected_area_id: str):
    """Show an actionable, cautious evidence-to-verification pathway.

    Returns the plan + Markdown for inclusion in the combined report.
    """
    section_title(
        "05 / THE SOLUTION",
        "From a satellite signal to a real decision.",
        "BLOOM doesn't stop at spotting a difference. It shows what to verify "
        "on the ground, which responses to consider, and how to monitor results.",
    )

    st.markdown(
        """
        <style>
        .bloom-solution-flow {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));
          gap:12px;margin:8px 0 20px}
        .bloom-solution-step {border:1px solid #dde9da;background:#f6f9f3;
          border-radius:14px;padding:15px 13px;min-height:110px}
        .bloom-solution-step .num {color:#608f63;font-size:11px;font-weight:700;
          letter-spacing:.1em}
        .bloom-solution-step h4 {color:#1f3f2b;margin:10px 0 5px;font-size:17px}
        .bloom-solution-step p {color:#56705e;font-size:12px;line-height:1.5;margin:0}
        @media(max-width:850px){.bloom-solution-flow{grid-template-columns:repeat(2,minmax(0,1fr))}}
        </style>
        <div class="bloom-solution-flow">
          <div class="bloom-solution-step"><span class="num">01 / DETECT</span>
            <h4>Find the signal</h4><p>Read the observed NDVI and rainfall for the study polygon.</p></div>
          <div class="bloom-solution-step"><span class="num">02 / VERIFY</span>
            <h4>Ask what happened</h4><p>Check land use, crop timing, water access and field photos.</p></div>
          <div class="bloom-solution-step"><span class="num">03 / ACT</span>
            <h4>Respond responsibly</h4><p>Consider a local intervention only if its underlying cause is confirmed.</p></div>
          <div class="bloom-solution-step"><span class="num">04 / MEASURE</span>
            <h4>Track outcomes</h4><p>Record new comparable observations, not predicted success.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    default_area = recommendation.winner or selected_area_id
    a, b = st.columns([1, 1.2], gap="medium")
    with a:
        target_area = st.selectbox(
            "Which study area are we investigating?",
            list(AREA_NAMES),
            index=list(AREA_NAMES).index(default_area),
            format_func=AREA_NAMES.get,
            key=f"bloom_action_area_{recommendation.goal}_{recommendation.year}_{selected_area_id}",
        )
    with b:
        signal = st.selectbox(
            "Field observation (unverified)",
            list(FIELD_SIGNALS),
            format_func=FIELD_SIGNALS.get,
            key=f"bloom_action_clue_{recommendation.goal}_{recommendation.year}_{target_area}",
        )

    plan = build_action_plan(data, recommendation, target_area, signal)
    st.markdown(
        f"**Investigation focus: {AREA_NAMES[target_area]}** · "
        f"NDVI {plan.ndvi:.4f} ({plan.year}) · "
        f"Rainfall {plan.rainfall_mm:.1f} mm · "
        f"NDVI difference vs 2005 {plan.measured_change:+.4f}"
    )
    st.caption(
        "This is a decision-support plan for two existing study polygons, "
        "not a claim of land degradation, crop suitability or a proven environmental cause."
    )

    left, right = st.columns([1.1, 1], gap="large")
    with left:
        st.markdown("#### 02 / Verification checklist")
        st.caption("Ticking tasks records a user checklist only. It does not authenticate any field finding.")
        checked = []
        for i, check in enumerate(plan.ground_checks):
            if st.checkbox(
                check,
                value=False,
                key=f"bloom_field_check_{target_area}_{recommendation.goal}_{recommendation.year}_{signal}_{i}",
            ):
                checked.append(check)
        st.caption(f"Checklist progress: {len(checked)} / {len(plan.ground_checks)} user-marked tasks")
    with right:
        st.markdown("#### 03 / Conditional next step")
        if signal == "not_checked":
            st.info(plan.conditional_action)
        else:
            st.warning(plan.conditional_action)
        st.markdown("#### 04 / How would we measure impact?")
        for task in plan.monitoring:
            st.write("• " + task)

    with st.expander("Evidence trace and what BLOOM cannot conclude"):
        for line in plan.evidence:
            st.write("• " + line)
        st.write("**Limit:** " + plan.interpretation)
        st.caption(
            "Original NASA CSV values are unchanged. "
            "The extraction provenance is pending review where indicated in metadata."
        )

    report = action_plan_markdown(data, plan, tuple(checked))
    st.download_button(
        "Download field action plan",
        data=report.encode("utf-8"),
        file_name=f"BLOOM_action_plan_{target_area}_{recommendation.goal}_{plan.year}.md",
        mime="text/markdown",
        type="primary",
        key="bloom_action_download",
    )
    return plan, report
