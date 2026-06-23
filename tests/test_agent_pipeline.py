# Agent 파이프라인 단위 테스트
from unittest.mock import patch

from app.agents.analyst import build_analyst_summary
from app.agents.critic_agent import _python_metric_checks
from app.agents.pattern_agent import build_pattern_summary
from app.agents.schemas import (
    CriticOutput,
    EnrichedStrategy,
    PipelineSnapshot,
    StrategyAgentOutput,
    StrategyNarrative,
    StrategyRecord,
)
from app.agents.strategy_agent import _merge_narratives
from app.graph.workflow import create_agent_graph


def _sample_snapshot() -> PipelineSnapshot:
    return PipelineSnapshot(
        log_path="data/processed/synthetic/synthetic_log_test.csv",
        impression_count=1000,
        user_count=50,
        ctr=0.08,
        cvr=0.12,
        ctcvr=0.01,
        strategies=[
            StrategyRecord(
                strategy_id="strategy_001",
                strategy_name="sky=clear → category_group=outdoor",
                target_condition="sky=clear",
                recommended_action="category_group=outdoor",
                expected_ctr_gain=0.02,
                expected_cvr_gain=0.01,
                support=0.05,
                confidence=0.6,
                lift=1.4,
                strategy_score=0.42,
                reason="support=0.050, confidence=0.600, lift=1.400",
            )
        ],
    )


def test_build_analyst_summary() -> None:
    summary = build_analyst_summary(_sample_snapshot())
    assert "CTR 8.00%" in summary
    assert "1,000" in summary


def test_build_pattern_summary() -> None:
    summary = build_pattern_summary(_sample_snapshot())
    assert "맑은 날" in summary
    assert "야외 콘텐츠 노출" in summary
    assert "support 0.050" in summary
    assert "lift=1.400" not in summary


def test_merge_narratives_keeps_metrics() -> None:
    snapshot = _sample_snapshot()
    output = StrategyAgentOutput(
        narratives=[
            StrategyNarrative(
                strategy_id="strategy_001",
                operational_reason="맑은 날 야외형 소재 노출을 권장합니다.",
            )
        ],
        overall_recommendation="주말 야외 캠페인을 우선 검토하세요.",
    )
    enriched, overall = _merge_narratives(snapshot, output)
    assert len(enriched) == 1
    assert enriched[0].lift == 1.4
    assert "야외형" in enriched[0].operational_reason
    assert overall.startswith("주말")


def test_python_metric_checks_detects_drift() -> None:
    snapshot = _sample_snapshot()
    drifted = EnrichedStrategy(
        strategy_id="strategy_001",
        strategy_name="x",
        target_condition="sky=clear",
        recommended_action="category_group=outdoor",
        expected_ctr_gain=0.99,
        expected_cvr_gain=0.01,
        support=0.05,
        confidence=0.6,
        lift=1.4,
        strategy_score=0.42,
        operational_reason="test",
    )
    issues = _python_metric_checks(snapshot, [drifted])
    assert any("expected_ctr_gain" in issue.issue for issue in issues)


@patch("app.graph.workflow.run_report_agent", return_value="테스트 보고서")
@patch(
    "app.graph.workflow.run_critic_agent",
    return_value=CriticOutput(approved=True, issues=[], revised_summary="검증 통과"),
)
@patch("app.graph.workflow.run_strategy_agent")
def test_agent_graph_smoke(mock_strategy, _mock_critic, _mock_report) -> None:
    snapshot = _sample_snapshot()
    enriched = EnrichedStrategy(
        strategy_id="strategy_001",
        strategy_name=snapshot.strategies[0].strategy_name,
        target_condition=snapshot.strategies[0].target_condition,
        recommended_action=snapshot.strategies[0].recommended_action,
        expected_ctr_gain=snapshot.strategies[0].expected_ctr_gain,
        expected_cvr_gain=snapshot.strategies[0].expected_cvr_gain,
        support=snapshot.strategies[0].support,
        confidence=snapshot.strategies[0].confidence,
        lift=snapshot.strategies[0].lift,
        strategy_score=snapshot.strategies[0].strategy_score,
        operational_reason="운영 제안",
    )
    mock_strategy.return_value = ([enriched], "종합 제안")

    graph = create_agent_graph(snapshot)
    final = graph.invoke({})

    assert "CTR 8.00%" in final["analyst_summary"]
    assert final["critic"]["approved"] is True
    assert final["report"] == "테스트 보고서"
