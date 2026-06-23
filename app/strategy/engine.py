# Strategy Score 계산 및 Top 전략 선정
import logging

import pandas as pd

from app.analytics.clustering import enrich_log_with_features
from app.analytics.metrics import compute_ctr, compute_cvr
from app.analytics.pattern_mining import encode_impression_items, mine_patterns

logger = logging.getLogger(__name__)

TOP_N_DEFAULT = 5

# Top 전략 선정 시 최소 품질 기준
MIN_EXPECTED_CTR_GAIN = 0.0
MIN_EXPECTED_CVR_GAIN = 0.01
MIN_STRATEGY_CONFIDENCE = 0.5
MIN_STRATEGY_CONFIDENCE_FALLBACK = 0.45
MIN_STRATEGY_LIFT = 1.02


def _select_eligible_strategies(strategies: pd.DataFrame, top_n: int) -> pd.DataFrame:
    # confidence tier로 Top N 채우기 (양수 CTR/CVR gain 유지)
    tiers = [MIN_STRATEGY_CONFIDENCE, MIN_STRATEGY_CONFIDENCE_FALLBACK]
    selected_indices: list[int] = []

    for min_confidence in tiers:
        if len(selected_indices) >= top_n:
            break
        mask = (
            (strategies["expected_ctr_gain"] > MIN_EXPECTED_CTR_GAIN)
            & (strategies["expected_cvr_gain"] > MIN_EXPECTED_CVR_GAIN)
            & (strategies["lift"] >= MIN_STRATEGY_LIFT)
            & (strategies["confidence"] >= min_confidence)
        )
        ranked = strategies[mask].sort_values("strategy_score", ascending=False)
        for index in ranked.index:
            if index in selected_indices:
                continue
            selected_indices.append(index)
            if len(selected_indices) >= top_n:
                break

    if not selected_indices:
        logger.warning("품질 기준 미달, 양수 gain 전략만 fallback")
        fallback = strategies[
            (strategies["expected_ctr_gain"] > MIN_EXPECTED_CTR_GAIN)
            & (strategies["expected_cvr_gain"] > MIN_EXPECTED_CVR_GAIN)
        ].sort_values("strategy_score", ascending=False)
        selected_indices = list(fallback.head(top_n).index)

    return strategies.loc[selected_indices].reset_index(drop=True)


STRATEGY_COLUMNS = [
    "strategy_id",
    "strategy_name",
    "target_condition",
    "recommended_action",
    "expected_ctr_gain",
    "expected_cvr_gain",
    "support",
    "confidence",
    "lift",
    "strategy_score",
    "reason",
]


def compute_strategy_score(
    ctr_gain: float,
    cvr_gain: float,
    lift: float,
    confidence: float,
    max_lift: float,
) -> float:
    normalized_lift = lift / max_lift if max_lift > 0 else 0.0
    return 0.35 * ctr_gain + 0.35 * cvr_gain + 0.15 * normalized_lift + 0.15 * confidence


def _format_item(item: str) -> str:
    if item.startswith("sky_"):
        return f"sky={item.removeprefix('sky_')}"
    if item.startswith("precip_"):
        return f"precip={item.removeprefix('precip_')}"
    if item.startswith("weekend_"):
        return f"weekend={item.removeprefix('weekend_')}"
    if item.startswith("type_"):
        return f"type={item.removeprefix('type_')}"
    if item.startswith("category_group_"):
        return f"category_group={item.removeprefix('category_group_')}"
    return item


def format_itemset(items: frozenset[str]) -> str:
    return " & ".join(_format_item(item) for item in sorted(items))


def impression_matches_rule(
    row: pd.Series,
    antecedents: frozenset[str],
    consequents: frozenset[str],
) -> bool:
    # impression이 규칙 antecedent·consequent를 모두 만족하는지 확인
    item_set = set(encode_impression_items(row))
    return antecedents.issubset(item_set) and consequents.issubset(item_set)


def evaluate_rule_performance(
    enriched_log: pd.DataFrame,
    antecedents: frozenset[str],
    consequents: frozenset[str],
) -> tuple[float, float]:
    # 규칙 조건 impression의 CTR/CVR gain
    baseline_ctr = compute_ctr(enriched_log)
    baseline_cvr = compute_cvr(enriched_log)
    mask = enriched_log.apply(
        lambda row: impression_matches_rule(row, antecedents, consequents),
        axis=1,
    )
    subset = enriched_log[mask]
    if subset.empty:
        return 0.0, 0.0
    return compute_ctr(subset) - baseline_ctr, compute_cvr(subset) - baseline_cvr


def build_strategies(
    rules_df: pd.DataFrame,
    enriched_log: pd.DataFrame,
    top_n: int = TOP_N_DEFAULT,
) -> pd.DataFrame:
    # 연관 규칙 → Strategy Score → Top N
    if rules_df.empty:
        return pd.DataFrame(columns=STRATEGY_COLUMNS)

    max_lift = float(rules_df["lift"].max())
    rows: list[dict[str, object]] = []

    for index, rule in rules_df.iterrows():
        antecedents = rule["antecedents"]
        consequents = rule["consequents"]
        ctr_gain, cvr_gain = evaluate_rule_performance(enriched_log, antecedents, consequents)
        support = float(rule["support"])
        confidence = float(rule["confidence"])
        lift = float(rule["lift"])
        target_condition = format_itemset(antecedents)
        recommended_action = format_itemset(consequents)
        strategy_score = compute_strategy_score(ctr_gain, cvr_gain, lift, confidence, max_lift)
        rows.append(
            {
                "strategy_id": f"strategy_{index + 1:03d}",
                "strategy_name": f"{target_condition} → {recommended_action}",
                "target_condition": target_condition,
                "recommended_action": recommended_action,
                "expected_ctr_gain": ctr_gain,
                "expected_cvr_gain": cvr_gain,
                "support": support,
                "confidence": confidence,
                "lift": lift,
                "strategy_score": strategy_score,
                "reason": (f"support={support:.3f}, confidence={confidence:.3f}, lift={lift:.3f}"),
            }
        )

    strategies = pd.DataFrame(rows, columns=STRATEGY_COLUMNS)
    strategies = strategies.drop_duplicates(
        subset=["target_condition", "recommended_action"],
        keep="first",
    )
    strategies = _select_eligible_strategies(strategies, top_n)
    strategies = strategies.reset_index(drop=True)
    logger.info("Top %s 전략 선정 완료", len(strategies))
    return strategies


def generate_top_strategies(
    log_df: pd.DataFrame,
    creative_catalog: pd.DataFrame,
    top_n: int = TOP_N_DEFAULT,
) -> pd.DataFrame:
    # 패턴 분석 → 전략 생성 파이프라인
    enriched_log = enrich_log_with_features(log_df, creative_catalog)
    rules_df = mine_patterns(log_df, creative_catalog)
    return build_strategies(rules_df, enriched_log, top_n=top_n)
