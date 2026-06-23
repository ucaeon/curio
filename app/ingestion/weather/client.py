# 기상청 단기예보 API 클라이언트
import logging
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
SUCCESS_CODE = "00"
PAGE_SIZE = 1000
KST = ZoneInfo("Asia/Seoul")
BASE_TIMES = ("0200", "0500", "0800", "1100", "1400", "1700", "2000", "2300")


class WeatherApiError(Exception):
    pass


def get_latest_base_datetime() -> tuple[str, str]:
    # 발표 시각 기준 최신 base_date, base_time 계산
    now = datetime.now(KST)

    for base_time in reversed(BASE_TIMES):
        hour = int(base_time[:2])
        minute = int(base_time[2:])
        base_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now >= base_dt + timedelta(minutes=40):
            return base_dt.strftime("%Y%m%d"), base_time

    yesterday = now - timedelta(days=1)
    return yesterday.strftime("%Y%m%d"), "2300"


def _normalize_items(items: Any) -> list[dict[str, Any]]:
    # API item이 dict이면 list로 맞춤
    if items is None:
        return []
    if isinstance(items, dict):
        return [items]
    return list(items)


def fetch_page(
    api_key: str,
    base_date: str,
    base_time: str,
    nx: int,
    ny: int,
    page_no: int,
    num_of_rows: int,
) -> dict[str, Any]:

    params = {
        "serviceKey": api_key,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }
    logger.info(
        "API 요청: base_date=%s, base_time=%s, pageNo=%s, nx=%s, ny=%s",
        base_date,
        base_time,
        page_no,
        nx,
        ny,
    )

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    header = payload.get("response", {}).get("header", {})
    result_code = header.get("resultCode", "")
    if result_code != SUCCESS_CODE:
        result_msg = header.get("resultMsg", "알 수 없는 오류")
        raise WeatherApiError(f"API 오류 [{result_code}]: {result_msg}")

    body = payload.get("response", {}).get("body")
    if body is None:
        raise WeatherApiError("응답에 body 키가 없습니다")

    return body


def fetch_all(
    api_key: str,
    nx: int = 60,
    ny: int = 127,
    base_date: str | None = None,
    base_time: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    # 페이지네이션으로 단기예보 전체 수집
    if base_date is None or base_time is None:
        base_date, base_time = get_latest_base_datetime()

    logger.info("기준 시각: base_date=%s, base_time=%s", base_date, base_time)

    first_body = fetch_page(api_key, base_date, base_time, nx, ny, page_no=1, num_of_rows=1)
    total_count = int(first_body.get("totalCount", 0))
    logger.info("전체 건수: %s", total_count)

    if total_count == 0:
        return []

    target_count = min(total_count, limit) if limit is not None else total_count
    all_items: list[dict[str, Any]] = []

    page_no = 1
    while len(all_items) < target_count:
        body = fetch_page(
            api_key, base_date, base_time, nx, ny, page_no=page_no, num_of_rows=PAGE_SIZE
        )
        items_wrapper = body.get("items")
        if not items_wrapper:
            break

        items = _normalize_items(items_wrapper.get("item"))
        all_items.extend(items)
        logger.info("수집 진행: %s / %s", min(len(all_items), target_count), target_count)

        if len(all_items) >= total_count:
            break
        page_no += 1

    return all_items[:target_count]
