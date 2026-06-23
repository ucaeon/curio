# 골든셋 정의
import json
from pathlib import Path

from app.agents.schemas import PipelineSnapshot, StrategyRecord
from app.evaluation.schemas import GoldenCase, GoldenExpectation

GOLDEN_CASES_PATH = Path("data/eval/golden_agent_cases.json")


def _strategy(
    strategy_id: str,
    target_condition: str,
    recommended_action: str,
    *,
    expected_ctr_gain: float = 0.02,
    expected_cvr_gain: float = 0.01,
    support: float = 0.05,
    confidence: float = 0.6,
    lift: float = 1.4,
    strategy_score: float = 0.42,
) -> StrategyRecord:
    strategy_name = f"{target_condition} → {recommended_action}"
    reason = f"support={support:.3f}, confidence={confidence:.3f}, lift={lift:.3f}"
    return StrategyRecord(
        strategy_id=strategy_id,
        strategy_name=strategy_name,
        target_condition=target_condition,
        recommended_action=recommended_action,
        expected_ctr_gain=expected_ctr_gain,
        expected_cvr_gain=expected_cvr_gain,
        support=support,
        confidence=confidence,
        lift=lift,
        strategy_score=strategy_score,
        reason=reason,
    )


def _snapshot(
    case_id: str,
    strategies: list[StrategyRecord],
    *,
    impression_count: int = 1000,
    user_count: int = 50,
    ctr: float = 0.08,
    cvr: float = 0.12,
    ctcvr: float = 0.01,
) -> PipelineSnapshot:
    return PipelineSnapshot(
        log_path=f"data/eval/golden/{case_id}.csv",
        impression_count=impression_count,
        user_count=user_count,
        ctr=ctr,
        cvr=cvr,
        ctcvr=ctcvr,
        strategies=strategies,
    )


