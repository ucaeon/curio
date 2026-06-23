# 유저 단위 KMeans 군집화
import json
import logging
from dataclasses import dataclass

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from app.analytics.metrics import compute_ctr, compute_cvr

logger = logging.getLogger(__name__)

OUTDOOR_KEYWORDS = ("축제", "관광", "레포츠", "여행코스")
INDOOR_KEYWORDS = ("전시", "음식점", "문화시설", "쇼핑", "교육", "영화", "연극", "클래식", "콘서트")

K_MIN = 3
K_MAX = 6
CLUSTER_RANDOM_STATE = 42

USER_FEATURE_COLUMNS = [
    "impression_count",
    "overall_ctr",
    "overall_cvr",
    "outdoor_ctr",
    "indoor_ctr",
    "weekend_ratio",
    "clear_weather_ctr",
    "rainy_weather_ctr",
    "event_ctr",
    "tour_ctr",
]


@dataclass(frozen=True)
class ClusteringResult:
    user_features: pd.DataFrame
    best_k: int
    silhouette_scores: dict[int, float]
    best_silhouette: float


def is_outdoor_friendly(category: object) -> bool:
    if category is None or pd.isna(category):
        return False
    text = str(category)
    return any(keyword in text for keyword in OUTDOOR_KEYWORDS)


def is_indoor_friendly(category: object) -> bool:
    if category is None or pd.isna(category):
        return False
    text = str(category)
    return any(keyword in text for keyword in INDOOR_KEYWORDS)


def is_rainy(precipitation: object) -> bool:
    if precipitation is None or pd.isna(precipitation):
        return False
    return str(precipitation) not in {"none", ""}


def parse_context_features(context_features: object) -> dict[str, object]:
    # context_features JSON 파싱
    if context_features is None or pd.isna(context_features):
        return {}
    if isinstance(context_features, dict):
        return context_features
    return json.loads(str(context_features))


def enrich_log_with_features(
    log_df: pd.DataFrame,
    creative_catalog: pd.DataFrame,
) -> pd.DataFrame:
    enriched = log_df.merge(
        creative_catalog[["creative_id", "creative_type", "category"]],
        on="creative_id",
        how="left",
    )
    context_df = enriched["context_features"].apply(parse_context_features).apply(pd.Series)
    enriched["sky"] = context_df.get("sky")
    enriched["precip"] = context_df.get("precip")
    enriched["is_weekend"] = context_df.get("weekend", 0).fillna(0).astype(int)
    enriched["is_outdoor"] = enriched["category"].apply(is_outdoor_friendly)
    enriched["is_indoor"] = enriched["category"].apply(is_indoor_friendly)
    enriched["is_clear"] = (enriched["sky"] == "clear") & ~enriched["precip"].apply(is_rainy)
    enriched["is_rainy"] = enriched["precip"].apply(is_rainy)
    return enriched


def _subset_ctr(subset_df: pd.DataFrame) -> float:
    if subset_df.empty:
        return 0.0
    return compute_ctr(subset_df)


def _subset_cvr(subset_df: pd.DataFrame) -> float:
    if subset_df.empty:
        return 0.0
    return compute_cvr(subset_df)


def build_user_features(
    log_df: pd.DataFrame,
    creative_catalog: pd.DataFrame,
) -> pd.DataFrame:
    enriched = enrich_log_with_features(log_df, creative_catalog)
    rows: list[dict[str, object]] = []

    for user_id, user_df in enriched.groupby("user_id", sort=True):
        rows.append(
            {
                "user_id": user_id,
                "impression_count": len(user_df),
                "overall_ctr": compute_ctr(user_df),
                "overall_cvr": _subset_cvr(user_df),
                "outdoor_ctr": _subset_ctr(user_df[user_df["is_outdoor"]]),
                "indoor_ctr": _subset_ctr(user_df[user_df["is_indoor"]]),
                "weekend_ratio": float(user_df["is_weekend"].mean()),
                "clear_weather_ctr": _subset_ctr(user_df[user_df["is_clear"]]),
                "rainy_weather_ctr": _subset_ctr(user_df[user_df["is_rainy"]]),
                "event_ctr": _subset_ctr(user_df[user_df["creative_type"] == "event"]),
                "tour_ctr": _subset_ctr(user_df[user_df["creative_type"] == "tour"]),
            }
        )

    return pd.DataFrame(rows)


def format_user_segment(cluster_id: int) -> str:
    return f"segment_{cluster_id}"


def find_best_k(
    feature_matrix: pd.DataFrame,
    k_min: int = K_MIN,
    k_max: int = K_MAX,
    random_state: int = CLUSTER_RANDOM_STATE,
) -> tuple[int, dict[int, float]]:
    # Silhouette Score로 k 탐색
    if len(feature_matrix) <= k_max:
        raise ValueError(f"유저 수({len(feature_matrix)})가 k_max({k_max})보다 커야 합니다")

    best_k = k_min
    best_score = -1.0
    silhouette_scores: dict[int, float] = {}

    for k in range(k_min, k_max + 1):
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(feature_matrix)
        model = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        cluster_labels = model.fit_predict(scaled_features)
        score = float(silhouette_score(scaled_features, cluster_labels))
        silhouette_scores[k] = score
        if score > best_score:
            best_score = score
            best_k = k

    return best_k, silhouette_scores


def fit_user_segments(
    user_features: pd.DataFrame,
    n_clusters: int,
    random_state: int = CLUSTER_RANDOM_STATE,
) -> pd.DataFrame:
    # KMeans 학습 후 user_segment 부여
    feature_matrix = user_features[USER_FEATURE_COLUMNS]
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(feature_matrix)
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    cluster_ids = model.fit_predict(scaled_features)

    result = user_features.copy()
    result["cluster_id"] = cluster_ids
    result["user_segment"] = result["cluster_id"].apply(format_user_segment)
    return result


def apply_user_segments(log_df: pd.DataFrame, segmented_users: pd.DataFrame) -> pd.DataFrame:
    # log에 user_segment 역매핑
    segment_map = segmented_users[["user_id", "user_segment"]]
    result = log_df.drop(columns=["user_segment"], errors="ignore").merge(
        segment_map,
        on="user_id",
        how="left",
    )
    return result


def cluster_users(
    log_df: pd.DataFrame,
    creative_catalog: pd.DataFrame,
    k_min: int = K_MIN,
    k_max: int = K_MAX,
    random_state: int = CLUSTER_RANDOM_STATE,
) -> tuple[ClusteringResult, pd.DataFrame]:
    # 유저 feature 생성 → k 선택 → 군집화 → log 역매핑
    user_features = build_user_features(log_df, creative_catalog)
    best_k, silhouette_scores = find_best_k(
        user_features[USER_FEATURE_COLUMNS],
        k_min=k_min,
        k_max=k_max,
        random_state=random_state,
    )
    segmented_users = fit_user_segments(user_features, n_clusters=best_k, random_state=random_state)
    segmented_log = apply_user_segments(log_df, segmented_users)

    best_silhouette = silhouette_scores[best_k]
    logger.info(
        "유저 군집화 완료: 유저 %s명, best_k=%s, silhouette=%.4f, scores=%s",
        len(segmented_users),
        best_k,
        best_silhouette,
        silhouette_scores,
    )

    result = ClusteringResult(
        user_features=segmented_users,
        best_k=best_k,
        silhouette_scores=silhouette_scores,
        best_silhouette=best_silhouette,
    )
    return result, segmented_log
