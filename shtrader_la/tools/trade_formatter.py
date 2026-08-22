"""Natural language -> structured trade idea.

Deterministic regex + validation. No model involved, so parsing is reproducible
and testable. Ambiguity is reported through `missing`, never guessed.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ..core.schemas import Side, ToolResult, TradeIdea
from .base import Tool

_BUY_WORDS = r"(?:buy|long|bullish|bid)"
_SELL_WORDS = r"(?:sell|short|bearish|ask)"

_FIAT = {"USD", "EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD", "NGN", "ZAR", "KES"}
_STABLE = {"USDT", "USDC", "BUSD", "DAI"}
_QUOTES = _FIAT | _STABLE
_CRYPTO = {"BTC", "ETH", "SOL", "XRP", "ADA", "MATIC", "BNB", "DOGE", "AVAX", "LINK", "DOT", "LTC"}
_METALS = {"XAU", "XAG", "XPT"}
_TICKERS = {"XAUUSD", "XAGUSD", "US30", "NAS100", "SPX500", "GER40", "UK100", "JP225"}
_BASES = _FIAT | _CRYPTO | _METALS


_NUM = r"(-?\d+(?:[.,]\d+)?)"


def _to_float(token: str) -> Optional[float]:
    token = token.strip().replace(",", "")
    try:
        return float(token)
    except ValueError:
        return None


def _find(pattern: str, text: str) -> Optional[float]:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    return _to_float(match.group(1))


class TradePlanParser(Tool):
    name = "trade_plan_parser"
    description = (
        "Parse a free-text trade idea into structured fields: symbol, side, entry, "
        "stop_loss, take_profit, risk_percent, account_balance."
    )

    def run(self, **kwargs: Any) -> ToolResult:
        text = kwargs.get("text") or kwargs.get("query") or ""
        if not isinstance(text, str) or not text.strip():
            return self.fail("'text' is required")

        idea = parse_trade_text(text)
        missing = [
            field
            for field in ("symbol", "side", "entry", "stop_loss", "take_profit")
            if getattr(idea, field) is None
        ]

        data: Dict[str, Any] = idea.to_dict()
        data["missing"] = missing
        data["complete"] = not missing

        explanation = (
            "Parsed "
            + ", ".join(f"{k}={v}" for k, v in idea.to_dict().items() if v is not None)
            if any(v is not None for v in idea.to_dict().values())
            else "No trade parameters detected."
        )
        return self.ok(data, explanation=explanation)


def parse_trade_text(text: str) -> TradeIdea:
    """Extract a TradeIdea from prose. Returns partially-filled ideas."""
    idea = TradeIdea(notes=text.strip())
    upper = text.upper()

    # --- side ---------------------------------------------------------------
    buy_at = re.search(_BUY_WORDS, text, re.IGNORECASE)
    sell_at = re.search(_SELL_WORDS, text, re.IGNORECASE)
    if buy_at and (not sell_at or buy_at.start() < sell_at.start()):
        idea.side = Side.BUY
    elif sell_at:
        idea.side = Side.SELL

    # --- symbol -------------------------------------------------------------
    idea.symbol = extract_symbol(text)


    # --- prices -------------------------------------------------------------
    idea.stop_loss = _find(
        rf"(?:stop(?:\s*loss)?|sl|stopped out|invalidation)\D{{0,15}}?{_NUM}", text
    )
    idea.take_profit = _find(
        rf"(?:take\s*profit|target|tp|objective)\D{{0,15}}?{_NUM}", text
    )
    idea.entry = _find(
        rf"(?:entry|enter|near|around|at|@|buy|sell|long|short)\D{{0,15}}?{_NUM}", text
    )

    # --- risk & balance -----------------------------------------------------
    idea.risk_percent = _find(rf"risk\D{{0,15}}?{_NUM}\s*%", text) or _find(
        rf"{_NUM}\s*%\s*risk", text
    )
    idea.account_balance = _find(
        rf"(?:balance|account|capital|equity)\D{{0,15}}?\$?\s*{_NUM}", text
    ) or _find(rf"\$\s*{_NUM}\s*(?:account|balance)", text)

    # Guard: don't let the risk percent leak into a price field.
    for field in ("entry", "stop_loss", "take_profit"):
        value = getattr(idea, field)
        if value is not None and idea.risk_percent is not None and value == idea.risk_percent:
            setattr(idea, field, None)

    # Infer side from stop placement when words were absent.
    if idea.side is None and idea.entry is not None and idea.stop_loss is not None:
        idea.side = Side.BUY if idea.stop_loss < idea.entry else Side.SELL

    return idea


def extract_symbol(text: str) -> Optional[str]:
    """Return a supported market symbol, or None.

    Only real market symbols are recognized: a pair whose base and quote are both
    known codes (EUR/USD, EURUSD, BTC/USDT), a known index/metal ticker, or a
    bare crypto/metal ticker written in uppercase (BTC). Ordinary English words
    can never produce a symbol, so prose such as "market structure" or
    "risk reward" yields None instead of a fabricated pair.
    """
    if not text:
        return None

    # 1. Explicit separator or space: EUR/USD, BTC-USDT, EUR USD, XAU / USD.
    for match in re.finditer(r"\b([A-Za-z]{2,5})\s*[/-]\s*([A-Za-z]{2,5})\b", text):
        pair = _pair(match.group(1), match.group(2))
        if pair:
            return pair
    for match in re.finditer(r"\b([A-Za-z]{3})\s+([A-Za-z]{3})\b", text):
        pair = _pair(match.group(1), match.group(2))
        if pair:
            return pair

    # 2. Known composite tickers and concatenated pairs: XAUUSD, EURUSD, BTCUSDT.
    for match in re.finditer(r"\b([A-Za-z]{5,10}|[A-Za-z]{2,5}\d{2,3})\b", text):
        token = match.group(1).upper()
        if token in _TICKERS:
            return token
        for cut in (3, 4):
            pair = _pair(token[:cut], token[cut:])
            if pair:
                return pair

    # 3. Bare crypto/metal ticker — uppercase only, so the English word "link"
    #    never becomes LINK/USD.
    for match in re.finditer(r"\b([A-Z]{3,5})\b", text):
        token = match.group(1)
        if token in _CRYPTO or token in _METALS:
            return f"{token}/USD"
    return None


def _pair(base: str, quote: str) -> Optional[str]:
    base, quote = base.upper(), quote.upper()
    if base in _BASES and quote in _QUOTES and base != quote:
        return f"{base}/{quote}"
    return None


def _normalize_symbol(candidate: str) -> str:
    """EURUSD -> EUR/USD; BTC -> BTC/USD; leave indices and metals alone."""
    candidate = candidate.upper().replace(" ", "")
    if candidate in _TICKERS:
        return candidate

    if "/" in candidate or "-" in candidate:
        return candidate.replace("-", "/")
    if len(candidate) == 6:
        return f"{candidate[:3]}/{candidate[3:]}"
    if candidate in {"BTC", "ETH", "SOL", "XRP", "ADA", "MATIC", "BNB", "DOGE", "AVAX", "LINK"}:
        return f"{candidate}/USD"
    return candidate


def format_trade_summary(idea: TradeIdea) -> List[str]:
    """Human-readable bullet lines for CLI/API display."""
    lines = []
    mapping = [
        ("Symbol", idea.symbol),
        ("Side", idea.side.value if idea.side else None),
        ("Entry", idea.entry),
        ("Stop loss", idea.stop_loss),
        ("Take profit", idea.take_profit),
        ("Risk %", idea.risk_percent),
        ("Account balance", idea.account_balance),
    ]
    for label, value in mapping:
        if value is not None:
            lines.append(f"{label}: {value}")
    return lines
