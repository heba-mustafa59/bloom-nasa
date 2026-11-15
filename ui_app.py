
"""BLOOM / editorial multi-page frontend.

Run: python -m streamlit run ui_app.py
This is a self-contained UI entry point; app.py and data/science APIs are untouched.
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

NAV_NAMES = [label for label, _ in NAV]


def main() -> None:
    st.set_page_config(
        page_title="BLOOM / Beyond the Green",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            "About": "BLOOM — evidence-led vegetation research in Jericho."
        },
    )

    inject_styles(ROOT)

    if st.session_state.get("bloom_page") not in NAV_NAMES:
        st.session_state["bloom_page"] = "Home"

    def navigate(label: str) -> None:
        if label in NAV_NAMES:
            st.session_state["bloom_page"] = label
            st.rerun()

    # Top navigation bar
    try:
        bar = st.container(key="bloom_topnav")
    except TypeError:
        bar = st.container()

    with bar:
        st.markdown(
            '''
            <div class="bloom-nav-brand">
                <div class="bloom-nav-logo">
                    <span>
                        <b>BLOOM</b>
                    </span>
                </div>
                <div class="bloom-nav-meta">
                    <i></i> JERICHO
                    <span class="dot">·</span>
                    EARTH INTELLIGENCE
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

        links = st.columns(
            [1, 1, 1.12, 1.35, 1, 1, 1],
            gap="small"
        )

        for column, (label, _) in zip(links, NAV):
            with column:
                if st.button(
                    label,
                    key=f"nav_{label.replace(' ', '_')}",
                    type=(
                        "primary"
                        if st.session_state["bloom_page"] == label
                        else "secondary"
                    ),
                    use_container_width=True,
                ):
                    navigate(label)

    # Synchronize alternate sidebar navigation
    if (
        st.session_state.get("sidebar_page_selector")
        != st.session_state["bloom_page"]
    ):
        st.session_state["sidebar_page_selector"] = (
            st.session_state["bloom_page"]
        )

    def sidebar_changed() -> None:
        st.session_state["bloom_page"] = (
            st.session_state["sidebar_page_selector"]
        )

    with st.sidebar:
        st.markdown(
            '''
            <div class="bloom-side-head">
                <span>YOUR RESEARCH SPACE</span>
                <h3>Investigation<br>controls.</h3>
                <p>One study, many perspectives.</p>
            </div>
            ''',
            unsafe_allow_html=True,
        )

        st.caption("NAVIGATE")

        st.selectbox(
            "Choose a page",
            NAV_NAMES,
            key="sidebar_page_selector",
            on_change=sidebar_changed,
        )

        st.divider()
        st.caption("DATA SOURCE")

        source = st.radio(
            "Choose data source",
            ["Uploaded observations · verification pending", "Verified NASA only", "Synthetic demo"],
            key="bloom_source",
            label_visibility="collapsed",
            help=(
                "Uploaded observations are original repository CSVs, "
                "but their NASA export provenance is pending. "
                "Strict mode accepts only independently verified exports. "
                "Synthetic mode is for UI testing only."
            ),
        )

        mode = {
            "Uploaded observations · verification pending": "review",
            "Verified NASA only": "verified",
            "Synthetic demo": "demo",
        }[source]

        st.caption("STUDY AREA")

        area_id = st.selectbox(
            "Choose study area",
            list(AREA_LABELS),
            format_func=AREA_LABELS.get,
            key="bloom_area",
            label_visibility="collapsed",
        )

        st.caption("TIME WINDOW")

        start_year, end_year = st.slider(
            "Display years",
            min_value=2005,
            max_value=2024,
            value=(2005, 2024),
            key="bloom_years",
            label_visibility="collapsed",
        )

        st.divider()
        st.caption("METHODS")

        st.markdown("**MODIS** · Vegetation index")
        st.markdown("**GPM** · Rainfall estimates")
        st.caption(
            "Correlation does not establish causation."
        )

        st.markdown(
            '''
            <div class="bloom-side-bottom">
                BLOOM / 2026<br>
                Evidence before conclusions.
            </div>
            ''',
            unsafe_allow_html=True,
        )

    ctx = load_ui_context(
        mode,
        area_id,
        start_year,
        end_year
    )

    current_page = st.session_state["bloom_page"]

    # Home begins with the study overview
    if current_page != "Home":
        data_label(ctx)

    for name, page in NAV:
        if name == current_page:
            page.render(ctx, navigate)
            break

    ui_footer()


if __name__ == "__main__":
    main()
