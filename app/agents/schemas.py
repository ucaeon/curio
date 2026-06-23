# Agent 구조화 출력 스키마
from pydantic import BaseModel, Field


class StrategyRecord(BaseModel):
    strategy_id: str
    strategy_name: str
    target_condition: str
    recommended_action: str
    expected_ctr_gain: float
    expected_cvr_gain: float
    support: float
    confidence: float
    lift: float
    strategy_score: float
    reason: str


class PipelineSnapshot(BaseModel):
    log_path: str
    impression_count: int
    user_count: int
    ctr: float
    cvr: float
    ctcvr: float
    strategies: list[StrategyRecord]


class StrategyNarrative(BaseModel):
    strategy_id: str
    operational_reason: str = Field(description="운영 설명")


class StrategyAgentOutput(BaseModel):
    narratives: list[StrategyNarrative]
    overall_recommendation: str = Field(description="종합 운영 제안")


class CriticIssue(BaseModel):
    strategy_id: str
    issue: str


class CriticOutput(BaseModel):
    approved: bool
    issues: list[CriticIssue]
    revised_summary: str = Field(description="검증 결과 요약")


class EnrichedStrategy(BaseModel):
    strategy_id: str
    strategy_name: str
    target_condition: str
    recommended_action: str
    expected_ctr_gain: float
    expected_cvr_gain: float
    support: float
    confidence: float
    lift: float
    strategy_score: float
    operational_reason: str


class AgentRunResult(BaseModel):
    analyst_summary: str
    pattern_summary: str
    strategies: list[EnrichedStrategy]
    overall_recommendation: str
    critic: CriticOutput
    report: str
