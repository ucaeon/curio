# 골든셋 채점
from app.agents.schemas import AgentRunResult
from app.evaluation.schemas import GoldenCase


def _collect_text(result: AgentRunResult) -> str:
    parts = [result.overall_recommendation, result.report]
    parts.extend(strategy.operational_reason for strategy in result.strategies)
    return " ".join(parts)


def grade_golden_case(case: GoldenCase, result: AgentRunResult) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    expectation = case.expectation

    if result.critic.approved != expectation.expected_approved:
        reasons.append(
            "critic 승인 불일치 "
            f"(expected={expectation.expected_approved}, actual={result.critic.approved})"
        )

    expected_ids = {item.strategy_id for item in case.snapshot.strategies}
    actual_ids = {item.strategy_id for item in result.strategies}
    if expected_ids != actual_ids:
        reasons.append(
            f"strategy_id 불일치 (expected={sorted(expected_ids)}, actual={sorted(actual_ids)})"
        )

    text_blob = _collect_text(result)
    for keyword in expectation.required_keywords:
        if keyword not in text_blob:
            reasons.append(f"필수 키워드 누락: {keyword}")

    for keyword in expectation.forbidden_keywords:
        if keyword in text_blob:
            reasons.append(f"금지 키워드 포함: {keyword}")

    return not reasons, reasons
