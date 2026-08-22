"""Deterministic tool tests. Every number the user sees is checked here."""

from __future__ import annotations

import pytest

from shtrader_la.tools.position_sizing import PositionSizingEngine, pip_size_for
from shtrader_la.tools.registry import ToolRegistry
from shtrader_la.tools.risk_reward import RiskCalculator, RiskRewardCalculator
from shtrader_la.tools.trade_analysis import TradeAnalysisTool


# -- risk calculator --------------------------------------------------------


def test_risk_calculator_exact_amount() -> None:
    result = RiskCalculator().run(account_balance=10_000, risk_percent=1)
    assert result.ok
    assert result.data["max_risk_amount"] == pytest.approx(100.0)
    assert result.data["remaining_balance_if_stopped"] == pytest.approx(9_900.0)


def test_risk_calculator_warns_above_two_percent() -> None:
    result = RiskCalculator().run(account_balance=1_000, risk_percent=5)
    assert result.ok
    assert result.data["warnings"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"account_balance": 0, "risk_percent": 1},
        {"account_balance": 1000, "risk_percent": 0},
        {"account_balance": 1000, "risk_percent": 150},
        {"account_balance": "abc", "risk_percent": 1},
        {"risk_percent": 1},
    ],
)
def test_risk_calculator_rejects_bad_input(kwargs) -> None:
    result = RiskCalculator().run(**kwargs)
    assert not result.ok
    assert result.error


# -- risk/reward ------------------------------------------------------------


def test_risk_reward_long() -> None:
    result = RiskRewardCalculator().run(
        entry=100, stop_loss=95, take_profit=115, direction="BUY"
    )
    assert result.ok
    assert result.data["risk_reward"] == pytest.approx(3.0)
    assert result.data["meets_min_rr"] is True
    assert result.data["breakeven_win_rate_percent"] == pytest.approx(25.0, abs=0.01)


def test_risk_reward_short() -> None:
    result = RiskRewardCalculator().run(
        entry=100, stop_loss=105, take_profit=90, direction="SELL"
    )
    assert result.ok
    assert result.data["risk_reward"] == pytest.approx(2.0)


def test_risk_reward_direction_inferred() -> None:
    result = RiskRewardCalculator().run(entry=100, stop_loss=95, take_profit=110)
    assert result.ok
    assert result.data["direction"] == "BUY"


def test_risk_reward_rejects_stop_on_wrong_side() -> None:
    result = RiskRewardCalculator().run(
        entry=100, stop_loss=105, take_profit=120, direction="BUY"
    )
    assert not result.ok
    assert "stop" in (result.error or "").lower()


def test_risk_reward_rejects_target_on_wrong_side() -> None:
    result = RiskRewardCalculator().run(
        entry=100, stop_loss=95, take_profit=90, direction="BUY"
    )
    assert not result.ok
    assert "take profit" in (result.error or "").lower()


def test_risk_reward_below_minimum_is_flagged() -> None:
    result = RiskRewardCalculator().run(
        entry=100, stop_loss=95, take_profit=105, direction="BUY", min_rr=2
    )
    assert result.ok
    assert result.data["meets_min_rr"] is False


# -- position sizing --------------------------------------------------------


def test_linear_sizing_is_exact() -> None:
    result = PositionSizingEngine().run(
        account_balance=10_000, risk_percent=1, entry=100, stop_loss=95, method="linear"
    )
    assert result.ok
    # 100 risk / 5 stop distance = 20 units
    assert result.data["units"] == pytest.approx(20.0)


def test_forex_sizing_uses_pip_value() -> None:
    result = PositionSizingEngine().run(
        account_balance=10_000,
        risk_percent=1,
        entry=1.1000,
        stop_loss=1.0950,
        symbol="EUR/USD",
        pip_value_per_lot=10,
    )
    assert result.ok
    assert result.data["method"] == "forex"
    assert result.data["stop_pips"] == pytest.approx(50.0, abs=0.01)
    # 100 risk / (50 pips * 10) = 0.2 lots
    assert result.data["lots"] == pytest.approx(0.2, abs=0.001)


def test_forex_sizing_records_pip_value_assumption() -> None:
    result = PositionSizingEngine().run(
        account_balance=10_000, risk_percent=1, entry=1.1, stop_loss=1.095, symbol="EUR/USD"
    )
    assert result.ok
    assert result.data["assumptions"]


def test_zero_stop_distance_is_rejected() -> None:
    result = PositionSizingEngine().run(
        account_balance=10_000, risk_percent=1, entry=100, stop_loss=100
    )
    assert not result.ok


def test_pip_size_for_jpy_pairs() -> None:
    assert pip_size_for("USD/JPY") == pytest.approx(0.01)
    assert pip_size_for("EUR/USD") == pytest.approx(0.0001)
    assert pip_size_for(None) == pytest.approx(0.0001)


# -- composite analysis -----------------------------------------------------


def test_trade_analysis_full_setup() -> None:
    result = TradeAnalysisTool().run(
        text="long EUR/USD entry 1.1000 stop loss 1.0950 take profit 1.1150",
        context={"account_balance": 10_000, "risk_percent": 1, "pip_value_per_lot": 10},
    )
    assert result.ok
    assert result.data["risk_reward"] == pytest.approx(3.0, abs=0.01)
    assert result.data["max_risk_amount"] == pytest.approx(100.0)


def test_trade_analysis_needs_entry_and_stop() -> None:
    result = TradeAnalysisTool().run(text="i want to buy gold", context={})
    assert not result.ok


# -- registry ---------------------------------------------------------------


def test_registry_exposes_all_tools() -> None:
    registry = ToolRegistry()
    names = registry.names()
    for expected in (
        "risk_calculator",
        "risk_reward_calculator",
        "position_sizing",
        "trade_plan_parser",
        "trade_analysis",
    ):
        assert expected in names


def test_registry_unknown_tool_fails_safely() -> None:
    result = ToolRegistry().run("does_not_exist")
    assert not result.ok
    assert "unknown tool" in (result.error or "")


def test_registry_never_raises_on_bad_kwargs() -> None:
    result = ToolRegistry().run("risk_calculator", account_balance=None, risk_percent=None)
    assert not result.ok
