# 패턴 요약
from langfuse import observe

from app.agents.schemas import PipelineSnapshot
from app.analytics.strategy_labels import format_strategy_natural


@observe(name="pattern")
def build_pattern_summary(snapshot: PipelineSnapshot) -> str:
    if not snapshot.strategies:
        return "유효 대응 사례가 발굴되지 않았습니다."

    lines: list[str] = []
    for index, strategy in enumerate(snapshot.strategies, start=1):
        body = format_strategy_natural(
            strategy.target_condition,
            strategy.recommended_action,
            support=strategy.support,
            confidence=strategy.confidence,
            lift=strategy.lift,
        )
        lines.append(f"{index}. {body}")
    return "연관규칙 기반 유효 대응 사례:\n" + "\n".join(lines)
