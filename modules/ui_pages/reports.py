
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
        else (
            "NASA-source CSVs uploaded to the repository — original export provenance pending"
            if ctx.metadata.get("verification_status") != "verified"
            else "NASA EXPORTS — VERIFIED IN METADATA"
        )
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

    # Attach the same explainable Area Advisor result shown in Explore.
    # Demo mode keeps its existing report behavior; no synthetic values
    # are ever passed off as uploaded NASA observations.
    if not ctx.is_demo:
        from modules.area_advisor import GOAL_LABELS, advise_area, advisor_report
        from modules.investigation_case import CaseData

        selected_goal = st.selectbox(
            "Area Advisor question",
            list(GOAL_LABELS),
            format_func=GOAL_LABELS.get,
            key="bloom_report_advisor_goal",
        )
        data = CaseData(ctx.ndvi_df, ctx.rainfall_df, ctx.geojson, ctx.metadata)
        recommendation = advise_area(data, selected_goal, int(ctx.end_year))
        st.write(
            "**Suggested area:** "
            + (("Area A" if recommendation.winner == "area_a" else "Area B")
               if recommendation.winner else "No clear recommendation")
        )
        st.caption(recommendation.explanation)
        report += "\n---\n\n" + advisor_report(data, recommendation)
        from modules.action_planner import build_action_plan, action_plan_markdown
        action_plan = build_action_plan(
            data,
            recommendation,
            recommendation.winner or ctx.area_id,
        )
        report += "\n---\n\n" + action_plan_markdown(data, action_plan)
        st.caption(
            "The downloaded report includes a proposed field-verification and "
            "monitoring pathway. No intervention or outcome is claimed as verified."
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

