"""BLOOM: one clear navigation system and visible study controls.

Main Streamlit entry point (app.py imports this main function).
Scientific calculations remain in the team's existing modules.
"""
from __future__ import annotations

from pathlib import Path
import streamlit as st

from modules.ui_components import inject_styles, ui_footer, data_label
from modules.ui_data import AREA_LABELS, load_ui_context
from modules.ui_pages import home, explore, analytics, mystery, compare, reports, about

ROOT = Path(__file__).resolve().parent

NAV = [
    ("Home", home),
    ("Explore", explore),
    ("Analytics", analytics),
    ("Mystery Lab", mystery),
    ("Compare", compare),
    ("Reports", reports),
    ("About", about),
]
NAV_NAMES = [name for name, _ in NAV]
NAV_TITLES = {
    "Home": "Overview",
    "Explore": "Explore map",
    "Analytics": "Analytics",
    "Mystery Lab": "Investigate",
    "Compare": "Compare areas",
    "Reports": "Reports",
    "About": "About",
}
SOURCE_CHOICES = [
    "Uploaded observations · verification pending",
    "Verified NASA only",
    "Synthetic demo",
]


def main() -> None:
    st.set_page_config(
        page_title="BLOOM | Earth Intelligence",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            "About": "BLOOM — exploring vegetation and rainfall in Jericho."
        },
    )
    inject_styles(ROOT)

    if st.session_state.get("bloom_page") not in NAV_NAMES:
        st.session_state["bloom_page"] = "Home"

    def navigate(page_name: str) -> None:
        if page_name in NAV_NAMES:
            st.session_state["bloom_page"] = page_name
            st.rerun()

    # Single destination state for desktop nav, mobile nav and page CTAs.
    if st.session_state.get("bloom_mobile_page") != st.session_state["bloom_page"]:
        st.session_state["bloom_mobile_page"] = st.session_state["bloom_page"]

    def mobile_changed() -> None:
        st.session_state["bloom_page"] = st.session_state["bloom_mobile_page"]

    with st.container(key="bloom_topnav"):
        st.markdown(
            """
            <div class="bloom-nav-brand">
              <div class="bloom-nav-logo">
                <span class="bloom-nav-mark" aria-hidden="true">◉</span>
                <b>BLOOM</b>
              </div>
              <div class="bloom-nav-meta">
                JERICHO, PALESTINE <span class="dot">·</span> EARTH INTELLIGENCE
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(key="bloom_desktop_nav"):
            columns = st.columns([1.05, 1.2, .95, 1.2, 1.25, .95, .85], gap="small")
            for column, (name, _) in zip(columns, NAV):
                with column:
                    if st.button(
                        NAV_TITLES[name],
                        key=f"nav_{name.replace(' ', '_')}",
                        type="primary" if st.session_state["bloom_page"] == name else "secondary",
                        use_container_width=True,
                    ):
                        navigate(name)

        with st.container(key="bloom_mobile_nav"):
            st.selectbox(
                "Go to",
                NAV_NAMES,
                format_func=NAV_TITLES.get,
                key="bloom_mobile_page",
                on_change=mobile_changed,
            )

    current_page = st.session_state["bloom_page"]

    # Study controls must be immediately discoverable, not hidden in sidebar.
    # On Home we focus on the overview; all exploration pages show controls.
    if current_page != "Home":
        with st.container(key="bloom_filters"):
            st.markdown(
                '<div class="bloom-filter-title"><strong>YOUR STUDY</strong>'
                '<span>Choose a region, period, and evidence source</span></div>',
                unsafe_allow_html=True,
            )
            src_col, area_col, period_col = st.columns([1.35, .85, 1.3], gap="medium")
            with src_col:
                source = st.selectbox(
                    "Data source",
                    SOURCE_CHOICES,
                    key="bloom_source",
                    help=(
                        "Pending observations come from uploaded CSV files. "
                        "Their original NASA export provenance is not independently confirmed. "
                        "Strict verified mode rejects them until verified."
                    ),
                )
            with area_col:
                area_id = st.selectbox(
                    "Study area",
                    list(AREA_LABELS),
                    format_func=AREA_LABELS.get,
                    key="bloom_area",
                )
            with period_col:
                start_year, end_year = st.slider(
                    "Years",
                    min_value=2005,
                    max_value=2024,
                    value=(2005, 2024),
                    key="bloom_years",
                )
    else:
        source = st.session_state.get("bloom_source", SOURCE_CHOICES[0])
        area_id = st.session_state.get("bloom_area", "area_a")
        start_year, end_year = st.session_state.get("bloom_years", (2005, 2024))

    mode = {
        SOURCE_CHOICES[0]: "review",
        SOURCE_CHOICES[1]: "verified",
        SOURCE_CHOICES[2]: "demo",
    }.get(source, "review")

    # The sidebar is only optional methodology/help. Critical controls are above.
    with st.sidebar:
        st.markdown(
            """
            <div class="bloom-side-head">
                <span>FIELD NOTES</span>
                <h3>Know the data.</h3>
                <p>Evidence first. Interpret with context.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("**Study**  ")
        st.caption("Jericho, Palestine · 2005–2024 · two study polygons")
        st.divider()
        st.markdown("**Satellite datasets**")
        st.markdown("MODIS MOD13Q1 · Vegetation index")
        st.markdown("GPM IMERG V07 · Rainfall estimates")
        st.divider()
        st.info(
            "Uploaded observations are provisional until source export "
            "provenance and exact matching polygons are confirmed."
        )
        st.caption(
            "Selecting a new area, period or data source is available at the "
            "top of each exploration page."
        )

    ctx = load_ui_context(mode, area_id, start_year, end_year)

    if current_page != "Home":
        data_label(ctx)

    for name, page in NAV:
        if name == current_page:
            page.render(ctx, navigate)
            break

    ui_footer()


if __name__ == "__main__":
    main()
