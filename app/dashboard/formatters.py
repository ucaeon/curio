# Dashboard 전략 표시 포맷
import pandas as pd

from app.analytics.strategy_labels import (
    format_clause_natural,
    format_strategy_line,
)

PERCENT_COLUMNS = ("expected_ctr_gain", "expected_cvr_gain")
RATIO_COLUMNS = ("support", "confidence", "strategy_score")

DISPLAY_COLUMN_LABELS = {
    "strategy_name": "전략",
    "strategy_score": "전략 점수",
    "expected_ctr_gain": "CTR 개선",
    "expected_cvr_gain": "CVR 개선",
    "support": "Support",
    "confidence": "Confidence",
    "lift": "Lift",
    "target_condition": "상황 조건",
    "recommended_action": "추천 액션",
    "operational_reason": "운영 제안",
}

ANALYSIS_DISPLAY_COLUMNS = [
    "strategy_name",
    "strategy_score",
    "expected_ctr_gain",
    "expected_cvr_gain",
    "support",
    "confidence",
    "lift",
    "target_condition",
    "recommended_action",
]

AGENT_DISPLAY_COLUMNS = [
    "strategy_name",
    "target_condition",
    "recommended_action",
    "strategy_score",
    "expected_ctr_gain",
    "expected_cvr_gain",
    "operational_reason",
]


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def apply_natural_strategy_labels(strategies: pd.DataFrame) -> pd.DataFrame:
    if strategies.empty:
        return strategies

    labeled = strategies.copy()
    labeled["target_condition"] = labeled["target_condition"].map(
        lambda value: format_clause_natural(str(value), for_action=False)
    )
    labeled["recommended_action"] = labeled["recommended_action"].map(
        lambda value: format_clause_natural(str(value), for_action=True)
    )
    labeled["strategy_name"] = [
        format_strategy_line(str(target), str(action))
        for target, action in zip(
            strategies["target_condition"],
            strategies["recommended_action"],
            strict=True,
        )
    ]
    return labeled


def build_strategy_display_table(
    strategies: pd.DataFrame,
    display_columns: list[str],
    column_labels: dict[str, str] | None = None,
) -> pd.DataFrame:
    if strategies.empty:
        return strategies

    labels = column_labels or DISPLAY_COLUMN_LABELS
    display_df = apply_natural_strategy_labels(strategies)[display_columns].copy()

    for column in PERCENT_COLUMNS:
        if column in display_df.columns:
            display_df[column] = display_df[column].map(format_percent)
    for column in RATIO_COLUMNS:
        if column in display_df.columns:
            display_df[column] = display_df[column].map(lambda value: f"{value:.3f}")
    if "lift" in display_df.columns:
        display_df["lift"] = strategies["lift"].map(lambda value: f"{value:.3f}")

    return display_df.rename(columns=labels)
