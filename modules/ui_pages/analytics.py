
"""Trend dashboard; reuses team-owned scientific renderer and functions."""

import streamlit as st

from modules.dashboard import render_dashboard

from modules.ui_components import (
    availability,
    number,
    page_header,
    section_title,
    stat_card
)

from modules.ui_data import (
    mystery_for,
    trend_for
)


def render(ctx, navigate):
    page_header(
        "02 / THE EVIDENCE",
        "Patterns, measured.",
        "Explore annual vegetation and rainfall observations "
        "— then test whether the change is statistically supported."
    )

    if not availability(ctx):
        return

    nd = ctx.area_data("ndvi")
    rain = ctx.area_data("rainfall_mm")

    nd_trend = trend_for(ctx, "ndvi")
    rain_trend = trend_for(ctx, "rainfall_mm")

    a, b, c, d = st.columns(
        4,
        gap="small"
    )

    with a:
        stat_card(
            "AVERAGE NDVI",
            number(
                nd["ndvi"].mean()
                if len(nd)
                else None
            ),
            "Selected period"
        )

    with b:
        stat_card(
            "MEAN ANNUAL RAIN",
            number(
                rain["rainfall_mm"].mean()
                if len(rain)
                else None,
                1,
                " mm"
            ),
            "Selected period",
            "sky"
        )

    with c:
        stat_card(
            "NDVI SLOPE / DECADE",
            number(
                nd_trend.get("slope_per_decade"),
                4
            ),
            "Linear regression estimate",
            "amber"
        )

    with d:
        stat_card(
            "VALID NDVI YEARS",
            str(
                nd_trend.get("n_observations", 0)
            ),
            "Usable yearly measurements"
        )

    section_title(
        "THE DATA LAB",
        "The long view",
        "The plots and tests below are computed "
        "from the selected area's observations."
    )

    render_dashboard(
        nd,
        rain,
        {
            "ndvi": nd_trend,
            "rainfall": rain_trend
        },
        mystery_for(ctx)
    )

    with st.expander("About the analysis period"):
        st.write(
            "Anomaly-model validation uses 2005–2024, even when a shorter "
            "range is selected for chart display."
        )

    with st.expander(
        "View or download observations"
    ):
        l, r = st.columns(2)

        with l:
            st.dataframe(
                nd,
                hide_index=True,
                use_container_width=True
            )

            st.download_button(
                "NDVI / CSV",
                nd.to_csv(index=False).encode("utf-8"),
                "bloom_ndvi_selection.csv",
                "text/csv",
                key="analytics_ndvi_csv"
            )

        with r:
            st.dataframe(
                rain,
                hide_index=True,
                use_container_width=True
            )

            st.download_button(
                "Rainfall / CSV",
                rain.to_csv(index=False).encode("utf-8"),
                "bloom_rainfall_selection.csv",
                "text/csv",
                key="analytics_rain_csv"
            )

    if st.button(
        "Investigate the mystery ↗",
        type="primary",
        key="analytics_next"
    ):
        navigate("Mystery Lab")
