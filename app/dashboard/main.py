# Streamlit 타겟팅 전략 Dashboard
import logging

import pandas as pd
import streamlit as st

from app.dashboard.agent_panel import render_agent_strategy_section, render_agent_tab_controls
from app.dashboard.charts import render_gain_chart, render_strategy_score_chart
from app.dashboard.formatters import (
    ANALYSIS_DISPLAY_COLUMNS,
    DISPLAY_COLUMN_LABELS,
    build_strategy_display_table,
    format_percent,
)
from app.dashboard.styles import apply_dashboard_styles, render_header
from app.pipeline.load import DashboardData, load_dashboard_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


@st.cache_data(show_spinner="분석 데이터를 불러오는 중...")
def get_dashboard_data(top_n: int) -> DashboardData:
    return load_dashboard_data(top_n=top_n)


def render_kpi_row(metrics: pd.DataFrame) -> None:
    row = metrics.iloc[0]
    col_ctr, col_cvr, col_ctcvr = st.columns(3)
    col_ctr.metric("CTR", format_percent(float(row["ctr"])))
    col_cvr.metric("CVR", format_percent(float(row["cvr"])))
    col_ctcvr.metric("CTCVR", format_percent(float(row["ctcvr"])))


def render_sidebar_controls() -> int:
    with st.sidebar:
        st.markdown('<p class="section-label">설정</p>', unsafe_allow_html=True)
        return st.slider("Top N 전략", min_value=3, max_value=10, value=5)


def render_sidebar_info(data: DashboardData) -> None:
    with st.sidebar:
        st.markdown('<p class="section-label">데이터 정보</p>', unsafe_allow_html=True)
        with st.container(border=True):
            st.caption("노출 로그")
            st.write(data.log_path.name)
            st.caption("소재 카탈로그")
            st.write(data.creatives_path.name)
            st.divider()
            st.metric("Impression", f"{data.impression_count:,}")
            st.metric("유저", f"{data.user_count:,}")


def render_analysis_tab(data: DashboardData, top_n: int) -> None:
    with st.container(border=True):
        st.markdown('<p class="section-label">성과 지표</p>', unsafe_allow_html=True)
        render_kpi_row(data.metrics)

    with st.container(border=True):
        st.markdown('<p class="section-label">타겟팅 전략</p>', unsafe_allow_html=True)
        st.markdown(f"##### Top {top_n} 운영 전략")
        if data.strategies.empty:
            st.warning("선정된 전략이 없습니다. 패턴 분석 조건을 확인하세요.")
        else:
            st.dataframe(
                build_strategy_display_table(
                    data.strategies,
                    display_columns=ANALYSIS_DISPLAY_COLUMNS,
                    column_labels=DISPLAY_COLUMN_LABELS,
                ),
                use_container_width=True,
                hide_index=True,
            )

    if not data.strategies.empty:
        chart_left, chart_right = st.columns(2, gap="medium")
        with chart_left:
            with st.container(border=True):
                render_strategy_score_chart(data.strategies)
        with chart_right:
            with st.container(border=True):
                render_gain_chart(data.strategies)


def main() -> None:
    st.set_page_config(
        page_title="Curio Strategy Dashboard",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_dashboard_styles()
    render_header("Curio 타겟팅 전략 Dashboard")

    top_n = render_sidebar_controls()

    try:
        data = get_dashboard_data(top_n=top_n)
    except FileNotFoundError as error:
        st.error(f"데이터 파일을 찾을 수 없습니다: {error}")
        st.info("feature·synthetic 로그 생성 후 다시 실행하세요.")
        return

    render_sidebar_info(data)

    tab_analysis, tab_agent = st.tabs(["성과·전략 분석", "에이전트 운영 제안"])

    with tab_analysis:
        render_analysis_tab(data, top_n=top_n)

    with tab_agent:
        render_agent_tab_controls(top_n=top_n)
        render_agent_strategy_section()


if __name__ == "__main__":
    main()
