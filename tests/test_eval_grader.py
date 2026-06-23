# 골든셋 채점 테스트
from app.agents.schemas import AgentRunResult, CriticOutput, EnrichedStrategy
from app.evaluation.golden_cases import build_golden_cases
from app.evaluation.grader import grade_golden_case


def _enriched_from_case(case_id: str) -> EnrichedStrategy:
    case = next(item for item in build_golden_cases() if item.case_id == case_id)
    strategy = case.snapshot.strategies[0]
    return EnrichedStrategy(
        strategy_id=strategy.strategy_id,
        strategy_name=strategy.strategy_name,
        target_condition=strategy.target_condition,
        recommended_action=strategy.recommended_action,
        expected_ctr_gain=strategy.expected_ctr_gain,
        expected_cvr_gain=strategy.expected_cvr_gain,
        support=strategy.support,
        confidence=strategy.confidence,
        lift=strategy.lift,
        strategy_score=strategy.strategy_score,
        operational_reason="맑은 날 야외 콘텐츠 노출을 권장합니다.",
    )


def test_grade_golden_case_pass() -> None:
    case = next(item for item in build_golden_cases() if item.case_id == "gs_clear_outdoor")
    result = AgentRunResult(
        analyst_summary="summary",
        pattern_summary="pattern",
        strategies=[_enriched_from_case("gs_clear_outdoor")],
        overall_recommendation="주말 야외 캠페인을 검토하세요.",
        critic=CriticOutput(approved=True, issues=[], revised_summary="통과"),
        report="report",
    )
    passed, reasons = grade_golden_case(case, result)
    assert passed is True
    assert reasons == []


def test_grade_golden_case_rejects_forbidden_keyword() -> None:
    case = next(item for item in build_golden_cases() if item.case_id == "gs_exaggeration_ban")
    enriched = _enriched_from_case("gs_exaggeration_ban")
    enriched = enriched.model_copy(update={"operational_reason": "무조건 노출하세요."})
    result = AgentRunResult(
        analyst_summary="summary",
        pattern_summary="pattern",
        strategies=[enriched],
        overall_recommendation="제안",
        critic=CriticOutput(approved=True, issues=[], revised_summary="통과"),
        report="report",
    )
    passed, reasons = grade_golden_case(case, result)
    assert passed is False
    assert any("무조건" in reason for reason in reasons)


def test_grade_empty_strategies_case() -> None:
    case = next(item for item in build_golden_cases() if item.case_id == "gs_empty_strategies")
    result = AgentRunResult(
        analyst_summary="summary",
        pattern_summary="pattern",
        strategies=[],
        overall_recommendation="전략 없음",
        critic=CriticOutput(approved=False, issues=[], revised_summary="전략 없음"),
        report="report",
    )
    passed, reasons = grade_golden_case(case, result)
    assert passed is True
    assert reasons == []


def test_golden_case_count() -> None:
    assert len(build_golden_cases()) == 20