def build_golden_cases() -> list[GoldenCase]:
    return [
        GoldenCase(
            case_id="gs_clear_outdoor",
            description="맑은 날 야외 콘텐츠 단일 전략",
            snapshot=_snapshot(
                "gs_clear_outdoor",
                [_strategy("strategy_001", "sky=clear", "category_group=outdoor")],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                required_keywords=["맑", "야외"],
            ),
        ),
        GoldenCase(
            case_id="gs_rain_indoor",
            description="비 오는 날 실내 콘텐츠 단일 전략",
            snapshot=_snapshot(
                "gs_rain_indoor",
                [_strategy("strategy_001", "precip=rain", "category_group=indoor")],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                required_keywords=["비", "실내"],
            ),
        ),
        GoldenCase(
            case_id="gs_clear_weekend_outdoor",
            description="맑은 주말 야외 복합 조건",
            snapshot=_snapshot(
                "gs_clear_weekend_outdoor",
                [
                    _strategy(
                        "strategy_001",
                        "sky=clear & weekend=1",
                        "category_group=outdoor",
                    )
                ],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                required_keywords=["주말", "야외"],
            ),
        ),
        GoldenCase(
            case_id="gs_rain_weekday_indoor",
            description="비 오는 평일 실내 복합 조건",
            snapshot=_snapshot(
                "gs_rain_weekday_indoor",
                [
                    _strategy(
                        "strategy_001",
                        "precip=rain & weekend=0",
                        "category_group=indoor",
                    )
                ],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                required_keywords=["평일", "실내"],
            ),
        ),
        GoldenCase(
            case_id="gs_cloudy_indoor",
            description="구름 많은 날 실내 전략",
            snapshot=_snapshot(
                "gs_cloudy_indoor",
                [_strategy("strategy_001", "sky=cloudy", "category_group=indoor")],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                required_keywords=["구름", "실내"],
            ),
        ),
        GoldenCase(
            case_id="gs_overcast_outdoor",
            description="흐린 날 야외 전략",
            snapshot=_snapshot(
                "gs_overcast_outdoor",
                [_strategy("strategy_001", "sky=overcast", "category_group=outdoor")],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                required_keywords=["흐린", "야외"],
            ),
        ),
        GoldenCase(
            case_id="gs_segment0_outdoor",
            description="segment_0 세그먼트 야외 타겟",
            snapshot=_snapshot(
                "gs_segment0_outdoor",
                [
                    _strategy(
                        "strategy_001",
                        "user_segment=segment_0",
                        "category_group=outdoor",
                    )
                ],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                required_keywords=["야외"],
            ),
        ),
        GoldenCase(
            case_id="gs_segment2_indoor",
            description="segment_2 세그먼트 실내 타겟",
            snapshot=_snapshot(
                "gs_segment2_indoor",
                [
                    _strategy(
                        "strategy_001",
                        "user_segment=segment_2",
                        "category_group=indoor",
                    )
                ],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                required_keywords=["실내"],
            ),
        ),
        GoldenCase(
            case_id="gs_clear_event",
            description="맑은 날 행사 소재 노출",
            snapshot=_snapshot(
                "gs_clear_event",
                [_strategy("strategy_001", "sky=clear", "type=event")],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                required_keywords=["행사"],
            ),
        ),
        GoldenCase(
            case_id="gs_clear_tour",
            description="맑은 날 관광 소재 노출",
            snapshot=_snapshot(
                "gs_clear_tour",
                [_strategy("strategy_001", "sky=clear", "type=tour")],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                required_keywords=["관광"],
            ),
        ),
        GoldenCase(
            case_id="gs_weekend_only",
            description="주말 단독 조건 야외 전략",
            snapshot=_snapshot(
                "gs_weekend_only",
                [_strategy("strategy_001", "weekend=1", "category_group=outdoor")],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                required_keywords=["주말"],
            ),
        ),
        GoldenCase(
            case_id="gs_multi_three_mixed",
            description="날씨·주말 혼합 3전략",
            snapshot=_snapshot(
                "gs_multi_three_mixed",
                [
                    _strategy(
                        "strategy_001",
                        "sky=clear",
                        "category_group=outdoor",
                        strategy_score=0.45,
                    ),
                    _strategy(
                        "strategy_002",
                        "precip=rain",
                        "category_group=indoor",
                        strategy_score=0.41,
                    ),
                    _strategy(
                        "strategy_003",
                        "weekend=1",
                        "category_group=outdoor",
                        strategy_score=0.39,
                    ),
                ],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                required_keywords=["야외", "실내"],
            ),
        ),
        GoldenCase(
            case_id="gs_top_five_full",
            description="Top 5 전략 풀 로드",
            snapshot=_snapshot(
                "gs_top_five_full",
                [
                    _strategy(
                        "strategy_001",
                        "sky=clear",
                        "category_group=outdoor",
                        strategy_score=0.50,
                    ),
                    _strategy(
                        "strategy_002",
                        "precip=rain",
                        "category_group=indoor",
                        strategy_score=0.48,
                    ),
                    _strategy(
                        "strategy_003",
                        "weekend=1",
                        "category_group=outdoor",
                        strategy_score=0.46,
                    ),
                    _strategy(
                        "strategy_004",
                        "sky=cloudy",
                        "category_group=indoor",
                        strategy_score=0.44,
                    ),
                    _strategy(
                        "strategy_005",
                        "user_segment=segment_1",
                        "type=event",
                        strategy_score=0.42,
                    ),
                ],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
            ),
        ),
        GoldenCase(
            case_id="gs_high_lift",
            description="고 lift 전략 과장 금지",
            snapshot=_snapshot(
                "gs_high_lift",
                [
                    _strategy(
                        "strategy_001",
                        "sky=clear",
                        "category_group=outdoor",
                        lift=2.1,
                        strategy_score=0.55,
                    )
                ],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                forbidden_keywords=["100%", "무조건", "확실"],
            ),
        ),
        GoldenCase(
            case_id="gs_borderline_support",
            description="경계 support·confidence 보수적 서술",
            snapshot=_snapshot(
                "gs_borderline_support",
                [
                    _strategy(
                        "strategy_001",
                        "precip=rain",
                        "category_group=indoor",
                        support=0.051,
                        confidence=0.46,
                        lift=1.03,
                        strategy_score=0.35,
                    )
                ],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                forbidden_keywords=["반드시", "확정"],
            ),
        ),
        GoldenCase(
            case_id="gs_low_kpi_snapshot",
            description="낮은 전역 KPI에서 신중한 종합 제안",
            snapshot=_snapshot(
                "gs_low_kpi_snapshot",
                [_strategy("strategy_001", "sky=clear", "category_group=outdoor")],
                impression_count=800,
                user_count=40,
                ctr=0.03,
                cvr=0.05,
                ctcvr=0.002,
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                forbidden_keywords=["급격", "폭발"],
            ),
        ),
        GoldenCase(
            case_id="gs_empty_strategies",
            description="전략 0건 graceful 처리",
            snapshot=_snapshot("gs_empty_strategies", []),
            expectation=GoldenExpectation(expected_approved=False),
        ),
        GoldenCase(
            case_id="gs_metric_integrity",
            description="지표 정합 유지 (환각 방지)",
            snapshot=_snapshot(
                "gs_metric_integrity",
                [_strategy("strategy_001", "sky=clear", "category_group=outdoor")],
            ),
            expectation=GoldenExpectation(expected_approved=True),
        ),
        GoldenCase(
            case_id="gs_contradiction_rain",
            description="맑은 날 조건과 모순되는 비 서술 금지",
            snapshot=_snapshot(
                "gs_contradiction_rain",
                [_strategy("strategy_001", "sky=clear", "category_group=outdoor")],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                required_keywords=["맑"],
                forbidden_keywords=["비 오는", "눈 오는"],
            ),
        ),
        GoldenCase(
            case_id="gs_exaggeration_ban",
            description="과장 표현 금지",
            snapshot=_snapshot(
                "gs_exaggeration_ban",
                [_strategy("strategy_001", "sky=clear", "category_group=outdoor")],
            ),
            expectation=GoldenExpectation(
                expected_approved=True,
                forbidden_keywords=["무조건", "100%", "확실"],
            ),
        ),
    ]


def export_golden_cases(path: Path | None = None) -> Path:
    target = path or GOLDEN_CASES_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    cases = build_golden_cases()
    payload = {"version": 1, "cases": [case.model_dump() for case in cases]}
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def load_golden_cases(path: Path | None = None) -> list[GoldenCase]:
    target = path or GOLDEN_CASES_PATH
    if not target.exists():
        export_golden_cases(target)
    payload = json.loads(target.read_text(encoding="utf-8"))
    return [GoldenCase(**item) for item in payload["cases"]]
