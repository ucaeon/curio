# Dashboard 에이전트 실행·전략 제안 UI
import logging

import pandas as pd
import streamlit as st

from app.agents.schemas import AgentRunResult, EnrichedStrategy
from app.config.settings import get_settings
from app.dashboard.formatters import (
    AGENT_DISPLAY_COLUMNS,
    DISPLAY_COLUMN_LABELS,
    build_strategy_display_table,
    format_percent,
    format_strategy_line,
)
from app.graph.workflow import run_agent_pipeline

logger = logging.getLogger(__name__)

AGENT_RESULT_KEY = "agent_result"


def is_agent_ready() -> bool:
    return bool(get_settings().openai_api_key)


def get_cached_agent_result() -> AgentRunResult | None:
    payload = st.session_state.get(AGENT_RESULT_KEY)
    if payload is None:
        return None
    return AgentRunResult(**payload)


def run_dashboard_agent(top_n: int) -> AgentRunResult:
    return run_agent_pipeline(top_n=top_n)


def store_agent_result(result: AgentRunResult) -> None:
    st.session_state[AGENT_RESULT_KEY] = result.model_dump()


def clear_agent_result() -> None:
    st.session_state.pop(AGENT_RESULT_KEY, None)


def build_agent_display_table(strategies: list[EnrichedStrategy]) -> pd.DataFrame:
    rows = [strategy.model_dump() for strategy in strategies]
    strategies_df = pd.DataFrame(rows)
    return build_strategy_display_table(
        strategies_df,
        display_columns=AGENT_DISPLAY_COLUMNS,
        column_labels={key: DISPLAY_COLUMN_LABELS[key] for key in AGENT_DISPLAY_COLUMNS},
    )


def render_agent_tab_controls(top_n: int) -> None:
    control_left, control_right = st.columns([1, 3])
    with control_left:
        if not is_agent_ready():
            st.warning("OPENAI_API_KEY가 없습니다.")
            return

        if st.button("에이전트 실행", type="primary", use_container_width=True, key="run_agent"):
            with st.spinner("에이전트가 전략을 생성하는 중..."):
                try:
                    result = run_dashboard_agent(top_n=top_n)
                    store_agent_result(result)
                    logger.info("Dashboard 에이전트 완료: approved=%s", result.critic.approved)
                    st.rerun()
                except FileNotFoundError as error:
                    st.error(f"데이터 파일 없음: {error}")
                except Exception as error:
                    logger.exception("Dashboard 에이전트 실패")
                    st.error(f"에이전트 실행 실패: {error}")

        if get_cached_agent_result() is not None:
            if st.button("결과 초기화", use_container_width=True, key="clear_agent"):
                clear_agent_result()
                st.rerun()

    with control_right:
        if get_cached_agent_result() is None:
            st.caption("에이전트 실행 후 결과가 표시됩니다.")


def render_agent_strategy_section() -> None:
    result = get_cached_agent_result()

    with st.container(border=True):
        st.markdown('<p class="section-label">에이전트 전략 제안</p>', unsafe_allow_html=True)
        st.markdown("##### 운영 제안 (Strategy + Critic)")

        if result is None:
            st.info("에이전트 실행 시 Top 전략에 운영 설명이 붙습니다.")
            return

        if result.critic.approved:
            st.success("Critic 검증 통과")
        else:
            st.warning("Critic 검증 미통과: 아래 이슈를 확인하세요.")

        summary_col, status_col = st.columns([3, 1])
        with summary_col:
            st.markdown("**종합 권고**")
            st.write(result.overall_recommendation)
        with status_col:
            st.metric("검증 전략 수", len(result.strategies))
            st.caption(result.critic.revised_summary)

        if result.critic.issues:
            with st.expander("Critic 이슈", expanded=not result.critic.approved):
                for issue in result.critic.issues:
                    st.markdown(f"- `{issue.strategy_id}`: {issue.issue}")

        if not result.strategies:
            st.warning("에이전트가 제안할 전략이 없습니다.")
            return

        st.dataframe(
            build_agent_display_table(result.strategies),
            use_container_width=True,
            hide_index=True,
        )

        for index, strategy in enumerate(result.strategies, start=1):
            strategy_title = format_strategy_line(
                strategy.target_condition,
                strategy.recommended_action,
            )
            with st.expander(f"전략 {index}: {strategy_title}", expanded=index == 1):
                metric_left, metric_right, metric_lift = st.columns(3)
                metric_left.metric("CTR 개선", format_percent(strategy.expected_ctr_gain))
                metric_right.metric("CVR 개선", format_percent(strategy.expected_cvr_gain))
                metric_lift.metric("Lift", f"{strategy.lift:.3f}")
                st.markdown("**운영 제안**")
                st.write(strategy.operational_reason)

        with st.expander("전체 보고서"):
            st.markdown(result.report)

        with st.expander("분석·패턴 요약"):
            st.markdown("**Analyst**")
            st.write(result.analyst_summary)
            st.markdown("**Pattern**")
            st.markdown(result.pattern_summary.replace("\n", "  \n"))
