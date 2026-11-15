
"""User-interface report preview, independent of Integration's report_generator."""

from datetime import datetime, timezone

import streamlit as st

from modules.ui_components import (
    availability,
    number,
    page_header,
    section_title,
    stat_card
)

from modules.ui_data import (
    AREA_LABELS,
    mystery_for,
    trend_for
)


def _report(
    ctx,
    veg,
    rainfall,
    mystery
):
    source = (
        "SYNTHETIC DEMO — NOT NASA DATA"
        if ctx.is_demo
        else "LOCAL CSV — RESEARCH PREVIEW; NASA PROVENANCE PENDING"
        if ctx.mode == "local"
        else "VERIFIED NASA EXPORTS"
    )

    limitations = "\n".join(
        "- " + str(x)
        for x in mystery.get("limitations") or []
    )

    return f"""# BLOOM / Investigation brief

**Data source:** {source}
**Study area:** {AREA_LABELS[ctx.area_id]}
**Displayed period:** {ctx.start_year}–{ctx.end_year}
**Generated UTC:** {datetime.now(timezone.utc):%Y-%m-%d %H:%M}

## Vegetation trend
- Classification: {veg.get('direction', 'not_analyzed')}
- NDVI slope per decade: {number(veg.get('slope_per_decade'), 4)}
- Mann–Kendall p-value: {number(veg.get('p_value'), 4)}
- Valid years: {veg.get('n_observations', 0)}

## Rainfall trend
- Classification: {rainfall.get('direction', 'not_analyzed')}
- Rainfall slope per decade: {number(rainfall.get('slope_per_decade'), 2)} mm
- Mann–Kendall p-value: {number(rainfall.get('p_value'), 4)}

## Mystery model / full period
- Validation state: {mystery.get('model_status', 'not_evaluated')}
- Validation R²: {number(mystery.get('validation_r2'))}
- Validation MAE: {number(mystery.get('validation_mae'), 4)} NDVI
- Flagged years: {len(mystery.get('anomalies') or [])}
- Interpretation: {mystery.get('verdict', 'Pending analysis')}

## Limitations
{limitations or '- No additional model limitations were supplied.'}
- Correlation and anomalies are not proof of causation.
- This is a UI preview, not the Integration team's official report.
"""


def render(ctx, navigate):
    page_header(
        "05 / THE RECORD",
        "Make the evidence shareable.",
        "From exploration to a cautious, readable "
        "summary of what the observations support."
    )

    if not availability(ctx):
        return

    veg = trend_for(ctx, "ndvi")
    rain = trend_for(ctx, "rainfall_mm")
    mystery = mystery_for(ctx)

    a, b, c = st.columns(
        3,
        gap="medium"
    )

    with a:
        stat_card(
            "AREA",
            AREA_LABELS[ctx.area_id],
            "Current focus"
        )

    with b:
        stat_card(
            "VEGETATION SIGNAL",
            veg.get(
                "direction",
                "pending"
            ).replace("_", " ").title(),
            "Statistical classification",
            "amber"
        )

    with c:
        stat_card(
            "MODEL STATE",
            mystery.get(
                "model_status",
                "pending"
            ).replace("_", " ").title(),
            "Holdout evaluation",
            "sky"
        )

    section_title(
        "01 / INVESTIGATION BRIEF",
        "Your evidence report",
        "A preview designed for transparency, "
        "not unsupported certainty."
    )

    report = _report(
        ctx,
        veg,
        rain,
        mystery
    )

    with st.container(border=True):
        st.markdown(report)

    st.download_button(
        "Download investigation brief ↓",
        data=report.encode("utf-8"),
        file_name=(
            f"BLOOM_{ctx.area_id}_"
            f"{ctx.start_year}-{ctx.end_year}_preview.md"
        ),
        mime="text/markdown",
        type="primary",
        key="reports_download"
    )

    st.caption(
        "Integration can replace this self-contained "
        "preview with modules/report_generator.py "
        "once its implementation is ready."
    )

