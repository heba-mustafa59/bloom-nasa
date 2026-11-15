
"""Explain BLOOM's methods and provenance without overstating what is known."""

import streamlit as st

from modules.ui_components import (
    feature_card,
    page_header,
    section_title
)


def render(ctx, navigate):
    page_header(
        "06 / OUR PURPOSE",
        "Science that knows its limits.",
        "BLOOM is a transparent, exploratory investigation "
        "of vegetation patterns in Jericho, Palestine."
    )

    # Use compact HTML with no Markdown-indented blank lines.
    # This avoids accidental code-block rendering in older Streamlit versions.
    st.markdown(
        '<div class="bloom-editorial-intro about-intro">'
        '<div class="eyebrow">A QUESTION WORTH ASKING</div>'
        '<h2>See the evidence.<br><em>Respect the uncertainty.</em></h2>'
        '<p>BLOOM combines Earth observation, rigorous trend tests and '
        'an exploratory model to ask where vegetation change may deserve '
        'deeper study. Satellite trends do not alone prove irrigation, '
        'human activity or any other cause.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    section_title(
        "01 / SOURCES",
        "Observations from space",
        "Specific Earth Engine products and their "
        "different spatial resolutions."
    )

    a, b, c = st.columns(
        3,
        gap="medium"
    )

    with a:
        feature_card(
            "01 / VEGETATION",
            "MODIS NDVI",
            "MOD13Q1 Version 6.1 · 16-day composites · "
            "250 m native spatial resolution; QA-filtered "
            "and scaled."
        )

    with b:
        feature_card(
            "02 / RAINFALL",
            "GPM IMERG",
            "Monthly V07 precipitation rates in mm/hour "
            "converted to annual totals with actual "
            "month lengths."
        )

    with c:
        feature_card(
            "03 / GEOGRAPHY",
            "Two study areas",
            "Verified polygons and provenance are essential "
            "before comparing two different land-use contexts."
        )

    section_title(
        "02 / METHODS",
        "The reasoning behind the results",
        "Four checks keep the research honest."
    )

    with st.expander(
        "01 / Linear trends and Mann–Kendall",
        expanded=True
    ):
        st.write(
            "Linear regression estimates change per year "
            "and decade; Mann–Kendall tests evidence for "
            "a monotonic trend. A non-significant p-value "
            "is not proof of stability."
        )

    with st.expander(
        "02 / Rainfall-based expected NDVI"
    ):
        st.write(
            "Chronological model training uses 2005–2018, "
            "with later years reserved for validation. "
            "A model must improve on the training-mean "
            "baseline before outliers can be considered "
            "exploratory flags."
        )

    with st.expander(
        "03 / Data quality"
    ):
        st.write(
            "Missing observations stay missing — never "
            "zero-filled. Metadata must document QA masks, "
            "polygon boundaries, scaling, conversion, "
            "source identifiers and data quality checks."
        )

    with st.expander(
        "04 / Limitations"
    ):
        st.write(
            "Mixed pixels, sensor uncertainty, spatial "
            "scale mismatch, missing data, possible "
            "temporal autocorrelation and unmeasured "
            "environmental drivers affect interpretation. "
            "Correlation cannot establish causation."
        )

    section_title(
        "03 / THE TEAM",
        "A connected research workflow",
        "Shared interfaces bring independent team "
        "contributions together."
    )

    st.markdown(
        "**Data & GIS** → **Statistics & Mystery** → "
        "**Interface & Mapping** → "
        "**Integration & Reporting**"
    )

    source_label = (
        "Synthetic demonstration" if ctx.is_demo
        else "Local CSV research preview · provenance pending"
        if ctx.mode == "local"
        else "Verified NASA mode (subject to loader checks)"
    )
    st.caption(f"Data status for your session: {source_label}")
