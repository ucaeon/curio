# LangGraph 상태
from typing import TypedDict


class AgentGraphState(TypedDict, total=False):
    analyst_summary: str
    pattern_summary: str
    enriched_strategies: list[dict]
    overall_recommendation: str
    critic: dict
    report: str
