# Dashboard 에이전트 패널 테스트
from app.agents.schemas import EnrichedStrategy
from app.dashboard.agent_panel import build_agent_display_table


def test_build_agent_display_table_formats_columns() -> None:
    strategies = [
        EnrichedStrategy(
            strategy_id="strategy_001",
            strategy_name="precip=rain -> category_group=indoor",
            target_condition="precip=rain",
            recommended_action="category_group=indoor",
            expected_ctr_gain=0.12,
            expected_cvr_gain=0.05,
            support=0.18,
            confidence=0.72,
            lift=1.02,
            strategy_score=0.41,
            operational_reason="비 오는 날 실내 소재를 우선 노출하세요.",
        )
    ]
    table = build_agent_display_table(strategies)
    assert "운영 제안" in table.columns
    assert table.iloc[0]["CTR 개선"] == "12.00%"
    assert "실내" in table.iloc[0]["추천 액션"]
    assert "비 오는 날" in table.iloc[0]["상황 조건"]
