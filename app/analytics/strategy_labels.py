# 자연어 라벨 변환
from __future__ import annotations

SKY_LABELS = {
    "clear": "맑은 날",
    "cloudy": "구름 많은 날",
    "overcast": "흐린 날",
}

PRECIP_LABELS = {
    "none": "강수 없음",
    "rain": "비 오는 날",
    "snow": "눈 오는 날",
    "shower": "소나기",
}

WEEKEND_LABELS = {
    "0": "평일",
    "1": "주말",
}

CATEGORY_GROUP_LABELS = {
    "indoor": "실내 콘텐츠",
    "outdoor": "야외 콘텐츠",
    "other": "기타 콘텐츠",
}

TYPE_LABELS = {
    "event": "행사 소재",
    "tour": "관광 소재",
}


def _parse_clause(clause: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for part in clause.split(" & "):
        token = part.strip()
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        pairs.append((key.strip(), value.strip()))
    return pairs


def _label_pair(key: str, value: str, *, for_action: bool) -> str:
    if key == "sky":
        return SKY_LABELS.get(value, f"하늘 {value}")
    if key == "precip":
        return PRECIP_LABELS.get(value, f"강수 {value}")
    if key == "weekend":
        return WEEKEND_LABELS.get(value, value)
    if key == "category_group":
        label = CATEGORY_GROUP_LABELS.get(value, value)
        return f"{label} 노출" if for_action else label
    if key == "type":
        label = TYPE_LABELS.get(value, value)
        return f"{label} 노출" if for_action else label
    return f"{key}={value}"


def format_clause_natural(clause: str, *, for_action: bool = False) -> str:
    pairs = _parse_clause(clause)
    if not pairs:
        return clause
    labels = [_label_pair(key, value, for_action=for_action) for key, value in pairs]
    separator = " · " if for_action else ", "
    return separator.join(labels)


def format_strategy_line(target_condition: str, recommended_action: str) -> str:
    situation = format_clause_natural(target_condition, for_action=False)
    action = format_clause_natural(recommended_action, for_action=True)
    return f"{situation} → {action}"


def format_strategy_natural(
    target_condition: str,
    recommended_action: str,
    *,
    support: float,
    confidence: float,
    lift: float,
) -> str:
    situation = format_clause_natural(target_condition, for_action=False)
    action = format_clause_natural(recommended_action, for_action=True)
    metrics = f"(support {support:.3f} · confidence {confidence:.3f} · lift {lift:.3f})"
    return f"{situation} → {action}\n   {metrics}"
