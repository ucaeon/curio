# 한국관광공사 TourAPI
import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://apis.data.go.kr/B551011/KorService2/areaBasedList2"
SEOUL_AREA_CODE = "1"


class TourApiError(Exception):
    pass


def fetch_page(api_key: str, page_no: int, num_of_rows: int) -> dict[str, Any]:
    # 지정 페이지 관광 데이터 조회
    params = {
        "serviceKey": api_key,
        "MobileOS": "ETC",
        "MobileApp": "Curio",
        "_type": "json",
        "areaCode": SEOUL_AREA_CODE,
        "numOfRows": num_of_rows,
        "pageNo": page_no,
    }
    logger.info("API 요청: pageNo=%s, numOfRows=%s", page_no, num_of_rows)

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    body = payload.get("response", {}).get("body")
    if body is None:
        raise TourApiError("응답에 body 키가 없습니다")

    header = payload.get("response", {}).get("header", {})
    result_code = header.get("resultCode", "")
    if result_code != "0000":
        result_msg = header.get("resultMsg", "알 수 없는 오류")
        raise TourApiError(f"API 오류 [{result_code}]: {result_msg}")

    return body


def fetch_all(api_key: str, limit: int | None = None) -> list[dict[str, Any]]:
    # 페이지네이션으로 서울 관광 데이터 전체 수집
    first_body = fetch_page(api_key, page_no=1, num_of_rows=1)
    total_count = int(first_body.get("totalCount", 0))
    logger.info("전체 건수: %s", total_count)

    if total_count == 0:
        return []

    target_count = min(total_count, limit) if limit is not None else total_count
    page_size = 1000
    all_items: list[dict[str, Any]] = []

    page_no = 1
    while len(all_items) < target_count:
        body = fetch_page(api_key, page_no=page_no, num_of_rows=page_size)
        items_wrapper = body.get("items")
        if not items_wrapper:
            break

        items = items_wrapper.get("item", [])
        if isinstance(items, dict):
            items = [items]

        all_items.extend(items)
        logger.info("수집 진행: %s / %s", min(len(all_items), target_count), target_count)

        if len(all_items) >= total_count:
            break
        page_no += 1

    return all_items[:target_count]
