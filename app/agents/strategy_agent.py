# Strategy Agent: Top 전략 운영 설명 생성
import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import observe

from app.agents.llm import get_chat_model
from app.agents.prompt_loader import load_prompt
from app.agents.schemas import EnrichedStrategy, PipelineSnapshot, StrategyAgentOutput
from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def _merge_narratives(
    snapshot: PipelineSnapshot,
    output: StrategyAgentOutput,
) -> tuple[list[EnrichedStrategy], str]:
    narrative_map = {item.strategy_id: item.operational_reason for item in output.narratives}
    enriched: list[EnrichedStrategy] = []

    for strategy in snapshot.strategies:
        operational_reason = narrative_map.get(
            strategy.strategy_id,
            strategy.reason,
        )
        enriched.append(
            EnrichedStrategy(
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
                operational_reason=operational_reason,
            )
        )
    return enriched, output.overall_recommendation


@observe(as_type="generation", name="strategy-agent")
def run_strategy_agent(
    snapshot: PipelineSnapshot,
    analyst_summary: str,
    pattern_summary: str,
    settings: Settings | None = None,
) -> tuple[list[EnrichedStrategy], str]:
    config = settings or get_settings()
    if not snapshot.strategies:
        return [], "발굴된 전략이 없어 추가 타겟팅 제안을 생성하지 않았습니다."

    system_prompt = load_prompt("strategy_agent.md")
    user_payload = {
        "analyst_summary": analyst_summary,
        "pattern_summary": pattern_summary,
        "strategies": [item.model_dump() for item in snapshot.strategies],
    }
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=json.dumps(user_payload, ensure_ascii=False, indent=2)),
    ]

    llm = get_chat_model(config).with_structured_output(StrategyAgentOutput)
    result: StrategyAgentOutput = llm.invoke(messages)
    enriched, overall = _merge_narratives(snapshot, result)
    logger.info("Strategy Agent 완료: enriched=%s", len(enriched))
    return enriched, overall
