"""BLOOM Evidence Lab, Mystery Detector, and scientific verdict UI.

Reads the integration contract's data. Does not perform statistical analyses.
"""
from __future__ import annotations

from math import isfinite

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

FOREST = "#1F3018"
LEAF = "#769945"
AMBER = "#B68548"
SKY = "#648B9A"


def _number(value, decimals=3):
    """Format available numbers, preserving genuine zero and avoiding NaN."""
    if isinstance(value, bool):
        return "N/A"
    try:
        number = float(value)
        return f"{number:,.{decimals}f}" if isfinite(number) else "N/A"
    except (TypeError, ValueError):
        return "N/A"


def _series(df, column, label):
    """Validate chart inputs; integration is responsible for area/year filtering."""
    expected = {"year", "area_id", column}
    if not isinstance(df, pd.DataFrame) or df.empty:
        st.info(f"{label}: NASA data not yet available.")
        return pd.DataFrame()
    if not expected.issubset(df.columns):
        st.warning(f"{label}: required columns are missing.")
        return pd.DataFrame()
    if df["area_id"].dropna().nunique() > 1:
        st.error(f"{label}: more than one study area was provided. Check app.py filtering.")
        return pd.DataFrame()
    result = df[["year", column]].copy()
    result["year"] = pd.to_numeric(result["year"], errors="coerce")
    result[column] = pd.to_numeric(result[column], errors="coerce")
    result = result.dropna(subset=["year", column])
    result = result[result["year"] % 1 == 0].sort_values("year")
    if result.empty:
        st.info(f"{label}: no valid observations in the selected period.")
        return result
    if result["year"].duplicated().any():
        st.error(f"{label}: duplicate year records detected. Please check the data loader.")
        return pd.DataFrame()
    result["year"] = result["year"].astype(int)
    return result


def _chart(df, column, label, kind, color, unit):
    st.markdown(f"**{label}**")
    clean = _series(df, column, label)
    if clean.empty:
        return
    fig = go.Figure()
    if kind == "bar":
        fig.add_trace(go.Bar(
            x=clean["year"], y=clean[column], marker_color=color,
            name=label, hovertemplate="Year %{x}<br>%{y:.1f} mm<extra></extra>",
        ))
    else:
        fig.add_trace(go.Scatter(
            x=clean["year"], y=clean[column], mode="lines+markers",
            line=dict(color=color, width=3), marker=dict(size=7),
            name=label, hovertemplate="Year %{x}<br>NDVI %{y:.4f}<extra></extra>",
        ))
    fig.update_layout(
        template="plotly_white", height=310, margin=dict(l=12, r=12, t=16, b=15),
        paper_bgcolor="white", plot_bgcolor="white", showlegend=False,
        xaxis_title="Year", yaxis_title=unit,
        font=dict(family="DM Sans, Arial", color=FOREST, size=14),
    )
    fig.update_xaxes(dtick=max(1, len(clean) // 6), tickformat="d", showgrid=False)
    fig.update_yaxes(gridcolor="#EEF0EA", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)


def _classification(result):
    if not isinstance(result, dict) or result.get("status") == "not_analyzed":
        return "Awaiting analysis"
    direction = result.get("direction")
    significant = result.get("significant")
    if direction == "insufficient_data" or significant is None:
        return "Not enough observations"
    if significant is False or direction == "not_significant":
        return "Not statistically significant"
    if significant is True and direction == "increasing":
        return "Significant increase"
    if significant is True and direction == "decreasing":
        return "Significant decrease"
    return "Inconclusive result"


def _trend_metrics(label, result, unit):
    st.markdown(f"**{label} statistics**")
    if not isinstance(result, dict):
        result = {}
    direction = _classification(result)
    slope = _number(result.get("slope_per_decade"), 4 if unit == "NDVI" else 2)
    if slope != "N/A":
        slope += f" {unit}/decade"
    pvalue = _number(result.get("p_value"), 4)
    significance = result.get("significant")
    significance_label = (
        "Yes" if significance is True else
        "No" if significance is False else "N/A"
    )
    columns = st.columns(4)
    for col, (title, value) in zip(columns, [
        ("Trend", direction), ("Slope", slope),
        ("Mann–Kendall p", pvalue), ("Significant?", significance_label),
    ]):
        with col:
            st.metric(title, value)
    if direction == "Not statistically significant":
        st.caption("A non-significant result does not prove the vegetation or rainfall is stable.")


def _mystery(mystery_result):
    st.markdown("### 03 / Anomaly Check")
    if not isinstance(mystery_result, dict) or not mystery_result:
        st.info("Mystery analysis not yet available.")
        return
    status = str(mystery_result.get("model_status") or "not_evaluated")
    if status == "not_evaluated":
        st.info("Model not evaluated yet. No anomaly conclusion is available.")
        return
    if status in {"insufficient_evidence", "unreliable", "failed", "error"}:
        st.warning("The rainfall model did not pass validation. Anomalies cannot be identified reliably.")
        return

    a, b = st.columns(2)
    with a:
        st.metric("Validation R²", _number(mystery_result.get("validation_r2")))
    with b:
        st.metric("Validation MAE", _number(mystery_result.get("validation_mae")))

    # Optional prediction-series keys are displayed only if the model supplies them.
    predictions = mystery_result.get("predictions")
    if isinstance(predictions, list) and predictions:
        frame = pd.DataFrame(predictions)
        required = {"year", "observed_ndvi", "predicted_ndvi"}
        if required.issubset(frame.columns):
            for col in required:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
            frame = frame.dropna(subset=list(required)).sort_values("year")
            if not frame.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=frame["year"], y=frame["observed_ndvi"],
                                         mode="lines+markers", name="Observed NDVI",
                                         line=dict(color=LEAF, width=3)))
                fig.add_trace(go.Scatter(x=frame["year"], y=frame["predicted_ndvi"],
                                         mode="lines+markers", name="Rainfall-based expected NDVI",
                                         line=dict(color=AMBER, dash="dash", width=2)))
                fig.update_layout(template="plotly_white", height=310,
                                  xaxis_title="Year", yaxis_title="NDVI (unitless)",
                                  legend=dict(orientation="h", y=-0.25),
                                  margin=dict(l=12, r=12, t=12, b=12))
                st.plotly_chart(fig, use_container_width=True)

    anomalies = mystery_result.get("anomalies")
    if isinstance(anomalies, list) and anomalies:
        st.markdown("**Flagged years (model output)**")
        st.dataframe(pd.DataFrame(anomalies), use_container_width=True, hide_index=True)
    else:
        st.caption("No anomalies identified by the validated model.")
    opposite = mystery_result.get("opposing_trends")
    if opposite is True:
        st.info("Opposing vegetation and rainfall trends were flagged for further investigation.")
    verdict = mystery_result.get("verdict")
    if verdict:
        st.write(verdict)
    for limitation in mystery_result.get("limitations") or []:
        st.caption("Limitation: " + str(limitation))
    st.caption("Correlation or prediction residuals alone cannot establish causation.")


