# Dashboard 전략 표시 포맷 테스트
import pandas as pd

from app.dashboard.formatters import apply_natural_strategy_labels, build_strategy_display_table


def _sample_strategies_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "strategy_id": "strategy_001",
                "strategy_name": "precip=rain & weekend=0 -> category_group=indoor",
                "target_condition": "precip=rain & weekend=0",
                "recommended_action": "category_group=indoor",
                "expected_ctr_gain": 0.0715,
                "expected_cvr_gain": 0.0398,
                "support": 0.023,
                "confidence": 0.752,
                "lift": 1.058,
                "strategy_score": 0.296,
                "reason": "test",
            }
        ]
    )


def test_apply_natural_strategy_labels() -> None:
    labeled = apply_natural_strategy_labels(_sample_strategies_df())
    assert labeled.iloc[0]["target_condition"] == "비 오는 날, 평일"
    assert labeled.iloc[0]["recommended_action"] == "실내 콘텐츠 노출"
    assert "비 오는 날" in labeled.iloc[0]["strategy_name"]


def test_build_strategy_display_table_formats_metrics() -> None:
    table = build_strategy_display_table(
        _sample_strategies_df(),
        display_columns=[
            "strategy_name",
            "expected_ctr_gain",
            "lift",
            "target_condition",
        ],
    )
    assert table.iloc[0]["CTR 개선"] == "7.15%"
    assert table.iloc[0]["Lift"] == "1.058"
    assert "실내" in table.iloc[0]["상황 조건"] or "비" in table.iloc[0]["전략"]
