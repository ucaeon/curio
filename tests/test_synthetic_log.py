# synthetic 가중 샘플링·성과 패턴 테스트
import pandas as pd

from app.analytics.clustering import enrich_log_with_features
from app.analytics.metrics import compute_ctr
from app.preprocessing.feature.synthetic_log import (
    category_group,
    generate_synthetic_log,
    get_context_flags,
)


def _mini_creative_catalog() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "creative_id": ["event_001", "tour_001", "event_002"],
            "creative_type": ["event", "tour", "event"],
            "title": ["축제", "맛집", "전시"],
            "district": ["강남", "종로", "마포"],
            "category": ["축제", "음식점", "전시"],
            "season": [None, None, None],
            "month": [6, 6, 6],
            "weekday": [5, 5, 1],
            "is_free": [True, False, True],
            "has_image": [True, True, True],
            "has_website": [True, True, False],
            "latitude": [37.5, 37.5, 37.5],
            "longitude": [127.0, 127.0, 127.0],
        }
    )


def _mini_context_catalog() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "context_id": "ctx_rain_weekday",
                "base_date": 20260601,
                "base_time": 800,
                "fcst_date": 20260603,
                "fcst_time": 1200,
                "temperature": 18.0,
                "sky_status": 4,
                "sky_status_name": "overcast",
                "precipitation_probability": 80,
                "precipitation_type": 1,
                "precipitation_type_name": "rain",
                "humidity": 90,
                "wind_speed": 2.0,
            },
            {
                "context_id": "ctx_clear_weekend",
                "base_date": 20260601,
                "base_time": 800,
                "fcst_date": 20260607,
                "fcst_time": 1400,
                "temperature": 26.0,
                "sky_status": 1,
                "sky_status_name": "clear",
                "precipitation_probability": 0,
                "precipitation_type": 0,
                "precipitation_type_name": "none",
                "humidity": 50,
                "wind_speed": 1.5,
            },
            {
                "context_id": "ctx_overcast_weekday",
                "base_date": 20260601,
                "base_time": 800,
                "fcst_date": 20260604,
                "fcst_time": 1500,
                "temperature": 22.0,
                "sky_status": 4,
                "sky_status_name": "cloudy",
                "precipitation_probability": 20,
                "precipitation_type": 0,
                "precipitation_type_name": "none",
                "humidity": 70,
                "wind_speed": 1.8,
            },
        ]
    )


def test_generate_synthetic_log_reproducible() -> None:
    creatives = _mini_creative_catalog()
    contexts = _mini_context_catalog()
    first = generate_synthetic_log(creatives, contexts, n_impressions=500, n_users=50)
    second = generate_synthetic_log(creatives, contexts, n_impressions=500, n_users=50)
    assert first["clicked"].tolist() == second["clicked"].tolist()
    assert first["creative_id"].tolist() == second["creative_id"].tolist()


def test_weighted_patterns_raise_target_ctr() -> None:
    creatives = _mini_creative_catalog()
    contexts = _mini_context_catalog()
    log_df = generate_synthetic_log(creatives, contexts, n_impressions=4000, n_users=200)
    enriched = enrich_log_with_features(log_df, creatives)

    rain_weekday = enriched[
        enriched["precip"].apply(lambda value: str(value) not in {"none", ""})
        & (enriched["is_weekend"] == 0)
    ]
    is_indoor = rain_weekday["category"].apply(lambda c: category_group(c) == "indoor")
    is_outdoor = rain_weekday["category"].apply(lambda c: category_group(c) == "outdoor")
    indoor_rain = rain_weekday[is_indoor]
    outdoor_rain = rain_weekday[is_outdoor]
    assert compute_ctr(indoor_rain) > compute_ctr(outdoor_rain)

    clear_weekend = enriched[(enriched["sky"] == "clear") & (enriched["is_weekend"] == 1)]
    outdoor_clear = clear_weekend[
        clear_weekend["category"].apply(lambda c: category_group(c) == "outdoor")
    ]
    indoor_clear = clear_weekend[
        clear_weekend["category"].apply(lambda c: category_group(c) == "indoor")
    ]
    assert compute_ctr(outdoor_clear) > compute_ctr(indoor_clear)

    overcast_weekday = enriched[
        (enriched["sky"].isin(["overcast", "cloudy"]))
        & (enriched["is_weekend"] == 0)
        & (enriched["precip"].apply(lambda value: str(value) in {"none", ""}))
    ]
    if not overcast_weekday.empty:
        indoor_overcast = overcast_weekday[
            overcast_weekday["category"].apply(lambda c: category_group(c) == "indoor")
        ]
        outdoor_overcast = overcast_weekday[
            overcast_weekday["category"].apply(lambda c: category_group(c) == "outdoor")
        ]
        if not indoor_overcast.empty and not outdoor_overcast.empty:
            assert compute_ctr(indoor_overcast) >= compute_ctr(outdoor_overcast)


def test_context_flags_for_scenarios() -> None:
    contexts = _mini_context_catalog()
    rain_flags = get_context_flags(contexts.iloc[0])
    assert rain_flags.rainy is True
    assert rain_flags.is_weekend is False

    clear_flags = get_context_flags(contexts.iloc[1])
    assert clear_flags.clear is True
    assert clear_flags.is_weekend is True
