# Slack 알림 메시지 빌더 테스트
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app.agents.schemas import AgentRunResult, CriticIssue, CriticOutput, EnrichedStrategy
from app.monitoring import slack_notify
from app.pipeline.load import DashboardData


def _sample_agent_result(*, approved: bool = True) -> AgentRunResult:
    strategy = EnrichedStrategy(
        strategy_id="strategy_001",
        strategy_name="sky=clear & weekend=1 → category_group=outdoor",
        target_condition="sky=clear & weekend=1",
        recommended_action="category_group=outdoor",
        expected_ctr_gain=0.0536,
        expected_cvr_gain=0.1158,
        support=0.082,
        confidence=0.509,
        lift=3.092,
        strategy_score=0.284,
        operational_reason="맑은 주말 야외 노출",
    )
    critic = CriticOutput(
        approved=approved,
        issues=[] if approved else [CriticIssue(strategy_id="strategy_001", issue="지표 불일치")],
        revised_summary="승인" if approved else "거절",
    )
    return AgentRunResult(
        analyst_summary="요약",
        pattern_summary="패턴",
        strategies=[strategy],
        overall_recommendation="야외 콘텐츠 집중 노출",
        critic=critic,
        report="보고서",
    )


def _sample_dashboard_data(tmp_path: Path) -> DashboardData:
    metrics = pd.DataFrame([{"ctr": 0.1086, "cvr": 0.1473, "ctcvr": 0.016}])
    strategies = pd.DataFrame(
        [
            {
                "strategy_id": "strategy_001",
                "strategy_name": "test",
                "target_condition": "sky=clear & weekend=1",
                "recommended_action": "category_group=outdoor",
                "expected_ctr_gain": 0.0536,
                "expected_cvr_gain": 0.1158,
                "support": 0.082,
                "confidence": 0.509,
                "lift": 3.092,
                "strategy_score": 0.284,
                "reason": "test",
            }
        ]
    )
    features_dir = tmp_path / "features"
    features_dir.mkdir()
    creatives_path = features_dir / "creatives_unit.csv"
    creatives_path.write_text("creative_id\nc1\n", encoding="utf-8")
    context_path = features_dir / "context_unit.csv"
    context_path.write_text("context_id\nc1\n", encoding="utf-8")

    return DashboardData(
        log_path=tmp_path / "synthetic_log_unit.csv",
        creatives_path=creatives_path,
        log_df=pd.DataFrame(),
        metrics=metrics,
        strategies=strategies,
        impression_count=10_000,
        user_count=500,
    )


@patch("app.monitoring.slack_notify.find_latest_prefixed_csv")
@patch("app.monitoring.slack_notify.load_pipeline_data")
def test_build_pipeline_success_message(
    mock_load_pipeline: object,
    mock_find_latest: object,
    tmp_path: Path,
) -> None:
    dashboard_data = _sample_dashboard_data(tmp_path)
    mock_load_pipeline.return_value = dashboard_data
    mock_find_latest.return_value = dashboard_data.creatives_path.parent / "context_unit.csv"

    agent_result = _sample_agent_result(approved=True)
    agent_path = tmp_path / "run_test.json"
    agent_path.write_text(agent_result.model_dump_json(), encoding="utf-8")

    message = slack_notify.build_pipeline_success_message(
        execution_date="2026-06-18 20:51",
        duration_sec=280,
        agent_result_path=agent_path,
    )

    assert "✅ Curio 파이프라인 완료" in message
    assert "CTR 10.86%" in message
    assert "🎯 Top 전략" in message
    assert "맑은 날" in message
    assert "Critic: ✅ 승인" in message


@patch("app.monitoring.slack_notify.find_latest_prefixed_csv")
@patch("app.monitoring.slack_notify.load_pipeline_data")
def test_build_critic_rejected_message(
    mock_load_pipeline: object,
    mock_find_latest: object,
    tmp_path: Path,
) -> None:
    dashboard_data = _sample_dashboard_data(tmp_path)
    mock_load_pipeline.return_value = dashboard_data
    mock_find_latest.return_value = dashboard_data.creatives_path.parent / "context_unit.csv"

    agent_result = _sample_agent_result(approved=False)
    agent_path = tmp_path / "run_reject_test.json"
    agent_path.write_text(agent_result.model_dump_json(), encoding="utf-8")

    message = slack_notify.build_critic_rejected_message(
        execution_date="2026-06-18 20:51",
        agent_result_path=agent_path,
    )

    assert "❌ Curio 파이프라인 실패: Critic 거절" in message
    assert "Critic: ❌ 거절" in message
    assert "지표 불일치" in message


def test_build_failure_message() -> None:
    message = slack_notify.build_failure_message(
        task_id="ingest_weather",
        execution_date="2026-06-18 20:51",
        error="API timeout",
    )
    assert "ingest_weather" in message
    assert "API timeout" in message
