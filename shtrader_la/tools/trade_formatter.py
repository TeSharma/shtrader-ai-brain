"""Natural language -> structured trade idea.

Deterministic parsing, no model involved, so results are reproducible and
testable. Ambiguity is reported through `missing`, never guessed.

Numeric extraction is a single-pass *claim* system rather than a set of
independent regexes: every number in the message is found once, with its span,
and each field claims at most one span. A span can never be claimed twice, so
"5000 account risking 1%" can only ever mean balance 5000 / risk 1%.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

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

# --- numeric scanning -------------------------------------------------------

_CURRENCY = "$€£₦"
_NUMBER_RE = re.compile(
    rf"(?P<cur>[{_CURRENCY}])?\s*(?P<num>\d[\d,]*(?:\.\d+)?)\s*(?P<suffix>%|k\b|pips?\b)?",
    re.IGNORECASE,
)

# Words that introduce each price field. Order matters: the most specific
# patterns are consumed first so "stop loss" can never be read as an entry.
_STOP_WORDS = r"(?:stop\s*loss|stoploss|\bsl\b|invalidation|stopped\s*out|\bstop\b)"
_TARGET_WORDS = r"(?:take\s*profit|\btp\b|target|objective|profit\s*target)"
_ENTRY_WORDS = (
    r"(?:entry|entries|enter|@"
    rf"|(?:{_BUY_WORDS}|{_SELL_WORDS})\s+(?:\w+\s+){{0,3}}?(?:at|near|around|from)"
    r"|(?:price|limit)\s+(?:at|of)?)"
)
_BALANCE_WORDS = r"(?:account\s*balance|balance|account|capital|equity|portfolio|funds?)"
_BALANCE_PREFIX = r"(?:i\s+have|with|using|on\s+a|of|is|:)"

# Distance (characters) a keyword may sit from the number it labels.
_NEAR = 18


@dataclass
class _Num:
    start: int
    end: int
    value: float
    currency: bool
    percent: bool
    unit: Optional[str]  # "k" | "pips" | None
    claimed_by: Optional[str] = None


def _to_float(token: str) -> Optional[float]:
    token = token.strip().replace(",", "")
    try:
        return float(token)
    except ValueError:
        return None


def scan_numbers(text: str) -> List[_Num]:
    """Every number in `text`, with span and adjacent markers."""
    out: List[_Num] = []
    for match in _NUMBER_RE.finditer(text or ""):
        value = _to_float(match.group("num"))
        if value is None:
            continue
        suffix = (match.group("suffix") or "").lower()
        unit: Optional[str] = None
        percent = suffix == "%"
        if suffix.startswith("k"):
            unit = "k"
            value *= 1000
        elif suffix.startswith("pip"):
            unit = "pips"
        out.append(
            _Num(
                start=match.start("num"),
                end=match.end("num"),
                value=value,
                currency=bool(match.group("cur")),
                percent=percent,
                unit=unit,
            )
        )
    return out


def _claim_by_keyword(
    text: str,
    numbers: Sequence[_Num],
    field: str,
    keyword_pattern: str,
    *,
    allow_percent: bool = False,
    allow_before: bool = False,
    min_value: float = 0.0,
    require_currency_or_min: bool = False,
) -> Optional[float]:
    """Assign the nearest unclaimed number to `field` using its keyword."""
    for match in re.finditer(keyword_pattern, text, re.IGNORECASE):
        candidates: List[_Num] = []
        for num in numbers:
            if num.claimed_by is not None:
                continue
            if num.percent and not allow_percent:
                continue
            if num.unit == "pips":
                continue
            if num.value < min_value:
                continue
            if require_currency_or_min and not num.currency and num.value < 100:
                continue
            gap_after = num.start - match.end()
            if 0 <= gap_after <= _NEAR and not _crosses_keyword(text, match.end(), num.start):
                candidates.append(num)
                continue
            if allow_before:
                gap_before = match.start() - num.end
                if 0 <= gap_before <= _NEAR and not _crosses_keyword(text, num.end, match.start()):
                    candidates.append(num)
        if not candidates:
            continue
        best = min(
            candidates,
            key=lambda n: min(
                abs(n.start - match.end()), abs(match.start() - n.end)
            ),
        )
        best.claimed_by = field
        return best.value
    return None


_ANY_KEYWORD = re.compile(
    rf"{_STOP_WORDS}|{_TARGET_WORDS}|{_BALANCE_WORDS}|\brisk(?:ing)?\b|\bentry\b",
    re.IGNORECASE,
)


def _crosses_keyword(text: str, start: int, end: int) -> bool:
    """True when another field keyword sits between a keyword and a number."""
    if end <= start:
        return False
    return bool(_ANY_KEYWORD.search(text[start:end]))


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
    idea = TradeIdea(notes=(text or "").strip())
    if not text:
        return idea

    # --- side ---------------------------------------------------------------
    buy_at = re.search(_BUY_WORDS, text, re.IGNORECASE)
    sell_at = re.search(_SELL_WORDS, text, re.IGNORECASE)
    if buy_at and (not sell_at or buy_at.start() < sell_at.start()):
        idea.side = Side.BUY
    elif sell_at:
        idea.side = Side.SELL

    # --- symbol -------------------------------------------------------------
    idea.symbol = extract_symbol(text)

    # --- numbers (claimed once each, most specific field first) --------------
    numbers = scan_numbers(text)

    idea.risk_percent = _claim_risk_percent(text, numbers)
    idea.stop_loss = _claim_by_keyword(text, numbers, "stop_loss", _STOP_WORDS)
    idea.take_profit = _claim_by_keyword(text, numbers, "take_profit", _TARGET_WORDS)
    idea.entry = _claim_by_keyword(text, numbers, "entry", _ENTRY_WORDS)
    idea.account_balance = _claim_balance(text, numbers)

    # Infer side from stop placement when words were absent.
    if idea.side is None and idea.entry is not None and idea.stop_loss is not None:
        idea.side = Side.BUY if idea.stop_loss < idea.entry else Side.SELL

    return idea


def _claim_risk_percent(text: str, numbers: Sequence[_Num]) -> Optional[float]:
    """A percentage tied to risk wording, else the only percentage present."""
    percents = [n for n in numbers if n.percent and n.claimed_by is None]
    if not percents:
        return None
    if len(percents) == 1:
        percents[0].claimed_by = "risk_percent"
        return percents[0].value
    for num in percents:
        window = text[max(0, num.start - 25) : min(len(text), num.end + 25)].lower()
        if "risk" in window:
            num.claimed_by = "risk_percent"
            return num.value
    percents[0].claimed_by = "risk_percent"
    return percents[0].value


def _claim_balance(text: str, numbers: Sequence[_Num]) -> Optional[float]:
    """Account balance: keyword on either side, or a lone currency amount."""
    value = _claim_by_keyword(
        text,
        numbers,
        "account_balance",
        _BALANCE_WORDS,
        allow_before=True,
        require_currency_or_min=True,
    )
    if value is not None:
        return value

    # "I have $2000 and want to risk 1%" — currency amount with balance framing.
    framing = re.search(rf"{_BALANCE_PREFIX}", text, re.IGNORECASE)
    for num in numbers:
        if num.claimed_by is not None or num.percent or num.unit == "pips":
            continue
        if num.currency and (framing is not None or num.value >= 100):
            num.claimed_by = "account_balance"
            return num.value
    return None


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


def extract_stop_pips(text: str) -> Optional[float]:
    """A stop distance expressed in pips ("with a 50 pip stop")."""
    for num in scan_numbers(text or ""):
        if num.unit == "pips":
            return num.value
    return None


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
