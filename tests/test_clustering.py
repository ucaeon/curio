# clustering 군집화 테스트
import pandas as pd

from app.analytics.clustering import (
    USER_FEATURE_COLUMNS,
    apply_user_segments,
    build_user_features,
    cluster_users,
    find_best_k,
    format_user_segment,
)


def _sample_creative_catalog() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "creative_id": ["event_001", "tour_001", "event_002"],
            "creative_type": ["event", "tour", "event"],
            "category": ["축제", "음식점", "전시"],
        }
    )


def _sample_log() -> pd.DataFrame:
    rows = []
    for user_index in range(12):
        user_id = f"user_{user_index + 1:04d}"
        for impression_index in range(5):
            creative_id = "event_001" if user_index % 2 == 0 else "tour_001"
            context = (
                '{"sky": "clear", "temp": 25.0, "precip": "none", "weekend": 1}'
                if impression_index % 2 == 0
                else '{"sky": "cloudy", "temp": 20.0, "precip": "rain", "weekend": 0}'
            )
            clicked = int((user_index + impression_index) % 3 == 0)
            converted = int(clicked and user_index % 4 == 0)
            rows.append(
                {
                    "impression_id": f"imp_{user_index:02d}{impression_index}",
                    "user_id": user_id,
                    "timestamp": "2026-06-17 12:00:00",
                    "user_segment": "",
                    "context_features": context,
                    "creative_id": creative_id,
                    "clicked": clicked,
                    "converted": converted,
                }
            )
    return pd.DataFrame(rows)


def test_build_user_features_shape() -> None:
    user_features = build_user_features(_sample_log(), _sample_creative_catalog())
    assert len(user_features) == 12
    assert set(USER_FEATURE_COLUMNS).issubset(user_features.columns)


def test_format_user_segment() -> None:
    assert format_user_segment(0) == "segment_0"
    assert format_user_segment(3) == "segment_3"


def test_find_best_k() -> None:
    user_features = build_user_features(_sample_log(), _sample_creative_catalog())
    best_k, scores = find_best_k(user_features[USER_FEATURE_COLUMNS], k_min=3, k_max=4)
    assert best_k in {3, 4}
    assert set(scores.keys()) == {3, 4}
    assert all(-1.0 <= score <= 1.0 for score in scores.values())


def test_apply_user_segments() -> None:
    log_df = _sample_log()
    user_features = build_user_features(log_df, _sample_creative_catalog())
    user_features["user_segment"] = "segment_0"
    segmented_log = apply_user_segments(log_df, user_features)
    assert segmented_log["user_segment"].eq("segment_0").all()


def test_cluster_users() -> None:
    result, segmented_log = cluster_users(
        _sample_log(),
        _sample_creative_catalog(),
        k_min=3,
        k_max=4,
    )
    assert result.best_k in {3, 4}
    assert len(result.user_features) == 12
    assert segmented_log["user_segment"].str.startswith("segment_").all()
    assert segmented_log["user_segment"].nunique() == result.best_k
