"""Router classification tests.

The router is rules-first, so every case here must pass with no model loaded.
"""

from __future__ import annotations

import pytest

from shtrader_la.core.router import Router, extract_signals
from shtrader_la.core.schemas import Intent


@pytest.fixture()
def router() -> Router:
    # No provider: pure deterministic rule behaviour.
    return Router(provider=None, use_llm_fallback=False)


@pytest.mark.parametrize(
    "query",
    [
        "what is risk reward",
        "what is risk reward?",
        "explain risk to reward ratio",
        "define position sizing",
        "teach me about market structure",
        "what does drawdown mean",
        "difference between a limit order and a stop order",
    ],
)
def test_conceptual_queries_route_to_knowledge(router: Router, query: str) -> None:
    assert router.classify(query).intent is Intent.KNOWLEDGE_QUERY


@pytest.mark.parametrize(
    "query",
    [
        "calculate my risk on a 5000 account risking 1%",
        "how much am i risking with a 10,000 balance at 2%",
        "what is my max risk on a $2,500 account at 1.5%",
        "risk per trade on a 5000 account at 1%",
    ],
)
def test_numeric_risk_queries_route_to_risk_calculation(router: Router, query: str) -> None:
    assert router.classify(query).intent is Intent.RISK_CALCULATION


@pytest.mark.parametrize(
    "query",
    [
        "position size for a 5000 account risking 1% entry 1.1000 stop 1.0950",
        "how many lots should i buy",
        "what lot size for my account",
    ],
)
def test_position_sizing_queries(router: Router, query: str) -> None:
    assert router.classify(query).intent is Intent.POSITION_SIZING


@pytest.mark.parametrize(
    "query",
    [
        "long EUR/USD entry 1.1000 stop loss 1.0950 take profit 1.1150",
        "review my trade: short BTC/USDT at 60000, sl 61000, tp 57000",
        "is this a good trade? entry 100 stop 95 target 115",
    ],
)
def test_trade_analysis_queries(router: Router, query: str) -> None:
    assert router.classify(query).intent is Intent.TRADE_ANALYSIS


def test_trading_plan_query(router: Router) -> None:
    decision = router.classify("build me a swing trading plan for gold")
    assert decision.intent is Intent.TRADING_PLAN


def test_empty_query_is_general(router: Router) -> None:
    decision = router.classify("   ")
    assert decision.intent is Intent.GENERAL_TRADING
    assert decision.source == "fallback"


def test_decision_is_serializable(router: Router) -> None:
    payload = router.classify("what is risk reward").to_dict()
    assert payload["intent"] == "knowledge_query"
    assert 0.0 <= payload["confidence"] <= 1.0
    assert payload["source"] in {"rules", "llm", "fallback"}


def test_signals_detect_money_and_percent() -> None:
    signals = extract_signals("calculate my risk on a 5000 account risking 1%")
    assert signals.money is True
    assert signals.percent is True
    assert signals.computational is True


def test_conceptual_signal_without_numbers_is_not_computational() -> None:
    signals = extract_signals("what is risk reward")
    assert signals.conceptual is True
    assert signals.computational is False
