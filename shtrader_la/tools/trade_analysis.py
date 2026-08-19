"""Composite trade analysis: parse -> risk -> R:R -> sizing -> verdict.

Everything numeric here is deterministic. The LLM only narrates the result.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.schemas import Side, ToolResult, TradeIdea
from .base import Tool
from .position_sizing import PositionSizingEngine
from .risk_reward import DEFAULT_MIN_RR, RiskCalculator, RiskRewardCalculator
from .trade_formatter import parse_trade_text


class TradeAnalysisTool(Tool):
    name = "trade_analysis"
    description = (
        "Full deterministic analysis of a trade idea: parses free text and/or "
        "explicit context, then computes account risk, risk/reward and position size."
    )

    def __init__(self) -> None:
        self.risk = RiskCalculator()
        self.rr = RiskRewardCalculator()
        self.sizing = PositionSizingEngine()

    def run(self, **kwargs: Any) -> ToolResult:
        idea = _merge_idea(kwargs)
        if idea.entry is None or idea.stop_loss is None:
            return self.fail(
                "Need at least an entry and a stop loss to analyse a trade. "
                "Provide them in the text or in context."
            )

        checks: Dict[str, Any] = {}
        warnings: List[str] = []
        recommendations: List[str] = []
        min_rr = float(kwargs.get("min_rr", DEFAULT_MIN_RR))

        # Risk/reward (requires a take profit)
        rr_data: Optional[Dict[str, Any]] = None
        if idea.take_profit is not None:
            rr_result = self.rr.run(
                entry=idea.entry,
                stop_loss=idea.stop_loss,
                take_profit=idea.take_profit,
                direction=idea.side.value if idea.side else None,
                min_rr=min_rr,
            )
            if not rr_result.ok:
                return self.fail(rr_result.error or "risk/reward calculation failed")
            rr_data = rr_result.data
            checks["risk_reward"] = rr_data
            if not rr_data["meets_min_rr"]:
                recommendations.append(
                    f"R:R of {rr_data['risk_reward']:.2f} is below the {min_rr:g}:1 "
                    "minimum — widen the target, tighten the stop, or skip the trade."
                )
            else:
                recommendations.append(
                    f"R:R of {rr_data['risk_reward']:.2f} clears the {min_rr:g}:1 "
                    f"minimum; you only need a {rr_data['breakeven_win_rate_percent']:.0f}% "
                    "win rate to break even."
                )
        else:
            warnings.append("No take profit supplied — risk/reward could not be computed.")

        # Account risk + sizing (require balance and risk %)
        if idea.account_balance is not None and idea.risk_percent is not None:
            risk_result = self.risk.run(
                account_balance=idea.account_balance, risk_percent=idea.risk_percent
            )
            if risk_result.ok:
                checks["account_risk"] = risk_result.data
                warnings.extend(risk_result.data.get("warnings", []))
            else:
                warnings.append(risk_result.error or "account risk calculation failed")

            size_result = self.sizing.run(
                account_balance=idea.account_balance,
                risk_percent=idea.risk_percent,
                entry=idea.entry,
                stop_loss=idea.stop_loss,
                symbol=idea.symbol,
                method=kwargs.get("method"),
                pip_value_per_lot=kwargs.get("pip_value_per_lot"),
                leverage=kwargs.get("leverage"),
            )
            if size_result.ok:
                checks["position_size"] = size_result.data
                warnings.extend(size_result.data.get("assumptions", []))
            else:
                warnings.append(size_result.error or "position sizing failed")
        else:
            recommendations.append(
                "Supply your account balance and risk percentage to get an exact "
                "position size."
            )

        structured = {
            "symbol": idea.symbol,
            "direction": idea.side.value if idea.side else None,
            "entry": idea.entry,
            "stop_loss": idea.stop_loss,
            "take_profit": idea.take_profit,
            "risk_percent": idea.risk_percent,
            "account_balance": idea.account_balance,
            "risk_reward": rr_data["risk_reward"] if rr_data else None,
            "meets_min_rr": rr_data["meets_min_rr"] if rr_data else None,
            "position_size": checks.get("position_size", {}).get("units"),
            "max_risk_amount": checks.get("account_risk", {}).get("max_risk_amount"),
            "checks": checks,
            "warnings": warnings,
            "recommendations": recommendations,
        }
        return self.ok(structured, explanation=_summary_line(structured))


def _merge_idea(kwargs: Dict[str, Any]) -> TradeIdea:
    """Explicit context wins over text-parsed values."""
    text = kwargs.get("text") or kwargs.get("query") or ""
    idea = parse_trade_text(text) if text else TradeIdea()
    context = kwargs.get("context") or {}

    def pick(name: str, *aliases: str):
        for key in (name, *aliases):
            if key in kwargs and kwargs[key] is not None:
                return kwargs[key]
            if key in context and context[key] is not None:
                return context[key]
        return None

    for field, aliases in {
        "symbol": ("market", "pair"),
        "entry": ("entry_price",),
        "stop_loss": ("sl", "stop"),
        "take_profit": ("tp", "target"),
        "risk_percent": ("risk",),
        "account_balance": ("balance",),
    }.items():
        value = pick(field, *aliases)
        if value is not None:
            setattr(idea, field, float(value) if field != "symbol" else str(value))

    side_raw = pick("side", "direction")
    if side_raw:
        token = str(side_raw).strip().upper()
        if token in {"BUY", "LONG"}:
            idea.side = Side.BUY
        elif token in {"SELL", "SHORT"}:
            idea.side = Side.SELL

    if idea.side is None and idea.entry is not None and idea.stop_loss is not None:
        idea.side = Side.BUY if idea.stop_loss < idea.entry else Side.SELL

    return idea


def _summary_line(structured: Dict[str, Any]) -> str:
    bits = []
    if structured.get("symbol"):
        bits.append(str(structured["symbol"]))
    if structured.get("direction"):
        bits.append(str(structured["direction"]))
    if structured.get("risk_reward") is not None:
        bits.append(f"R:R {structured['risk_reward']:.2f}")
    if structured.get("max_risk_amount") is not None:
        bits.append(f"risk {structured['max_risk_amount']:,.2f}")
    return " | ".join(bits) or "Partial trade analysis."
