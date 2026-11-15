
"""BLOOM reusable visual primitives; no analytical calculations."""

from __future__ import annotations

from html import escape
from math import isfinite
from pathlib import Path
import streamlit as st

FOREST = "#163D2E"
LEAF = "#4C8B63"
AMBER = "#D99A56"
SKY = "#62AFC8"


def inject_styles(root: Path) -> None:
    css = root / "assets" / "bloom.css"
    if css.exists():
        st.markdown(
            f"<style>{css.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def page_header(
    eyebrow: str,
    title: str,
    subtitle: str
) -> None:
    st.markdown(
        f'<header class="bloom-page-head">'
        f'<div class="eyebrow">{escape(eyebrow)}</div>'
        f'<h1>{escape(title)}</h1>'
        f'<p>{escape(subtitle)}</p></header>',
        unsafe_allow_html=True,
    )


def section_title(
    number: str,
    title: str,
    caption: str = ""
) -> None:
    st.markdown(
        f'<div class="bloom-section-heading">'
        f'<span>{escape(number)}</span>'
        f'<div><h2>{escape(title)}</h2>'
        f'<p>{escape(caption)}</p></div></div>',
        unsafe_allow_html=True,
    )


def stat_card(
    label: str,
    value: str,
    note: str,
    accent: str = "leaf"
) -> None:
    variant = (
        accent
        if accent in {"leaf", "amber", "sky"}
        else "leaf"
    )

    st.markdown(
        f'<div class="bloom-stat bloom-{variant}">'
        f'<span>{escape(label)}</span>'
        f'<strong>{escape(str(value))}</strong>'
        f'<small>{escape(note)}</small></div>',
        unsafe_allow_html=True,
    )


def feature_card(
    eyebrow: str,
    title: str,
    detail: str,
    number: str = ""
) -> None:
    st.markdown(
        f'<article class="bloom-feature">'
        f'<span class="feature-n">'
        f'{escape(number or eyebrow)}</span>'
        f'<h3>{escape(title)}</h3>'
        f'<p>{escape(detail)}</p></article>',
        unsafe_allow_html=True,
    )


def number(
    value,
    decimals: int = 3,
    suffix: str = ""
) -> str:
    try:
        if isinstance(value, bool) or value is None:
            return "N/A"

        x = float(value)

        return (
            f"{x:,.{decimals}f}{suffix}"
            if isfinite(x)
            else "N/A"
        )

    except (ValueError, TypeError):
        return "N/A"


def availability(ctx) -> bool:
    if ctx.ready:
        return True

    st.info(
        "**Data unavailable.** No verified NASA "
        "observations could be loaded for this view."
    )

    if ctx.error:
        with st.expander("See data loading details"):
            st.code(ctx.error)

    st.caption(
        "Switch to Synthetic demo in Research Controls "
        "to explore the interface. Demo values are not "
        "NASA measurements."
    )

    return False


def data_label(ctx) -> None:
    if ctx.is_demo:
        st.markdown(
            '''
            <div class="bloom-data-ribbon demo">
                <b>DEMO MODE</b>
                <span>
                    Synthetic values for design testing —
                    not NASA observations.
                </span>
            </div>
            ''',
            unsafe_allow_html=True,
        )
    elif ctx.metadata.get("verification_status") != "verified" and ctx.ready:
        st.markdown(
            '''
            <div class="bloom-data-ribbon real">
                <b>NASA STUDY DATA</b>
                <span>
                    Using original study observations;
                    independent export provenance review is pending.
                </span>
            </div>
            ''',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '''
            <div class="bloom-data-ribbon real">
                <b>NASA MODE</b>
                <span>
                    Verified-source mode. Unavailable
                    or invalid data will not be replaced.
                </span>
            </div>
            ''',
            unsafe_allow_html=True,
        )


def style_figure(
    fig,
    yaxis: str = ""
) -> None:
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(
            family="DM Sans, Arial",
            color=FOREST,
            size=12
        ),
        margin=dict(
            l=24,
            r=20,
            t=46,
            b=22
        ),
        height=370,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0
        ),
        xaxis=dict(
            title="Year",
            showgrid=False,
            tickformat="d"
        ),
        yaxis=dict(
            title=yaxis,
            gridcolor="#E9EEE9",
            zeroline=False
        ),
        hovermode="x unified",
    )


def ui_footer() -> None:
    st.markdown(
        '''
        <footer class="bloom-footer">
            <div class="footer-logo">
                BLOOM
                <span>Beyond the Green.</span>
            </div>
            <div class="footer-caption">
                JERICHO, PALESTINE
                &nbsp; / &nbsp; EARTH OBSERVATION
            </div>
            <small>
                Evidence first. Conclusions with context.<br>
                MODIS NDVI · GPM IMERG rainfall
            </small>
        </footer>
        ''',
        unsafe_allow_html=True,
    )
