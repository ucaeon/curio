# 골든셋 평가 스키마
from pydantic import BaseModel, Field

from app.agents.schemas import PipelineSnapshot


class GoldenExpectation(BaseModel):
    expected_approved: bool
    required_keywords: list[str] = Field(default_factory=list)
    forbidden_keywords: list[str] = Field(default_factory=list)


class GoldenCase(BaseModel):
    case_id: str
    description: str
    snapshot: PipelineSnapshot
    expectation: GoldenExpectation


class CaseTrialResult(BaseModel):
    case_id: str
    trial: int
    passed: bool
    critic_approved: bool
    reasons: list[str]


class CaseAggregateResult(BaseModel):
    case_id: str
    trial_passes: list[bool]
    pass_at_k: bool
    pass_pow_k: bool


class EvalSuiteResult(BaseModel):
    k: int
    trials: int
    case_count: int
    pass_at_k: float
    pass_pow_k: float
    pass_at_1: float
    cases: list[CaseAggregateResult]
    trial_results: list[CaseTrialResult]
