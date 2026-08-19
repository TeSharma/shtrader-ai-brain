"""Account risk and risk/reward calculators. Pure arithmetic, no model."""

from __future__ import annotations

from typing import Any

from ..core.schemas import Side, ToolResult
from .base import Tool

DEFAULT_MIN_RR = 2.0


def _round(value: float, digits: int = 6) -> float:
    return round(value, digits)


class RiskCalculator(Tool):
    name = "risk_calculator"
    description = (
        "Compute the maximum capital at risk for a trade from account balance and "
        "risk percentage. Input: account_balance, risk_percent."
    )

    def run(self, **kwargs: Any) -> ToolResult:
        try:
            balance = self.positive(self.as_float(kwargs.get("account_balance"), "account_balance"), "account_balance")
            risk_percent = self.as_float(kwargs.get("risk_percent"), "risk_percent")
        except ValueError as exc:
            return self.fail(str(exc))

        if risk_percent <= 0:
            return self.fail("'risk_percent' must be greater than zero")
        if risk_percent > 100:
            return self.fail("'risk_percent' cannot exceed 100")

        max_risk = balance * (risk_percent / 100.0)
        warnings = []
        if risk_percent > 2:
            warnings.append(
                f"{risk_percent:g}% per trade is above the 1-2% band most risk "
                "frameworks consider survivable."
            )

        return self.ok(
            {
                "account_balance": _round(balance, 2),
                "risk_percent": risk_percent,
                "max_risk_amount": _round(max_risk, 2),
                "remaining_balance_if_stopped": _round(balance - max_risk, 2),
                "warnings": warnings,
            },
            explanation=(
                f"{risk_percent:g}% of {balance:,.2f} = {max_risk:,.2f} maximum capital at risk."
            ),
        )


class RiskRewardCalculator(Tool):
    name = "risk_reward_calculator"
    description = (
        "Compute risk distance, reward distance and risk/reward ratio. "
        "Input: entry, stop_loss, take_profit, direction (BUY/SELL), optional min_rr."
    )

    def run(self, **kwargs: Any) -> ToolResult:
        try:
            entry = self.as_float(kwargs.get("entry"), "entry")
            stop_loss = self.as_float(kwargs.get("stop_loss"), "stop_loss")
            take_profit = self.as_float(kwargs.get("take_profit"), "take_profit")
        except ValueError as exc:
            return self.fail(str(exc))

        raw_direction = kwargs.get("direction") or kwargs.get("side")
        side = _coerce_side(raw_direction, entry, stop_loss)
        if side is None:
            return self.fail(
                "'direction' must be BUY/LONG or SELL/SHORT, and could not be inferred."
            )

        min_rr = kwargs.get("min_rr", DEFAULT_MIN_RR)
        try:
            min_rr = self.as_float(min_rr, "min_rr")
        except ValueError as exc:
            return self.fail(str(exc))

        if side.is_long:
            risk = entry - stop_loss
            reward = take_profit - entry
        else:
            risk = stop_loss - entry
            reward = entry - take_profit

        if risk <= 0:
            return self.fail(
                "Invalid stop loss: for a "
                f"{side.value} the stop must sit on the losing side of entry "
                f"({'below' if side.is_long else 'above'} {entry:g})."
            )
        if reward <= 0:
            return self.fail(
                "Invalid take profit: for a "
                f"{side.value} the target must sit on the winning side of entry "
                f"({'above' if side.is_long else 'below'} {entry:g})."
            )

        rr = reward / risk
        breakeven_win_rate = 1.0 / (1.0 + rr) * 100.0

        return self.ok(
            {
                "direction": side.value,
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_distance": _round(risk),
                "reward_distance": _round(reward),
                "risk_reward": _round(rr, 4),
                "min_rr": min_rr,
                "meets_min_rr": rr >= min_rr,
                "breakeven_win_rate_percent": _round(breakeven_win_rate, 2),
            },
            explanation=(
                f"Risk {risk:g}, reward {reward:g} -> R:R {rr:.2f}. "
                f"Breakeven win rate {breakeven_win_rate:.1f}%. "
                f"{'Meets' if rr >= min_rr else 'Below'} the {min_rr:g}:1 minimum."
            ),
        )


def _coerce_side(raw: Any, entry: float, stop_loss: float) -> Side | None:
    """Accept several spellings; fall back to inferring from stop placement."""
    if isinstance(raw, Side):
        return raw
    if isinstance(raw, str):
        token = raw.strip().upper()
        if token in {"BUY", "LONG", "B"}:
            return Side.BUY
        if token in {"SELL", "SHORT", "S"}:
            return Side.SELL
    if raw in (None, ""):
        if stop_loss < entry:
            return Side.BUY
        if stop_loss > entry:
            return Side.SELL
    return None
