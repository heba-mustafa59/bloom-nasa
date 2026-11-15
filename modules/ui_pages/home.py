
"""BLOOM — Premium full-screen Home Page."""

import streamlit as st

from modules.ui_components import (
    feature_card,
    section_title,
    data_label
)


def render(ctx, navigate):

    # =========================================
    # 01 — FULL SCREEN HERO
    # =========================================

    st.html("""
    <section class="bloom-landing">

        <div class="landing-grid" aria-hidden="true"></div>
        <div class="landing-orbit orbit-a" aria-hidden="true"></div>
        <div class="landing-orbit orbit-b" aria-hidden="true"></div>

        <div class="landing-top">
            <span>NASA EARTH OBSERVATION</span>
            <span>JORDAN VALLEY / PALESTINE</span>
        </div>

        <div class="landing-center">

            <div class="landing-kicker">
                EXPLORING THE UNSEEN STORY OF VEGETATION
            </div>

            <h1>
                <span class="landing-word">
                    BLOOM<span class="landing-period">.</span>
                </span>
                <br>
                <em>Beyond the green.</em>
            </h1>

            <p>
                What does a greener landscape really tell us?
                <br>
                Follow twenty years of vegetation and rainfall evidence
                <br class="desktop-only">
                and discover the questions hidden beneath the surface.
            </p>

        </div>

        <div class="landing-bottom">

            <span>
                JERICHO, PALESTINE
                <span class="landing-separator">/</span>
                2005—2024
            </span>

            <a href="#bloom-discover" class="landing-scroll">
                SCROLL TO DISCOVER
                <span>↓</span>
            </a>

            <span>AN EARTH INTELLIGENCE PROJECT</span>

        </div>

    </section>
    """)

    # =========================================
    # 02 — SCROLL DESTINATION
    # =========================================

    st.html('<div id="bloom-discover"></div>')

    data_label(ctx)

    # =========================================
    # 02B — LIVE NASA CSV DISCOVERY CASE
    # =========================================
    # The landing case is derived from the original uploaded observations,
    # never hard-coded or populated with synthetic demo values.
    if ctx.ready and not ctx.is_demo:
        from modules.discovery_time_machine import discovery
        from modules.investigation_case import AREA_NAMES, CaseData

        case = CaseData(ctx.ndvi_df, ctx.rainfall_df, ctx.geojson, ctx.metadata)
        story = discovery(case)
        a, b = story.changes["area_a"], story.changes["area_b"]
        if story.switched_leader:
            headline = "The greener area changed."
            detail = (
                f"In {story.initial_year}, {AREA_NAMES[story.first_leader]} had the higher "
                f"annual NDVI. By {story.final_year}, {AREA_NAMES[story.final_leader]} "
                "had the higher value. What changed between these two observations?"
            )
        else:
            headline = "Two landscapes. Different vegetation signals."
            detail = (
                "Compare the two original study polygons across twenty annual observations "
                "and explore the evidence behind the differences."
            )

        st.markdown(
            """
            <style>
              .bloom-discovery {
                background:linear-gradient(115deg,#183322,#30543a 75%,#516c43);
                color:#f6f8ee; border:1px solid #6c875c;
                border-radius:22px; padding:28px 32px; margin:24px 0;
                box-shadow:0 14px 35px rgba(16,47,32,.13)
              }
              .bloom-discovery .eyebrow {
                color:#c5d79f; font-size:11px; letter-spacing:.2em;
                font-weight:700; margin-bottom:14px
              }
              .bloom-discovery h2 {color:white;margin:0 0 12px;font-size:clamp(26px,3vw,39px)}
              .bloom-discovery p {color:#e3eddf;max-width:850px;line-height:1.75}
              .discovery-data {display:flex;flex-wrap:wrap;gap:14px;margin-top:22px}
              .discovery-data .fact {
                flex:1 1 230px;background:rgba(255,255,255,.09);
                border:1px solid rgba(230,247,223,.16);
                padding:16px 19px;border-radius:14px
              }
              .discovery-data .fact span {font-size:12px;color:#d4e4ce}
              .discovery-data .fact strong {display:block;color:white;font-size:23px;margin:6px 0}
              .discovery-data .fact small {color:#d4e4ce;font-size:11px}
            </style>
            """,
            unsafe_allow_html=True,
        )
        from html import escape as escape_html

        st.markdown(
            f"""
            <section class="bloom-discovery">
              <div class="eyebrow">CASE 001 / REAL DATA DISCOVERY · JERICHO</div>
              <h2>{escape_html(headline)}</h2>
              <p>{escape_html(detail)}</p>
              <div class="discovery-data">
                <div class="fact">
                  <span>AREA A · NDVI {story.initial_year} → {story.final_year}</span>
                  <strong>{a.first_ndvi:.4f} → {a.selected_ndvi:.4f}</strong>
                  <small>Change {a.difference:+.4f} NDVI units</small>
                </div>
                <div class="fact">
                  <span>AREA B · NDVI {story.initial_year} → {story.final_year}</span>
                  <strong>{b.first_ndvi:.4f} → {b.selected_ndvi:.4f}</strong>
                  <small>Change {b.difference:+.4f} NDVI units</small>
                </div>
              </div>
            </section>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            "Based on uploaded annual polygon-mean NDVI values. "
            "Endpoint differences are not a significance test or an explanation of cause. "
            "Original export provenance review is still pending."
        )
        if st.button(
            "Investigate this discovery →",
            key="bloom_discovery_start",
            type="primary",
            use_container_width=True,
        ):
            # Show the first year initially; the Time Machine can then jump to 2024.
            st.session_state["bloom_explore_year"] = story.initial_year
            navigate("Explore")

    # =========================================
    # 02C — THE SOLUTION (VISIBLE BEFORE ANY GENERAL INTRO)
    # =========================================
    st.markdown(
        """
        <style>
        .bloom-solution-home{border:1px solid #d5e0cb;border-radius:20px;
          padding:28px 30px;margin:22px 0 20px;background:#f5f8f0}
        .bloom-solution-home .eyebrow{color:#66834f;font-size:12px;
          letter-spacing:.16em;font-weight:700}
        .bloom-solution-home h2{color:#1f3f2b;font-size:clamp(27px,3vw,38px);margin:9px 0}
        .bloom-solution-home p{color:#4a654f;line-height:1.8;max-width:840px}
        .bloom-solution-home .steps{display:flex;gap:8px;flex-wrap:wrap;margin-top:17px}
        .bloom-solution-home .steps span{border:1px solid #c5d7b9;border-radius:30px;
          color:#30563c;background:white;padding:9px 15px;font-size:13px;font-weight:600}
        </style>
        <section class="bloom-solution-home">
          <div class="eyebrow">THE SOLUTION / FROM SCIENCE TO ACTION</div>
          <h2>Don't just detect change. Know what to check next.</h2>
          <p>
            A satellite can show a vegetation signal, but cannot tell a farmer
            exactly why it happened. BLOOM connects twenty years of
            observations to an explainable area priority, a ground-truth
            checklist, conditional next steps and a plan to measure outcomes.
          </p>
          <div class="steps">
            <span>01 · DETECT</span><span>02 · VERIFY</span>
            <span>03 · ACT IF CONFIRMED</span><span>04 · MEASURE</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    if ctx.ready and not ctx.is_demo:
        if st.button(
            "Build an evidence-based action plan →",
            key="bloom_home_solution_start",
            type="primary",
        ):
            st.session_state["bloom_advisor_goal"] = "field_followup"
            navigate("Explore")

    # =========================================
    # 03 — INTRODUCTION
    # =========================================

    st.html("""
    <section class="bloom-editorial-intro">

        <div class="eyebrow">
            01 / THE QUESTION
        </div>

        <h2>
            Green doesn't always
            <br>
            mean <em>the same thing.</em>
        </h2>

        <p>
            Satellites can show where the landscape changes.
            BLOOM goes further — linking NASA vegetation
            observations with rainfall estimates and careful
            statistical testing, without mistaking correlation
            for cause.
        </p>

    </section>
    """)

    # =========================================
    # 04 — STUDY OVERVIEW
    # =========================================

    section_title(
        "THE STUDY",
        "A closer look at the landscape",
        "Three foundations. One transparent investigation."
    )

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        feature_card(
            "01 / OBSERVE",
            "Vegetation",
            "Quality-filtered MODIS NDVI observations reveal "
            "how vegetation changes across years."
        )

    with col2:
        feature_card(
            "02 / CONTEXT",
            "Rainfall",
            "GPM IMERG rainfall estimates provide a second "
            "signal to compare with vegetation change."
        )

    with col3:
        feature_card(
            "03 / QUESTION",
            "The unexpected",
            "A validated rainfall model can highlight unusual "
            "vegetation deviations for further study."
        )

    # =========================================
    # 05 — PROCESS SECTION
    # =========================================

    st.html("""
    <section class="bloom-chapter">

        <div class="chapter-index">
            02 / THE PROCESS
        </div>

        <div>
            <h2>
                From pixels
                <br>
                to perspective.
            </h2>

            <p>
                A guided research experience built
                to explain the evidence, not simply
                decorate it.
            </p>
        </div>

    </section>
    """)

    # =========================================
    # 06 — INVESTIGATION JOURNEY
    # =========================================

    section_title(
        "THE JOURNEY",
        "Follow the evidence",
        "Move between geography, trends, anomalies "
        "and scientific interpretation."
    )

    steps = [
        (
            "01",
            "Explore",
            "Find the documented study areas."
        ),
        (
            "02",
            "Analyze",
            "Measure long-term change and significance."
        ),
        (
            "03",
            "Investigate",
            "Check predictions and model limitations."
        ),
        (
            "04",
            "Explain",
            "Compare regions and communicate findings."
        ),
    ]

    columns = st.columns(4, gap="small")

    for col, (number, title, description) in zip(
        columns, steps
    ):
        with col:
            st.html(f"""
            <div class="bloom-step">
                <span>{number}</span>
                <h3>{title}</h3>
                <p>{description}</p>
            </div>
            """)

    # =========================================
    # 07 — FINAL CALL TO ACTION
    # =========================================

    st.html("""
    <section class="bloom-home-cta">

        <div class="eyebrow">
            READY TO INVESTIGATE?
        </div>

        <h2>
            Look closer.
            <br>
            <em>Ask better questions.</em>
        </h2>

        <p>
            Begin with the landscape,
            or jump straight into the science.
        </p>

    </section>
    """)

    left, middle, right = st.columns(
        [1, 1, 2],
        gap="small"
    )

    with left:
        if st.button(
            "Explore the map ↗",
            type="primary",
            use_container_width=True,
            key="home_explore"
        ):
            navigate("Explore")

    with middle:
        if st.button(
            "Open analytics ↗",
            use_container_width=True,
            key="home_analytics"
        ):
            navigate("Analytics")

    with right:
        st.caption(
            "BLOOM / Evidence before conclusions."
        )
