import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import observe

from app.agents.llm import get_chat_model
from app.agents.prompt_loader import load_prompt
from app.agents.schemas import CriticIssue, CriticOutput, EnrichedStrategy, PipelineSnapshot
from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

METRIC_TOLERANCE = 1e-6


def _python_metric_checks(
    snapshot: PipelineSnapshot,
    enriched: list[EnrichedStrategy],
) -> list[CriticIssue]:
    issues: list[CriticIssue] = []
    ground_truth = {item.strategy_id: item for item in snapshot.strategies}

    for strategy in enriched:
        truth = ground_truth.get(strategy.strategy_id)
        if truth is None:
            issues.append(
                CriticIssue(
                    strategy_id=strategy.strategy_id,
                    issue="하층 파이프라인에 없는 strategy_id",
                )
            )
            continue

        checks = [
            ("expected_ctr_gain", strategy.expected_ctr_gain, truth.expected_ctr_gain),
            ("expected_cvr_gain", strategy.expected_cvr_gain, truth.expected_cvr_gain),
            ("support", strategy.support, truth.support),
            ("confidence", strategy.confidence, truth.confidence),
            ("lift", strategy.lift, truth.lift),
            ("strategy_score", strategy.strategy_score, truth.strategy_score),
        ]
        for name, actual, expected in checks:
            if abs(actual - expected) > METRIC_TOLERANCE:
                issues.append(
                    CriticIssue(
                        strategy_id=strategy.strategy_id,
                        issue=f"{name} 불일치 (expected={expected}, actual={actual})",
                    )
                )
    return issues


@observe(as_type="generation", name="critic-agent")
def run_critic_agent(
    snapshot: PipelineSnapshot,
    analyst_summary: str,
    pattern_summary: str,
    enriched: list[EnrichedStrategy],
    overall_recommendation: str,
    settings: Settings | None = None,
) -> CriticOutput:
    config = settings or get_settings()
    metric_issues = _python_metric_checks(snapshot, enriched)

    if not enriched:
        return CriticOutput(
            approved=False,
            issues=metric_issues,
            revised_summary="검증할 전략이 없습니다.",
        )

    system_prompt = load_prompt("critic_agent.md")
    user_payload = {
        "analyst_summary": analyst_summary,
        "pattern_summary": pattern_summary,
        "overall_recommendation": overall_recommendation,
        "strategies": [item.model_dump() for item in enriched],
        "python_metric_issues": [item.model_dump() for item in metric_issues],
    }
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=json.dumps(user_payload, ensure_ascii=False, indent=2)),
    ]

    llm = get_chat_model(config).with_structured_output(CriticOutput)
    llm_result: CriticOutput = llm.invoke(messages)

    merged_issues = metric_issues + [
        issue for issue in llm_result.issues if issue not in metric_issues
    ]
    approved = llm_result.approved and not metric_issues
    output = CriticOutput(
        approved=approved,
        issues=merged_issues,
        revised_summary=llm_result.revised_summary,
    )
    logger.info("Critic Agent 완료: approved=%s issues=%s", output.approved, len(output.issues))
    return output
