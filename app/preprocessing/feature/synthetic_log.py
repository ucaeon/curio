# synthetic 노출 로그 생성 (상황별 가중 샘플링)
import json
import logging
import random
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from app.analytics.metrics import compute_ctr, compute_cvr

logger = logging.getLogger(__name__)

SYNTHETIC_COLUMNS = [
    "impression_id",
    "user_id",
    "timestamp",
    "user_segment",
    "context_features",
    "creative_id",
    "clicked",
    "converted",
]

BASE_CTR = 0.08
BASE_CVR = 0.12
MAX_CTR = 0.5
DEFAULT_N_IMPRESSIONS = 10_000
DEFAULT_N_USERS = 500
SYNTHETIC_RANDOM_SEED = 42
UNASSIGNED_USER_SEGMENT = ""

OUTDOOR_KEYWORDS = ("축제", "관광", "레포츠", "여행코스")
INDOOR_KEYWORDS = ("전시", "음식점", "문화시설", "쇼핑", "교육", "영화", "연극", "클래식", "콘서트")

HIGH_CVR_KEYWORDS = ("음식점", "관광지")
MID_CVR_KEYWORDS = ("전시", "문화시설", "교육")
LOW_CVR_KEYWORDS = ("축제", "콘서트", "클래식", "뮤지컬", "연극")

CVR_HIGH = 0.15
CVR_MID = 0.12
CVR_LOW = 0.08

# 노출 가중치: Apriori co-occurrence 보정
WEIGHT_RAIN_WEEKDAY_INDOOR = 4.2
WEIGHT_RAIN_WEEKDAY_OUTDOOR = 0.4
WEIGHT_CLEAR_WEEKEND_OUTDOOR = 4.0
WEIGHT_CLEAR_WEEKEND_INDOOR = 0.6
WEIGHT_OVERCAST_WEEKDAY_INDOOR = 1.9
WEIGHT_OVERCAST_WEEKDAY_OUTDOOR = 0.85
WEIGHT_CONTEXT_SCENARIO_BOOST = 2.2
WEIGHT_NOISE_LOW = 0.72
WEIGHT_NOISE_HIGH = 1.28


@dataclass(frozen=True)
class UserProfile:
    outdoor_multiplier: float
    indoor_multiplier: float
    weekend_multiplier: float
    event_multiplier: float
    tour_multiplier: float
    free_multiplier: float


@dataclass(frozen=True)
class ContextFlags:
    is_weekend: bool
    rainy: bool
    clear: bool
    overcast: bool


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


def category_group(category: object) -> str:
    if is_outdoor_friendly(category):
        return "outdoor"
    if is_indoor_friendly(category):
        return "indoor"
    return "other"


def is_rainy(precipitation_type_name: object) -> bool:
    if precipitation_type_name is None or pd.isna(precipitation_type_name):
        return False
    return str(precipitation_type_name) not in {"none", ""}


def is_overcast_sky(sky_status_name: object) -> bool:
    if sky_status_name is None or pd.isna(sky_status_name):
        return False
    return str(sky_status_name) in {"overcast", "cloudy"}


def format_user_id(user_index: int) -> str:
    return f"user_{user_index + 1:04d}"


def build_user_profiles(n_users: int, rng: random.Random) -> list[UserProfile]:
    return [
        UserProfile(
            outdoor_multiplier=rng.uniform(0.88, 1.28),
            indoor_multiplier=rng.uniform(0.88, 1.28),
            weekend_multiplier=rng.uniform(0.92, 1.18),
            event_multiplier=rng.uniform(0.9, 1.15),
            tour_multiplier=rng.uniform(0.9, 1.15),
            free_multiplier=rng.uniform(0.96, 1.12),
        )
        for _ in range(n_users)
    ]


def assign_user_indices(n_impressions: int, n_users: int, rng: random.Random) -> list[int]:
    if n_users > n_impressions:
        raise ValueError(f"유저 수({n_users})는 impression 수({n_impressions}) 이하여야 합니다")

    counts = [1] * n_users
    for _ in range(n_impressions - n_users):
        counts[rng.randrange(n_users)] += 1

    user_indices: list[int] = []
    for user_index, count in enumerate(counts):
        user_indices.extend([user_index] * count)
    rng.shuffle(user_indices)
    return user_indices


def build_timestamp(fcst_date: object, fcst_time: object) -> datetime | None:
    if fcst_date is None or pd.isna(fcst_date) or fcst_time is None or pd.isna(fcst_time):
        return None

    date_text = str(int(fcst_date))
    time_text = str(int(fcst_time)).zfill(4)
    try:
        return datetime.strptime(f"{date_text}{time_text}", "%Y%m%d%H%M")
    except ValueError:
        return None


