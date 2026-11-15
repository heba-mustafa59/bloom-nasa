
"""Mystery Lab: validation before exploration, no fabricated predictions."""

from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.ui_components import (
    availability,
    number,
    page_header,
    section_title,
    stat_card,
    style_figure
)

from modules.ui_data import mystery_for


def render(ctx, navigate):
    page_header(
        "03 / THE UNKNOWN",
        "Not every green signal has an easy answer.",
        "Test whether rainfall alone predicts vegetation "
        "well enough to flag an unusual year."
    )

    if not availability(ctx):
        return

    result = mystery_for(ctx)
    status = str(
        result.get("model_status", "not_evaluated")
    )

    a, b, c = st.columns(
        3,
        gap="medium"
    )

    with a:
        stat_card(
            "MODEL STATUS",
            status.replace("_", " ").title(),
            "Out-of-sample validation"
        )

    with b:
        stat_card(
            "VALIDATION R²",
            number(result.get("validation_r2")),
            "A performance measure, not a cause",
            "sky"
        )

    with c:
        stat_card(
            "VALIDATION MAE",
            number(
                result.get("validation_mae"),
                4
            ),
            "Mean absolute prediction error · NDVI",
            "amber"
        )

    section_title(
        "01 / MODEL",
        "Model validation",
        "Checked against later observations before any anomaly is reported."
    )

    l, r = st.columns(
        [1.15, 1],
        gap="large"
    )

    with l:
        st.markdown(
            '''
            <div class="bloom-method-card">
                <div class="eyebrow">
                    THE VALIDATION GATE
                </div>

                <h3>Evidence before alerts.</h3>

                <p>
                    The linear model predicts NDVI from annual
                    rainfall. It must have a positive holdout R²
                    and beat a training-mean baseline on MAE
                    before any residual is considered worth flagging.
                </p>

                <div class="method-rule">
                    TRAIN 2005–2018
                    &nbsp; → &nbsp;
                    TEST 2019–2024
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )

    with r:
        if status == "validated":
            st.success(
                "The exploratory validation gate passed. "
                "Deviations are only leads for further study."
            )
        else:
            st.warning(
                "The model did not pass validation; no reliable anomaly alerts can be issued."
            )


    section_title(
        "02 / DEVIATIONS",
        "Observed versus expected",
        "Only validated outliers are displayed."
    )

    anomalies = result.get("anomalies") or []

    if status == "validated" and anomalies:
        frame = pd.DataFrame(anomalies)

        st.dataframe(
            frame,
            use_container_width=True,
            hide_index=True
        )

        if {
            "year",
            "residual"
        }.issubset(frame.columns):
            fig = go.Figure(
                go.Bar(
                    x=frame["year"],
                    y=frame["residual"],
                    marker_color=[
                        "#4C8B63"
                        if v >= 0
                        else "#D99A56"
                        for v in frame["residual"]
                    ]
                )
            )

            fig.add_hline(
                y=0,
                line_color="#163D2E"
            )

            style_figure(
                fig,
                "Observed − expected NDVI"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    else:
        st.info(
            "No defensible flagged years are available "
            "for the current model state."
        )

    if result.get("opposing_trends") is True:
        st.info(
            "Vegetation and rainfall show statistically "
            "supported opposite trend directions; "
            "this does not identify a cause."
        )

    section_title(
        "03 / VERDICT",
        "What the evidence shows",
        ""
    )

    verdict = escape(
        str(
            result.get("verdict") or "Pending analysis"
        )
    )

    st.markdown(
        f'''
        <div class="bloom-quote">
            <div class="eyebrow">
                SCIENTIFIC VERDICT
            </div>
            <p>{verdict}</p>
        </div>
        ''',
        unsafe_allow_html=True
    )

    with st.expander(
        "Methods and limitations",
        expanded=False
    ):
        st.write(
            "A validation-year residual may be flagged "
            "only when its absolute value exceeds twice "
            "the sample standard deviation of training "
            "residuals, and only if the model passes validation."
        )

        for limitation in result.get("limitations") or []:
            st.write("• " + str(limitation))

        st.caption(
            "Neither a good fit nor a flagged residual "
            "establishes irrigation or land-use causation."
        )

    if st.button(
        "Compare study areas ↗",
        type="primary",
        key="mystery_next"
    ):
        navigate("Compare")
