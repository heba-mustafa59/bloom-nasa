"""BLOOM homepage: a clear research journey with a data-driven hero.

Uses the same UIContext as the rest of the app; never invents observations.
"""
from html import escape

import plotly.graph_objects as go
import streamlit as st

from modules.ui_components import data_label, number, section_title
from modules.ui_data import AREA_LABELS

ROUTES = [
    ("01", "Explore", "Explore the map", "Locate the two study polygons and inspect the study geography.", "Open map"),
    ("02", "Analytics", "Analyze the trends", "Examine vegetation and rainfall changes across the years.", "View trends"),
    ("03", "Compare", "Compare the areas", "See both regions on the same axes with the same time window.", "Compare areas"),
    ("04", "Reports", "Take the evidence", "Review an evidence brief and download the available results.", "View reports"),
]


def _preview_chart(ctx):
    """Show uploaded (or explicitly demo) data for the selected study area."""
    data = ctx.area_data("ndvi")
    if data.empty:
        st.info("No observations available for this selection.")
        return

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data["year"],
            y=data["ndvi"],
            name="NDVI",
            mode="lines+markers",
            line=dict(color="#C5E39A", width=3, shape="spline", smoothing=0.25),
            marker=dict(color="#F1F8E4", size=6, line=dict(color="#7FA65B", width=1)),
            fill="tozeroy",
            fillcolor="rgba(163,205,114,0.10)",
            hovertemplate="Year %{x}<br>NDVI %{y:.4f}<extra></extra>",
        )
    )
    fig.update_layout(
        height=242,
        margin=dict(l=5, r=8, t=12, b=5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font=dict(family="DM Sans, Arial", color="#DBE9D9", size=11),
        xaxis=dict(title=None, showgrid=False, tickformat="d", tickfont=dict(color="#A8C3AC")),
        yaxis=dict(title=None, gridcolor="rgba(203,229,209,.13)", zeroline=False, tickfont=dict(color="#A8C3AC")),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render(ctx, navigate):
    # The first screen identifies the study and has actions that really navigate.
    with st.container(key="bloom_hero"):
        left, right = st.columns([1.15, .85], gap="large")
        with left:
            st.html(
                """
                <div class="bloom-hero-copy">
                    <div class="bloom-hero-kicker">
                        <span class="bloom-kicker-dot"></span>
                        EARTH OBSERVATION / JERICHO
                    </div>
                    <h1>BLOOM<span>.</span></h1>
                    <h2>Beyond the green.</h2>
                    <p>
                        Explore twenty years of vegetation and rainfall
                        records. Compare two study areas, investigate
                        trends, and see what the evidence can really tell us.
                    </p>
                    <div class="bloom-hero-meta">
                        <span>31° N / JERICHO</span>
                        <span>2005—2024</span>
                        <span>02 STUDY AREAS</span>
                    </div>
                </div>
                """
            )
            start, trends = st.columns([1.1, 1], gap="small")
            with start:
                if st.button(
                    "Explore the map →",
                    type="primary",
                    use_container_width=True,
                    key="home_hero_explore",
                ):
                    navigate("Explore")
            with trends:
                if st.button(
                    "View analysis ↗",
                    use_container_width=True,
                    key="home_hero_analytics",
                ):
                    navigate("Analytics")

        with right:
            status = (
                "SYNTHETIC DEMO"
                if ctx.is_demo else
                "PROVENANCE PENDING"
                if ctx.is_provisional else
                "VERIFIED OBSERVATIONS"
            )
            st.html(
                '<div class="bloom-hero-panel-head">'
                '<span>STUDY SNAPSHOT / VEGETATION</span>'
                '<strong>' + escape(AREA_LABELS.get(ctx.area_id, "Study area")) + '</strong>'
                '<small>' + escape(status) + '</small>'
                '</div>'
            )
            _preview_chart(ctx)
            nd = ctx.area_data("ndvi")
            rain = ctx.area_data("rainfall_mm")
            nd_mean = number(nd["ndvi"].mean(), 3) if len(nd) else "N/A"
            rain_mean = number(rain["rainfall_mm"].mean(), 1, " mm") if len(rain) else "N/A"
            st.html(
                '<div class="bloom-hero-panel-metrics">'
                '<div><span>MEAN NDVI</span><strong>' + escape(nd_mean) + '</strong></div>'
                '<div><span>MEAN ANNUAL RAIN</span><strong>' + escape(rain_mean) + '</strong></div>'
                '</div>'
            )

    # Make the provenance caveat visible without obscuring the landing experience.
    data_label(ctx)

    section_title(
        "YOUR JOURNEY",
        "Find your way through the evidence.",
        "Four clear starting points — from the map to the report.",
    )

    columns = st.columns(4, gap="medium")
    for col, (index, route, title, detail, button_label) in zip(columns, ROUTES):
        with col:
            with st.container(key=f"bloom_route_{index}"):
                st.html(
                    '<div class="bloom-route-copy">'
                    '<span>' + index + ' / BLOOM</span>'
                    '<h3>' + escape(title) + '</h3>'
                    '<p>' + escape(detail) + '</p>'
                    '</div>'
                )
                if st.button(
                    button_label + " →",
                    use_container_width=True,
                    key=f"home_route_{index}",
                ):
                    navigate(route)

    st.html(
        """
        <section class="bloom-observation-story">
            <div>
                <span class="eyebrow">OUR RESEARCH QUESTION</span>
                <h2>Where is the land changing — and what do we actually know?</h2>
            </div>
            <p>
                Vegetation patterns tell one part of the story.
                Rainfall gives context. BLOOM puts them side by side,
                separates measured change from possible explanations,
                and makes uncertainty visible.
            </p>
        </section>
        """
    )

    section_title(
        "THE STUDY",
        "Built on environmental observations.",
        "Real methodology, explicit limits, and a path from research to action.",
    )
    a, b, c = st.columns(3, gap="medium")
    blocks = [
        ("VEGETATION / NDVI", "01", "Monitor vegetation", "Annual MODIS NDVI observations show changes in vegetation activity across the study period."),
        ("PRECIPITATION / GPM", "02", "Put rainfall in context", "Annual rainfall estimates help compare wet and dry years; precipitation alone does not establish a cause."),
        ("INTERPRETATION", "03", "Investigate, don't assume", "Statistical tests and an exploratory model support cautious interpretation and future field verification."),
    ]
    for col, (tag, index, heading, detail) in zip((a, b, c), blocks):
        with col:
            st.html(
                '<article class="bloom-evidence-card">'
                '<span>' + escape(index + " / " + tag) + '</span>'
                '<h3>' + escape(heading) + '</h3>'
                '<p>' + escape(detail) + '</p>'
                '</article>'
            )

    st.html(
        """
        <section class="bloom-final-invite">
          <span>READY TO INVESTIGATE?</span>
          <h2>Start with a place.<br><em>Leave with a clearer picture.</em></h2>
        </section>
        """
    )
    left, right, spacer = st.columns([1, 1, 2], gap="small")
    with left:
        if st.button("Open the map →", type="primary", use_container_width=True, key="home_end_map"):
            navigate("Explore")
    with right:
        if st.button("Compare areas ↗", use_container_width=True, key="home_end_compare"):
            navigate("Compare")
