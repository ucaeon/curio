# 서울시 문화행사 Open API 클라이언트
import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

BASE_URL = "http://openapi.seoul.go.kr:8088"
SERVICE_NAME = "culturalEventInfo"
SUCCESS_CODE = "INFO-000"
PAGE_SIZE = 1000


class SeoulEventApiError(Exception):
    pass


def _normalize_rows(row: Any) -> list[dict[str, Any]]:
    # API row가 dict이면 list로 맞춤
    if row is None:
        return []
    if isinstance(row, dict):
        return [row]
    return list(row)


def fetch_page(api_key: str, start: int, end: int) -> dict[str, Any]:
    # 지정 범위 페이지 조회
    url = f"{BASE_URL}/{api_key}/json/{SERVICE_NAME}/{start}/{end}"
    logger.info("API 요청: start=%s, end=%s", start, end)

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()

    service_data = payload.get(SERVICE_NAME)
    if service_data is None:
        raise SeoulEventApiError(f"응답에 {SERVICE_NAME} 키가 없습니다")

    result = service_data.get("RESULT", {})
    code = result.get("CODE", "")
    if code != SUCCESS_CODE:
        message = result.get("MESSAGE", "알 수 없는 오류")
        raise SeoulEventApiError(f"API 오류 [{code}]: {message}")

    return service_data


def fetch_all(api_key: str, limit: int | None = None) -> list[dict[str, Any]]:
    # 1000건 단위 페이지네이션으로 전체 수집
    first_page = fetch_page(api_key, 1, 1)
    total_count = int(first_page.get("list_total_count", 0))
    logger.info("전체 건수: %s", total_count)

    if total_count == 0:
        return []

    target_count = min(total_count, limit) if limit is not None else total_count
    all_rows: list[dict[str, Any]] = []

    start_index = 1
    while start_index <= target_count:
        end_index = min(start_index + PAGE_SIZE - 1, target_count)
        page_data = fetch_page(api_key, start_index, end_index)
        rows = _normalize_rows(page_data.get("row"))
        all_rows.extend(rows)
        logger.info("수집 진행: %s / %s", len(all_rows), target_count)
        start_index = end_index + 1

    return all_rows
