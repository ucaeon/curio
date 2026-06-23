# raw JSON → 분석용 CSV 전처리
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

SOURCE_COLUMNS = [
    "contentid",
    "contenttypeid",
    "title",
    "addr1",
    "addr2",
    "areacode",
    "sigungucode",
    "cat1",
    "cat2",
    "cat3",
    "mapx",
    "mapy",
    "firstimage",
    "firstimage2",
    "createdtime",
    "modifiedtime",
]

COLUMN_RENAME_MAP = {
    "contentid": "content_id",
    "contenttypeid": "content_type_id",
    "title": "title",
    "addr1": "address",
    "areacode": "area_code",
    "sigungucode": "sigungu_code",
    "cat1": "category_large",
    "cat2": "category_middle",
    "cat3": "category_small",
    "mapx": "longitude",
    "mapy": "latitude",
    "firstimage": "image_url",
    "firstimage2": "thumbnail_url",
    "createdtime": "created_time",
    "modifiedtime": "modified_time",
}

# contenttypeid → 관광 타입명
CONTENT_TYPE_MAP = {
    "12": "관광지",
    "14": "문화시설",
    "15": "축제공연행사",
    "25": "여행코스",
    "28": "레포츠",
    "32": "숙박",
    "38": "쇼핑",
    "39": "음식점",
}

# sigungucode → 서울 자치구명
SEOUL_DISTRICT_MAP = {
    "1": "종로구",
    "2": "중구",
    "3": "용산구",
    "4": "성동구",
    "5": "광진구",
    "6": "동대문구",
    "7": "중랑구",
    "8": "성북구",
    "9": "강북구",
    "10": "도봉구",
    "11": "노원구",
    "12": "은평구",
    "13": "서대문구",
    "14": "마포구",
    "15": "양천구",
    "16": "강서구",
    "17": "구로구",
    "18": "금천구",
    "19": "영등포구",
    "20": "동작구",
    "21": "관악구",
    "22": "서초구",
    "23": "강남구",
    "24": "송파구",
    "25": "강동구",
}


def _has_image(value: object) -> bool:
    # 이미지 URL 존재 여부
    if value is None or pd.isna(value):
        return False
    return bool(str(value).strip())


def transform_tour(items: list[dict]) -> pd.DataFrame:
    # 컬럼 정제 + feature 생성
    df = pd.DataFrame(items)

    for col in SOURCE_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df = df[SOURCE_COLUMNS].copy()

    # addr2는 address에 합쳐서 제거
    df["addr1"] = df.apply(
        lambda row: " ".join(
            filter(None, [str(row["addr1"] or "").strip(), str(row["addr2"] or "").strip()])
        ),
        axis=1,
    )
    df = df.drop(columns=["addr2"])

    df = df.rename(columns=COLUMN_RENAME_MAP)

    # 좌표 float 변환
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")

    # feature 생성
    df["has_image"] = df["image_url"].apply(_has_image)
    df["content_type_name"] = df["content_type_id"].apply(
        lambda v: CONTENT_TYPE_MAP.get(str(v).strip(), None) if pd.notna(v) else None
    )
    df["district"] = df["sigungu_code"].apply(
        lambda v: (
            SEOUL_DISTRICT_MAP.get(str(int(float(v))), None)
            if pd.notna(v) and str(v).strip()
            else None
        )
    )

    return df


def load_raw_json(raw_path: Path) -> list[dict]:
    # raw JSON 로드
    with raw_path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("raw JSON은 리스트 형식이어야 합니다")
    return data


def save_processed_tour(df: pd.DataFrame, output_dir: Path) -> Path:
    # data/processed/tour/ 에 CSV 저장
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"tour_{timestamp}.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("processed 저장 완료: %s (%s건)", output_path, len(df))
    return output_path


def transform_and_save(raw_path: Path, output_dir: Path) -> Path:
    # 전처리 + 저장 한 번에 실행
    items = load_raw_json(raw_path)
    df = transform_tour(items)
    return save_processed_tour(df, output_dir)
