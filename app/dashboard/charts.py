# Dashboard Plotly 차트
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.dashboard.theme import CHART_COLORS, CTR_COLOR, CVR_COLOR, PLOTLY_LAYOUT


def _apply_plotly_theme(figure: go.Figure) -> go.Figure:
    figure.update_layout(**PLOTLY_LAYOUT)
    figure.update_xaxes(showline=False, zeroline=False)
    figure.update_yaxes(showline=False)
    return figure


def _strategy_chart_labels(count: int) -> list[str]:
    return [f"전략 {index + 1}" for index in range(count)]


def _strategy_chart_yaxis(labels: list[str]) -> dict[str, str | list[str]]:
    return {"categoryorder": "array", "categoryarray": labels[::-1]}


def render_strategy_score_chart(strategies: pd.DataFrame) -> None:
    chart_df = strategies.copy().reset_index(drop=True)
    labels = _strategy_chart_labels(len(chart_df))
    chart_df["label"] = labels
    chart_df["bar_color"] = [
        CHART_COLORS[index % len(CHART_COLORS)] for index in range(len(chart_df))
    ]

    figure = go.Figure(
        go.Bar(
            x=chart_df["strategy_score"],
            y=chart_df["label"],
            orientation="h",
            marker={
                "color": chart_df["bar_color"],
                "line": {"width": 0},
                "cornerradius": 4,
            },
            hovertemplate="%{y}<br>점수: %{x:.3f}<extra></extra>",
        )
    )
    figure.update_layout(
        title="Strategy Score",
        xaxis_title="점수",
        yaxis=_strategy_chart_yaxis(labels),
        showlegend=False,
        bargap=0.28,
    )
    st.plotly_chart(_apply_plotly_theme(figure), use_container_width=True)


def render_gain_chart(strategies: pd.DataFrame) -> None:
    chart_df = strategies.copy().reset_index(drop=True)
    labels = _strategy_chart_labels(len(chart_df))

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            name="CTR 개선",
            y=labels,
            x=chart_df["expected_ctr_gain"],
            orientation="h",
            marker={"color": CTR_COLOR, "cornerradius": 4},
            hovertemplate="%{y}<br>CTR: %{x:.2%}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Bar(
            name="CVR 개선",
            y=labels,
            x=chart_df["expected_cvr_gain"],
            orientation="h",
            marker={"color": CVR_COLOR, "cornerradius": 4},
            hovertemplate="%{y}<br>CVR: %{x:.2%}<extra></extra>",
        )
    )
    figure.update_layout(
        title="예상 CTR / CVR 개선",
        xaxis_title="개선율",
        barmode="group",
        yaxis=_strategy_chart_yaxis(labels),
        bargap=0.22,
        bargroupgap=0.08,
        legend={"title": ""},
    )
    figure.update_xaxes(tickformat=".1%")
    st.plotly_chart(_apply_plotly_theme(figure), use_container_width=True)
