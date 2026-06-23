# 전략 자연어 라벨 테스트
from app.analytics.strategy_labels import (
    format_clause_natural,
    format_strategy_line,
    format_strategy_natural,
)


def test_format_condition_natural() -> None:
    text = format_clause_natural("precip=rain & sky=overcast & weekend=0", for_action=False)
    assert "비 오는 날" in text
    assert "흐린 날" in text
    assert "평일" in text


def test_format_action_natural() -> None:
    text = format_clause_natural(
        "category_group=indoor & type=event",
        for_action=True,
    )
    assert "실내 콘텐츠 노출" in text
    assert "행사 소재 노출" in text


def test_format_strategy_line() -> None:
    text = format_strategy_line("precip=rain & weekend=0", "category_group=indoor")
    assert "비 오는 날" in text
    assert "실내 콘텐츠 노출" in text


def test_format_strategy_natural_includes_metrics() -> None:
    text = format_strategy_natural(
        "precip=rain & weekend=0",
        "category_group=indoor",
        support=0.023,
        confidence=0.752,
        lift=1.058,
    )
    assert "비 오는 날" in text
    assert "실내 콘텐츠 노출" in text
    assert "support 0.023" in text
    assert "lift 1.058" in text
