# raw JSON → 분석용 CSV 전처리
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

SOURCE_COLUMNS = [
    "TITLE",
    "CODENAME",
    "GUNAME",
    "PLACE",
    "DATE",
    "USE_FEE",
    "ORG_NAME",
    "PROGRAM",
    "HMPG_ADDR",
    "MAIN_IMG",
    "LOT",
    "LAT",
]

COLUMN_RENAME_MAP = {
    "TITLE": "title",
    "CODENAME": "codename",
    "GUNAME": "guname",
    "PLACE": "place",
    "DATE": "date_text",
    "USE_FEE": "use_fee",
    "ORG_NAME": "org_name",
    "PROGRAM": "program",
    "HMPG_ADDR": "hmpg_addr",
    "MAIN_IMG": "main_img",
    "LOT": "lot",
    "LAT": "lat",
}

DATE_RANGE_PATTERN = re.compile(
    r"(\d{4}[-./]\d{1,2}[-./]\d{1,2})\s*[~\-–]\s*(\d{4}[-./]\d{1,2}[-./]\d{1,2})"
)
SINGLE_DATE_PATTERN = re.compile(r"(\d{4}[-./]\d{1,2}[-./]\d{1,2})")

SEASON_MAP = {
    12: "winter",
    1: "winter",
    2: "winter",
    3: "spring",
    4: "spring",
    5: "spring",
    6: "summer",
    7: "summer",
    8: "summer",
    9: "fall",
    10: "fall",
    11: "fall",
}


def _parse_date_value(value: str | None) -> pd.Timestamp | None:
    # 문자열 → Timestamp
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    normalized = text.replace(".", "-").replace("/", "-")
    if len(normalized) == 8 and normalized.isdigit():
        normalized = f"{normalized[:4]}-{normalized[4:6]}-{normalized[6:8]}"

    parsed = pd.to_datetime(normalized, errors="coerce")
    if pd.isna(parsed):
        return None
    return pd.Timestamp(parsed.date())


def _split_date_text(date_text: str | None) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    # DATE 텍스트에서 시작일·종료일 분리
    if date_text is None or pd.isna(date_text):
        return None, None

    text = str(date_text).strip()
    if not text:
        return None, None

    range_match = DATE_RANGE_PATTERN.search(text)
    if range_match:
        return _parse_date_value(range_match.group(1)), _parse_date_value(range_match.group(2))

    single_match = SINGLE_DATE_PATTERN.search(text)
    if single_match:
        parsed = _parse_date_value(single_match.group(1))
        return parsed, parsed

    return None, None


def _resolve_start_end_dates(row: pd.Series) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    # START_DATE/END_DATE 우선, 없으면 DATE 파싱
    start = _parse_date_value(row.get("START_DATE") or row.get("STRTDATE"))
    end = _parse_date_value(row.get("END_DATE") or row.get("ENDDATE"))

    if start is not None or end is not None:
        return start, end

    return _split_date_text(row.get("DATE"))


def _infer_is_free(use_fee: str | None) -> bool | None:
    # use_fee에서 무료 여부 추론
    if use_fee is None or pd.isna(use_fee):
        return None

    text = str(use_fee).strip().lower()
    if not text:
        return None
    if "무료" in text or "free" in text:
        return True
    if "유료" in text or "원" in text:
        return False
    return None


def _has_text(value: object) -> bool:
    # 빈 문자열 여부
    if value is None or pd.isna(value):
        return False
    return bool(str(value).strip())


def _get_season(date_value: pd.Timestamp | None) -> str | None:
    # 시작일 기준 계절
    if date_value is None or pd.isna(date_value):
        return None
    return SEASON_MAP.get(int(date_value.month))


def transform_events(rows: list[dict]) -> pd.DataFrame:
    # 컬럼 정제 + feature 생성
    df = pd.DataFrame(rows)

    for column in SOURCE_COLUMNS:
        if column not in df.columns:
            df[column] = None

    df = df[SOURCE_COLUMNS].rename(columns=COLUMN_RENAME_MAP)

    start_dates: list[pd.Timestamp | None] = []
    end_dates: list[pd.Timestamp | None] = []
    for _, row in pd.DataFrame(rows).iterrows():
        start, end = _resolve_start_end_dates(row)
        start_dates.append(start)
        end_dates.append(end)

    df["start_date"] = start_dates
    df["end_date"] = end_dates
    df["is_free"] = df["use_fee"].apply(_infer_is_free)
    df["month"] = df["start_date"].apply(
        lambda value: int(value.month) if value is not None and not pd.isna(value) else None
    )
    df["weekday"] = df["start_date"].apply(
        lambda value: value.day_name().lower() if value is not None and not pd.isna(value) else None
    )
    df["season"] = df["start_date"].apply(_get_season)
    df["duration_days"] = df.apply(
        lambda row: (
            (row["end_date"] - row["start_date"]).days + 1
            if row["start_date"] is not None
            and row["end_date"] is not None
            and not pd.isna(row["start_date"])
            and not pd.isna(row["end_date"])
            else None
        ),
        axis=1,
    )
    df["has_image"] = df["main_img"].apply(_has_text)
    df["has_website"] = df["hmpg_addr"].apply(_has_text)

    return df


def load_raw_json(raw_path: Path) -> list[dict]:
    # raw JSON 로드
    with raw_path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("raw JSON은 리스트 형식이어야 합니다")
    return data


def save_processed_events(df: pd.DataFrame, output_dir: Path) -> Path:
    # data/processed/seoul_event/ 에 CSV 저장
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"seoul_events_{timestamp}.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("processed 저장 완료: %s (%s건)", output_path, len(df))
    return output_path


def transform_and_save(raw_path: Path, output_dir: Path) -> Path:
    # 전처리 + 저장 한 번에 실행
    rows = load_raw_json(raw_path)
    df = transform_events(rows)
    return save_processed_events(df, output_dir)
