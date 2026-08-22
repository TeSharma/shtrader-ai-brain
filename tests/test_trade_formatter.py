"""Parser tests, including the regression guard for fabricated symbols."""

from __future__ import annotations

import pytest

from shtrader_la.core.schemas import Side
from shtrader_la.tools.trade_formatter import extract_symbol, parse_trade_text


@pytest.mark.parametrize(
    "text, expected",
    [
        ("long EUR/USD", "EUR/USD"),
        ("buy EURUSD now", "EUR/USD"),
        ("short XAU/USD", "XAU/USD"),
        ("XAUUSD setup", "XAUUSD"),
        ("BTC-USDT breakout", "BTC/USDT"),
        ("scaling into BTC", "BTC/USD"),
        ("US30 long", "US30"),
    ],
)
def test_real_symbols_are_recognized(text: str, expected: str) -> None:
    assert extract_symbol(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "what is market structure",
        "explain risk reward",
        "the market is trending higher",
        "should i target a wider stop",
        "i need a trade review please",
        "link me the position sizing doc",
        "how much am i risking on a 5000 account",
    ],
)
def test_prose_never_produces_a_symbol(text: str) -> None:
    assert extract_symbol(text) is None
    assert parse_trade_text(text).symbol is None


def test_full_trade_idea_parse() -> None:
    idea = parse_trade_text(
        "long EUR/USD entry 1.1000, stop loss 1.0950, take profit 1.1150, "
        "risk 1% of my 10,000 account"
    )
    assert idea.symbol == "EUR/USD"
    assert idea.side is Side.BUY
    assert idea.entry == pytest.approx(1.1000)
    assert idea.stop_loss == pytest.approx(1.0950)
    assert idea.take_profit == pytest.approx(1.1150)
    assert idea.risk_percent == pytest.approx(1.0)
    assert idea.account_balance == pytest.approx(10000.0)


def test_side_inferred_from_stop_placement() -> None:
    idea = parse_trade_text("entry 100 stop loss 95 take profit 115")
    assert idea.side is Side.BUY


def test_short_side_inferred() -> None:
    idea = parse_trade_text("entry 100, sl 105, tp 85")
    assert idea.side is Side.SELL


def test_risk_percent_does_not_leak_into_price_fields() -> None:
    idea = parse_trade_text("risk 2% on my account")
    assert idea.risk_percent == pytest.approx(2.0)
    assert idea.entry is None
    assert idea.stop_loss is None