def get_context_flags(context_row: pd.Series) -> ContextFlags:
    sky = context_row.get("sky_status_name")
    precip = context_row.get("precipitation_type_name")
    timestamp = build_timestamp(context_row.get("fcst_date"), context_row.get("fcst_time"))
    is_weekend = timestamp is not None and timestamp.weekday() >= 5
    rainy = is_rainy(precip)
    clear = str(sky) == "clear" and not rainy
    overcast = is_overcast_sky(sky) and not rainy
    return ContextFlags(
        is_weekend=is_weekend,
        rainy=rainy,
        clear=clear,
        overcast=overcast,
    )


def format_context_features(context_row: pd.Series) -> str:
    fcst_date = context_row.get("fcst_date")
    timestamp = build_timestamp(fcst_date, context_row.get("fcst_time"))
    is_weekend = 0
    if timestamp is not None:
        is_weekend = int(timestamp.weekday() >= 5)

    temperature = context_row.get("temperature")
    temp_value = float(temperature) if pd.notna(temperature) else None

    payload = {
        "sky": context_row.get("sky_status_name"),
        "temp": temp_value,
        "precip": context_row.get("precipitation_type_name"),
        "weekend": is_weekend,
    }
    return json.dumps(payload, ensure_ascii=False)


def _apply_weight_noise(weight: float, rng: random.Random) -> float:
    return weight * rng.uniform(WEIGHT_NOISE_LOW, WEIGHT_NOISE_HIGH)


def compute_context_sampling_weight(context_row: pd.Series, rng: random.Random) -> float:
    # 목표 시나리오 context가 충분히 샘플링되도록 가중
    flags = get_context_flags(context_row)
    weight = 1.0
    if flags.rainy and not flags.is_weekend:
        weight *= WEIGHT_CONTEXT_SCENARIO_BOOST
    if flags.clear and flags.is_weekend:
        weight *= WEIGHT_CONTEXT_SCENARIO_BOOST
    if flags.overcast and not flags.is_weekend:
        weight *= 1.6
    return _apply_weight_noise(weight, rng)


def compute_creative_sampling_weight(
    category_group_label: str,
    flags: ContextFlags,
    rng: random.Random,
) -> float:
    # 상황:소재 co-occurrence 가중
    weight = 1.0
    if flags.rainy and not flags.is_weekend:
        if category_group_label == "indoor":
            weight = WEIGHT_RAIN_WEEKDAY_INDOOR
        elif category_group_label == "outdoor":
            weight = WEIGHT_RAIN_WEEKDAY_OUTDOOR
    elif flags.clear and flags.is_weekend:
        if category_group_label == "outdoor":
            weight = WEIGHT_CLEAR_WEEKEND_OUTDOOR
        elif category_group_label == "indoor":
            weight = WEIGHT_CLEAR_WEEKEND_INDOOR
    elif flags.overcast and not flags.is_weekend:
        if category_group_label == "indoor":
            weight = WEIGHT_OVERCAST_WEEKDAY_INDOOR
        elif category_group_label == "outdoor":
            weight = WEIGHT_OVERCAST_WEEKDAY_OUTDOOR

    return max(_apply_weight_noise(weight, rng), 0.05)


def sample_context_row(context_catalog: pd.DataFrame, rng: random.Random) -> pd.Series:
    weights = [
        compute_context_sampling_weight(context_catalog.iloc[index], rng)
        for index in range(len(context_catalog))
    ]
    chosen = rng.choices(range(len(context_catalog)), weights=weights, k=1)[0]
    return context_catalog.iloc[chosen]


def sample_creative_row(
    creative_catalog: pd.DataFrame,
    category_groups: list[str],
    context_row: pd.Series,
    rng: random.Random,
) -> pd.Series:
    flags = get_context_flags(context_row)
    weights = [compute_creative_sampling_weight(group, flags, rng) for group in category_groups]
    chosen = rng.choices(range(len(creative_catalog)), weights=weights, k=1)[0]
    return creative_catalog.iloc[chosen]


def compute_click_probability(
    creative_row: pd.Series,
    context_row: pd.Series,
    user_profile: UserProfile,
    rng: random.Random,
) -> float:
    flags = get_context_flags(context_row)
    category = creative_row.get("category")
    group = category_group(category)
    probability = BASE_CTR

    if flags.rainy and not flags.is_weekend and group == "indoor":
        probability *= 1.75 * user_profile.indoor_multiplier
    elif flags.clear and flags.is_weekend and group == "outdoor":
        probability *= 1.8 * user_profile.outdoor_multiplier
    elif flags.overcast and not flags.is_weekend and group == "indoor":
        probability *= 1.28 * user_profile.indoor_multiplier
    elif flags.rainy and group == "outdoor":
        probability *= 0.52
    elif flags.clear and flags.is_weekend and group == "indoor":
        probability *= 0.78

    if creative_row.get("has_image") is True:
        probability *= 1.08
    if creative_row.get("is_free") is True:
        probability *= 1.06 * user_profile.free_multiplier

    creative_type = creative_row.get("creative_type")
    if creative_type == "event":
        probability *= user_profile.event_multiplier
    elif creative_type == "tour":
        probability *= user_profile.tour_multiplier

    probability *= rng.uniform(0.9, 1.1)
    return min(probability, MAX_CTR)


