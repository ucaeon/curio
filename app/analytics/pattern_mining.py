# Apriori 기반 상황→소재 패턴 분석
import logging

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

from app.analytics.clustering import (
    enrich_log_with_features,
    is_indoor_friendly,
    is_outdoor_friendly,
)

logger = logging.getLogger(__name__)

MIN_SUPPORT = 0.01
MIN_CONFIDENCE = 0.15
MIN_LIFT = 1.02

CONTEXT_PREFIXES = ("sky_", "precip_", "weekend_")
CONTENT_PREFIXES = ("type_", "category_group_")


def category_group_label(category: object) -> str:
    # 카테고리를 outdoor/indoor/other 그룹으로 축약
    if is_outdoor_friendly(category):
        return "outdoor"
    if is_indoor_friendly(category):
        return "indoor"
    return "other"


def encode_impression_items(row: pd.Series) -> list[str]:
    # impression 1건을 Apriori 거래 아이템 리스트로 변환
    sky = row.get("sky")
    precip = row.get("precip")
    weekend = row.get("is_weekend")
    creative_type = row.get("creative_type")
    category = row.get("category")

    return [
        f"sky_{sky}",
        f"precip_{precip}",
        f"weekend_{int(weekend)}",
        f"type_{creative_type}",
        f"category_group_{category_group_label(category)}",
    ]


def build_transaction_dataframe(
    log_df: pd.DataFrame,
    creative_catalog: pd.DataFrame,
) -> pd.DataFrame:
    # impression → one-hot 거래 행렬
    enriched = enrich_log_with_features(log_df, creative_catalog)
    transactions = enriched.apply(encode_impression_items, axis=1).tolist()
    encoder = TransactionEncoder()
    encoded = encoder.fit(transactions).transform(transactions)
    return pd.DataFrame(encoded, columns=encoder.columns_)


def _is_context_item(item: str) -> bool:
    return item.startswith(CONTEXT_PREFIXES)


def _is_content_item(item: str) -> bool:
    return item.startswith(CONTENT_PREFIXES)


def _is_context_to_content_rule(antecedents: frozenset[str], consequents: frozenset[str]) -> bool:
    if not antecedents or not consequents:
        return False
    return all(_is_context_item(item) for item in antecedents) and all(
        _is_content_item(item) for item in consequents
    )


def mine_context_content_rules(
    transaction_df: pd.DataFrame,
    min_support: float = MIN_SUPPORT,
    min_confidence: float = MIN_CONFIDENCE,
    min_lift: float = MIN_LIFT,
) -> pd.DataFrame:
    # Apriori + Association Rule로 상황→소재 규칙 추출
    frequent_itemsets = apriori(transaction_df, min_support=min_support, use_colnames=True)
    if frequent_itemsets.empty:
        return pd.DataFrame()

    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=min_confidence,
    )
    if rules.empty:
        return pd.DataFrame()

    rules = rules[rules["lift"] >= min_lift].copy()
    context_content_mask = rules.apply(
        lambda row: _is_context_to_content_rule(row["antecedents"], row["consequents"]),
        axis=1,
    )
    rules = rules[context_content_mask].reset_index(drop=True)
    logger.info("연관 규칙 추출: %s건", len(rules))
    return rules


def mine_patterns(
    log_df: pd.DataFrame,
    creative_catalog: pd.DataFrame,
    min_support: float = MIN_SUPPORT,
    min_confidence: float = MIN_CONFIDENCE,
    min_lift: float = MIN_LIFT,
) -> pd.DataFrame:
    # log → 거래 행렬 → 상황→소재 규칙
    transaction_df = build_transaction_dataframe(log_df, creative_catalog)
    return mine_context_content_rules(
        transaction_df,
        min_support=min_support,
        min_confidence=min_confidence,
        min_lift=min_lift,
    )
