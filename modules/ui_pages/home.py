
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

        <div class="landing-top">
            <span>NASA EARTH OBSERVATION</span>
            <span>JORDAN VALLEY / PALESTINE</span>
        </div>

        <div class="landing-center">

            <div class="landing-kicker">
                A JERICHO EARTH OBSERVATION STUDY
            </div>

            <h1>
                <span class="landing-word">
                    BLOOM<span class="landing-period">.</span>
                </span>
                <br>
                <em>Beyond the green.</em>
            </h1>

            <p>
                Explore two study areas in Jericho, compare vegetation
                <br class="desktop-only">
                and rainfall records from 2005–2024, and understand
                <br class="desktop-only">
                what the available evidence can — and cannot — explain.
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
            BLOOM compares vegetation and rainfall across two
            study areas in Jericho. Our uploaded observations are
            available for exploration, while independent confirmation
            of their satellite export provenance is still pending.
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