def compute_conversion_probability(
    creative_row: pd.Series,
    context_row: pd.Series,
    rng: random.Random,
) -> float:
    category = creative_row.get("category")
    if category is None or pd.isna(category):
        probability = BASE_CVR
    else:
        text = str(category)
        if any(keyword in text for keyword in HIGH_CVR_KEYWORDS):
            probability = CVR_HIGH
        elif any(keyword in text for keyword in LOW_CVR_KEYWORDS):
            probability = CVR_LOW
        elif any(keyword in text for keyword in MID_CVR_KEYWORDS):
            probability = CVR_MID
        else:
            probability = BASE_CVR

    flags = get_context_flags(context_row)
    group = category_group(category)

    if flags.rainy and not flags.is_weekend and group == "indoor":
        probability *= 1.5
    elif flags.clear and flags.is_weekend and group == "outdoor":
        probability *= 1.45
    elif flags.overcast and not flags.is_weekend and group == "indoor":
        probability *= 1.18
    elif flags.rainy and group == "outdoor":
        probability *= 0.68

    probability *= rng.uniform(0.9, 1.1)
    return min(probability, 0.45)


def prepare_creative_catalog(creative_catalog: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    prepared = creative_catalog.reset_index(drop=True)
    groups = [category_group(value) for value in prepared["category"]]
    return prepared, groups


def generate_synthetic_log(
    creative_catalog: pd.DataFrame,
    context_catalog: pd.DataFrame,
    n_impressions: int = DEFAULT_N_IMPRESSIONS,
    n_users: int = DEFAULT_N_USERS,
) -> pd.DataFrame:
    rng = random.Random(SYNTHETIC_RANDOM_SEED)
    user_profiles = build_user_profiles(n_users, rng)
    user_indices = assign_user_indices(n_impressions, n_users, rng)
    creatives, category_groups = prepare_creative_catalog(creative_catalog)
    contexts = context_catalog.reset_index(drop=True)

    rows: list[dict[str, object]] = []
    for index in range(n_impressions):
        context_row = sample_context_row(contexts, rng)
        creative_row = sample_creative_row(creatives, category_groups, context_row, rng)
        user_profile = user_profiles[user_indices[index]]

        click_probability = compute_click_probability(
            creative_row,
            context_row,
            user_profile,
            rng,
        )
        conversion_probability = compute_conversion_probability(creative_row, context_row, rng)
        clicked = int(rng.random() < click_probability)
        converted = int(clicked and rng.random() < conversion_probability)

        timestamp = build_timestamp(context_row.get("fcst_date"), context_row.get("fcst_time"))
        rows.append(
            {
                "impression_id": f"imp_{index:06d}",
                "user_id": format_user_id(user_indices[index]),
                "timestamp": timestamp.isoformat(sep=" ") if timestamp else None,
                "user_segment": UNASSIGNED_USER_SEGMENT,
                "context_features": format_context_features(context_row),
                "creative_id": creative_row["creative_id"],
                "clicked": clicked,
                "converted": converted,
            }
        )

    log_df = pd.DataFrame(rows, columns=SYNTHETIC_COLUMNS)
    impressions_per_user = log_df.groupby("user_id").size()
    logger.info(
        "synthetic log 생성: %s건, 유저 %s명 (유저당 평균 %.1f건, CTR=%.4f, CVR=%.4f)",
        len(log_df),
        log_df["user_id"].nunique(),
        impressions_per_user.mean(),
        compute_ctr(log_df),
        compute_cvr(log_df),
    )
    return log_df


def save_synthetic_log(log_df: pd.DataFrame, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"synthetic_log_{timestamp}.csv"
    log_df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("synthetic log 저장 완료: %s (%s건)", output_path, len(log_df))
    return output_path


def generate_and_save_synthetic_log(
    creative_catalog: pd.DataFrame,
    context_catalog: pd.DataFrame,
    output_dir: Path,
    n_impressions: int = DEFAULT_N_IMPRESSIONS,
    n_users: int = DEFAULT_N_USERS,
) -> Path:
    log_df = generate_synthetic_log(
        creative_catalog=creative_catalog,
        context_catalog=context_catalog,
        n_impressions=n_impressions,
        n_users=n_users,
    )
    return save_synthetic_log(log_df, output_dir)
