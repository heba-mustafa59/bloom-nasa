
"""Compare spatial areas using shared axes and the existing trend engine."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.ui_components import (
    availability,
    number,
    page_header,
    section_title,
    style_figure
)

from modules.ui_data import (
    AREA_LABELS,
    trend_for
)

COLORS = {
    "area_a": "#2E7254",
    "area_b": "#C58E50"
}


def render(ctx, navigate):
    page_header(
        "04 / TWO PERSPECTIVES",
        "A tale of two landscapes.",
        "Compare the same observation windows without "
        "assuming the areas share the same environmental drivers."
    )

    if not availability(ctx):
        return

    section_title(
        "01 / VEGETATION",
        "Two paths through time",
        "NDVI series share the same axis and calendar window."
    )

    fig = go.Figure()

    for area, label in AREA_LABELS.items():
        frame = ctx.area_data(
            "ndvi",
            area
        )

        fig.add_trace(
            go.Scatter(
                x=frame["year"],
                y=frame["ndvi"],
                mode="lines+markers",
                name=label,
                line=dict(
                    color=COLORS[area],
                    width=3
                ),
                marker=dict(size=6)
            )
        )

    style_figure(
        fig,
        "NDVI (unitless)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    section_title(
        "02 / PRECIPITATION",
        "The water context",
        "Annual precipitation totals (mm per year)."
    )

    rainfig = go.Figure()

    for area, label in AREA_LABELS.items():
        frame = ctx.area_data(
            "rainfall_mm",
            area
        )

        rainfig.add_trace(
            go.Bar(
                x=frame["year"],
                y=frame["rainfall_mm"],
                name=label,
                marker_color=COLORS[area],
                opacity=0.86
            )
        )

    rainfig.update_layout(
        barmode="group"
    )

    style_figure(
        rainfig,
        "Rainfall (mm/year)"
    )

    st.plotly_chart(
        rainfig,
        use_container_width=True
    )

    section_title(
        "03 / SIGNIFICANCE",
        "Compare the evidence",
        "Interpret p-values carefully; a non-significant "
        "trend is not proof of stability."
    )

    rows = []

    for area, label in AREA_LABELS.items():
        nv = trend_for(
            ctx,
            "ndvi",
            area
        )

        rv = trend_for(
            ctx,
            "rainfall_mm",
            area
        )

        rows.append({
            "Study area": label,
            "NDVI trend": nv.get(
                "direction",
                "not_analyzed"
            ),
            "NDVI / decade": number(
                nv.get("slope_per_decade"),
                4
            ),
            "NDVI p-value": number(
                nv.get("p_value"),
                4
            ),
            "Rainfall trend": rv.get(
                "direction",
                "not_analyzed"
            ),
            "Rainfall / decade (mm)": number(
                rv.get("slope_per_decade"),
                2
            ),
            "Rainfall p-value": number(
                rv.get("p_value"),
                4
            ),
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Comparative plots can inspire hypotheses, "
        "not demonstrate cause and effect."
    )

    if st.button(
        "Generate a report ↗",
        type="primary",
        key="compare_next"
    ):
        navigate("Reports")
