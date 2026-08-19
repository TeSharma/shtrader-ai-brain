"""Position sizing engine.

The interface is designed for the full problem (forex pip values, contract
sizes, account currency, leverage caps). The MVP implements two exact methods:

* `linear`  — units = risk_amount / price_distance. Correct for crypto, shares,
  and any instrument quoted in the account currency.
* `forex`   — lots = risk_amount / (stop_pips * pip_value_per_lot). Correct when
  pip value per standard lot is known in the account currency.

Anything requiring live FX conversion is explicitly reported as an assumption
rather than silently approximated.
"""

from __future__ import annotations

from typing import Any, Dict

from ..core.schemas import ToolResult
from .base import Tool

JPY_QUOTES = ("JPY",)


def pip_size_for(symbol: str | None) -> float:
    """0.01 for JPY-quoted pairs, else 0.0001. Used only for forex sizing."""
    if not symbol:
        return 0.0001
    normalized = symbol.upper().replace("/", "").replace("-", "").replace("_", "")
    return 0.01 if normalized.endswith(JPY_QUOTES) else 0.0001


class PositionSizingEngine(Tool):
    name = "position_sizing"
    description = (
        "Compute position size from account balance, risk percent and stop distance. "
        "Input: account_balance, risk_percent, entry, stop_loss, optional method "
        "('linear'|'forex'), symbol, pip_value_per_lot, leverage."
    )

    def run(self, **kwargs: Any) -> ToolResult:
        try:
            balance = self.positive(
                self.as_float(kwargs.get("account_balance"), "account_balance"),
                "account_balance",
            )
            risk_percent = self.positive(
                self.as_float(kwargs.get("risk_percent"), "risk_percent"), "risk_percent"
            )
            entry = self.positive(self.as_float(kwargs.get("entry"), "entry"), "entry")
            stop_loss = self.positive(
                self.as_float(kwargs.get("stop_loss"), "stop_loss"), "stop_loss"
            )
        except ValueError as exc:
            return self.fail(str(exc))

        if risk_percent > 100:
            return self.fail("'risk_percent' cannot exceed 100")

        distance = abs(entry - stop_loss)
        if distance == 0:
            return self.fail("Entry and stop loss cannot be equal — stop distance is zero.")

        risk_amount = balance * (risk_percent / 100.0)
        symbol = kwargs.get("symbol")
        method = (kwargs.get("method") or ("forex" if _looks_like_forex(symbol) else "linear")).lower()

        assumptions: list[str] = []
        data: Dict[str, Any]

        if method == "forex":
            pip = pip_size_for(symbol)
            stop_pips = distance / pip
            pip_value_per_lot = kwargs.get("pip_value_per_lot")
            if pip_value_per_lot is None:
                pip_value_per_lot = 10.0
                assumptions.append(
                    "Assumed a pip value of 10.00 account-currency units per standard "
                    "lot (true for USD-quoted pairs on a USD account). Supply "
                    "pip_value_per_lot for exact sizing on cross pairs."
                )
            try:
                pip_value_per_lot = self.positive(
                    self.as_float(pip_value_per_lot, "pip_value_per_lot"), "pip_value_per_lot"
                )
            except ValueError as exc:
                return self.fail(str(exc))

            lots = risk_amount / (stop_pips * pip_value_per_lot)
            units = lots * 100_000
            data = {
                "method": "forex",
                "stop_distance": round(distance, 8),
                "stop_pips": round(stop_pips, 2),
                "pip_size": pip,
                "pip_value_per_lot": pip_value_per_lot,
                "lots": round(lots, 4),
                "micro_lots": round(lots * 100, 1),
                "units": round(units, 2),
                "notional": round(units * entry, 2),
            }
            explanation = (
                f"Risk {risk_amount:,.2f} over {stop_pips:.1f} pips at "
                f"{pip_value_per_lot:g}/pip/lot -> {lots:.4f} lots."
            )
        else:
            units = risk_amount / distance
            data = {
                "method": "linear",
                "stop_distance": round(distance, 8),
                "units": round(units, 8),
                "notional": round(units * entry, 2),
            }
            explanation = (
                f"Risk {risk_amount:,.2f} / stop distance {distance:g} -> "
                f"{units:.6f} units."
            )

        leverage = kwargs.get("leverage")
        if leverage is not None:
            try:
                leverage = self.positive(self.as_float(leverage, "leverage"), "leverage")
            except ValueError as exc:
                return self.fail(str(exc))
            max_notional = balance * leverage
            data["leverage"] = leverage
            data["max_notional_at_leverage"] = round(max_notional, 2)
            data["within_leverage_limit"] = data["notional"] <= max_notional
            if not data["within_leverage_limit"]:
                assumptions.append(
                    f"Required notional {data['notional']:,.2f} exceeds the "
                    f"{leverage:g}x limit of {max_notional:,.2f}. Reduce size or widen "
                    "the stop."
                )

        data.update(
            {
                "account_balance": round(balance, 2),
                "risk_percent": risk_percent,
                "risk_amount": round(risk_amount, 2),
                "symbol": symbol,
                "assumptions": assumptions,
            }
        )
        return self.ok(data, explanation=explanation)


def _looks_like_forex(symbol: str | None) -> bool:
    if not symbol:
        return False
    normalized = symbol.upper().replace("/", "").replace("-", "").replace("_", "")
    if len(normalized) != 6:
        return False
    majors = {
        "USD", "EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD",
        "ZAR", "NGN", "KES", "GHS", "EGP", "MAD",
    }
    return normalized[:3] in majors and normalized[3:] in majors