def _verdict(trend_results, mystery_result):
    st.markdown("### 04 / Key Findings")
    if not isinstance(trend_results, dict):
        trend_results = {}
    for key, title in (("ndvi", "Vegetation"), ("rainfall", "Rainfall")):
        outcome = _classification(trend_results.get(key))
        st.write(f"**{title}:** {outcome}.")
    if isinstance(mystery_result, dict):
        if mystery_result.get("model_status") in {"insufficient_evidence", "unreliable", "failed"}:
            pass  # Validation warning is already displayed in Anomaly Check.
        elif mystery_result.get("model_status") in (None, "not_evaluated"):
            st.info("Mystery verdict: Pending analysis.")
        elif mystery_result.get("verdict"):
            st.write("**Mystery verdict:** " + str(mystery_result["verdict"]))
    with st.expander("Interpretation limits"):
        st.write(
            "Resolution differences, missing observations and unmeasured "
            "environmental factors can affect results. These trends do not establish causation."
        )


def render_dashboard(ndvi_df, rainfall_df, trend_results: dict, mystery_result: dict) -> None:
    """Render evidence charts, supplied statistical metrics, mystery and verdict."""
    st.markdown("### 02 / Observed Changes")
    col_ndvi, col_rain = st.columns(2)
    with col_ndvi:
        _chart(ndvi_df, "ndvi", "Vegetation index", "line", LEAF, "NDVI (unitless)")
    with col_rain:
        _chart(rainfall_df, "rainfall_mm", "Annual rainfall", "bar", SKY, "Rainfall (mm/year)")

    if not isinstance(trend_results, dict):
        trend_results = {}
    _trend_metrics("Vegetation", trend_results.get("ndvi"), "NDVI")
    _trend_metrics("Rainfall", trend_results.get("rainfall"), "mm")
    st.divider()
    _mystery(mystery_result)
    st.divider()
    _verdict(trend_results, mystery_result)
