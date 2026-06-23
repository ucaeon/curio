# strategy engine 테스트
import pandas as pd

from app.analytics.pattern_mining import (
    build_transaction_dataframe,
    category_group_label,
    mine_context_content_rules,
)
from app.strategy.engine import compute_strategy_score, format_itemset, generate_top_strategies


def _sample_creative_catalog() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "creative_id": ["event_001", "tour_001"],
            "creative_type": ["event", "tour"],
            "category": ["축제", "음식점"],
        }
    )


def _sample_log() -> pd.DataFrame:
    rows = []
    for index in range(40):
        creative_id = "event_001" if index % 2 == 0 else "tour_001"
        context = (
            '{"sky": "clear", "temp": 25.0, "precip": "none", "weekend": 1}'
            if index % 3 != 0
            else '{"sky": "cloudy", "temp": 20.0, "precip": "rain", "weekend": 0}'
        )
        rows.append(
            {
                "impression_id": f"imp_{index:03d}",
                "user_id": f"user_{index % 5 + 1:04d}",
                "timestamp": "2026-06-17 12:00:00",
                "user_segment": "segment_0",
                "context_features": context,
                "creative_id": creative_id,
                "clicked": int(index % 4 == 0),
                "converted": int(index % 8 == 0),
            }
        )
    return pd.DataFrame(rows)


def test_category_group_label() -> None:
    assert category_group_label("축제") == "outdoor"
    assert category_group_label("음식점") == "indoor"
    assert category_group_label("기타") == "other"


def test_compute_strategy_score() -> None:
    score = compute_strategy_score(
        ctr_gain=0.05,
        cvr_gain=0.03,
        lift=2.0,
        confidence=0.6,
        max_lift=2.0,
    )
    expected = 0.35 * 0.05 + 0.35 * 0.03 + 0.15 * 1.0 + 0.15 * 0.6
    assert abs(score - expected) < 1e-9


def test_format_itemset() -> None:
    label = format_itemset(frozenset({"sky_clear", "weekend_1"}))
    assert "sky=clear" in label
    assert "weekend=1" in label


def test_mine_context_content_rules() -> None:
    transaction_df = build_transaction_dataframe(_sample_log(), _sample_creative_catalog())
    rules = mine_context_content_rules(
        transaction_df,
        min_support=0.05,
        min_confidence=0.1,
        min_lift=1.0,
    )
    assert not rules.empty
    assert {"support", "confidence", "lift"}.issubset(rules.columns)


def test_generate_top_strategies() -> None:
    strategies = generate_top_strategies(_sample_log(), _sample_creative_catalog(), top_n=3)
    assert len(strategies) <= 3
    assert {
        "strategy_id",
        "strategy_name",
        "target_condition",
        "recommended_action",
        "strategy_score",
    }.issubset(strategies.columns)
    if not strategies.empty:
        assert (strategies["expected_ctr_gain"] > 0).all()
        assert (strategies["expected_cvr_gain"] > 0).all()


def test_select_eligible_strategies_excludes_weak_cvr() -> None:
    from app.strategy.engine import STRATEGY_COLUMNS, _select_eligible_strategies

    rows = [
        {
            "strategy_id": "strategy_001",
            "strategy_name": "a",
            "target_condition": "sky=clear",
            "recommended_action": "category_group=outdoor",
            "expected_ctr_gain": 0.05,
            "expected_cvr_gain": 0.03,
            "support": 0.1,
            "confidence": 0.6,
            "lift": 1.2,
            "strategy_score": 0.5,
            "reason": "ok",
        },
        {
            "strategy_id": "strategy_002",
            "strategy_name": "b",
            "target_condition": "precip=rain",
            "recommended_action": "category_group=indoor",
            "expected_ctr_gain": 0.04,
            "expected_cvr_gain": 0.005,
            "support": 0.1,
            "confidence": 0.6,
            "lift": 1.1,
            "strategy_score": 0.4,
            "reason": "weak",
        },
    ]
    strategies = pd.DataFrame(rows, columns=STRATEGY_COLUMNS)
    selected = _select_eligible_strategies(strategies, top_n=5)
    assert len(selected) == 1
    assert selected.iloc[0]["strategy_id"] == "strategy_001"
