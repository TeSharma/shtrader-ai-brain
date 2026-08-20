"""Intent router.

Rules first, model second. Regex classification is free, deterministic and
testable; the LLM is only consulted when the rules are genuinely ambiguous, and
its answer is constrained to the known Intent set. The router never computes
numbers and never calls tools.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..llm.base import GenerationConfig, LLMProvider
from .schemas import Intent

_PRICE_LEVEL = re.compile(
    r"(?:stop\s*loss|stoploss|\bsl\b|take\s*profit|\btp\b|entry|invalidation)",
    re.IGNORECASE,
)
_RISK_PERCENT = re.compile(r"\d+(?:\.\d+)?\s*%", re.IGNORECASE)
_MONEY = re.compile(r"[$€£₦]\s?\d|(?:\d[\d,]*)\s*(?:usd|eur|gbp|ngn|kes|zar)\b", re.IGNORECASE)

_KEYWORDS: Dict[Intent, List[str]] = {
    Intent.POSITION_SIZING: [
        "position size", "position sizing", "how many lots", "how many units",
        "lot size", "how much should i buy", "how much to buy", "sizing",
    ],
    Intent.RISK_CALCULATION: [
        "how much am i risking", "capital at risk", "risk amount", "risk per trade",
        "max risk", "maximum risk", "drawdown limit", "risk calculator",
    ],
    Intent.TRADE_ANALYSIS: [
        "analyse this trade", "analyze this trade", "review my trade", "is this a good trade",
        "risk/reward", "risk reward", "r:r", "rr ratio", "check this setup", "trade idea",
    ],
    Intent.TRADING_PLAN: [
        "trading plan", "trade plan", "build me a plan", "strategy plan", "playbook",
        "entry criteria", "checklist before", "swing-trading plan", "swing trading plan",
    ],
    Intent.KNOWLEDGE_QUERY: [
        "what is", "what are", "explain", "define", "how does", "why does",
        "difference between", "teach me", "meaning of",
    ],
}

_ALLOWED = {i.value: i for i in Intent}


@dataclass
class RouteDecision:
    intent: Intent
    confidence: float
    source: str  # "rules" | "llm" | "fallback"
    matched: List[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "intent": self.intent.value,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "matched": self.matched,
        }


class Router:
    """Classify a user query into an :class:`Intent`.

    The provider is optional and only used as a tie-breaker, so the router works
    identically offline with no weights present.
    """

    def __init__(self, provider: Optional[LLMProvider] = None, use_llm_fallback: bool = True) -> None:
        self.provider = provider
        self.use_llm_fallback = use_llm_fallback

    # -- public API --------------------------------------------------------

    def classify(self, query: str) -> RouteDecision:
        text = (query or "").strip()
        if not text:
            return RouteDecision(Intent.GENERAL_TRADING, 0.0, "fallback", [])

        rules = self._rule_scores(text)
        if rules:
            intent, score, matched = rules[0]
            runner_up = rules[1][1] if len(rules) > 1 else 0.0
            if score >= 2 or score - runner_up >= 1:
                return RouteDecision(intent, min(0.95, 0.6 + 0.1 * score), "rules", matched)

        llm_intent = self._llm_classify(text)
        if llm_intent is not None:
            return RouteDecision(llm_intent, 0.5, "llm", [])

        if rules:
            intent, score, matched = rules[0]
            return RouteDecision(intent, 0.45, "rules", matched)
        return RouteDecision(Intent.GENERAL_TRADING, 0.3, "fallback", [])

    # -- internals ---------------------------------------------------------

    def _rule_scores(self, text: str):
        lowered = text.lower()
        scores: Dict[Intent, float] = {}
        matched: Dict[Intent, List[str]] = {}

        for intent, phrases in _KEYWORDS.items():
            for phrase in phrases:
                if phrase in lowered:
                    scores[intent] = scores.get(intent, 0.0) + 1.0
                    matched.setdefault(intent, []).append(phrase)

        has_levels = bool(_PRICE_LEVEL.search(text))
        has_percent = bool(_RISK_PERCENT.search(text))
        has_money = bool(_MONEY.search(text))

        if has_levels:
            scores[Intent.TRADE_ANALYSIS] = scores.get(Intent.TRADE_ANALYSIS, 0.0) + 1.5
            matched.setdefault(Intent.TRADE_ANALYSIS, []).append("price levels")
        if has_percent and has_money:
            scores[Intent.RISK_CALCULATION] = scores.get(Intent.RISK_CALCULATION, 0.0) + 1.0
            matched.setdefault(Intent.RISK_CALCULATION, []).append("balance + risk %")
        # A full setup (levels + balance + risk) is an analysis, not a bare calc.
        if has_levels and has_percent:
            scores[Intent.TRADE_ANALYSIS] = scores.get(Intent.TRADE_ANALYSIS, 0.0) + 0.75

        if not scores:
            return []
        ordered = sorted(
            ((intent, score, matched.get(intent, [])) for intent, score in scores.items()),
            key=lambda row: row[1],
            reverse=True,
        )
        return ordered

    def _llm_classify(self, text: str) -> Optional[Intent]:
        if not self.use_llm_fallback or self.provider is None:
            return None
        if not self.provider.available():
            return None
        prompt = (
            "Classify the trader's message into exactly one label.\n"
            "Labels: " + ", ".join(_ALLOWED) + "\n"
            "Answer with the label only, no punctuation.\n\n"
            f"Message: {text}\nLabel:"
        )
        try:
            raw = self.provider.generate(prompt, GenerationConfig(max_tokens=12, temperature=0.0))
        except Exception:
            return None
        token = (raw or "").strip().lower().splitlines()[0].strip(" .`\"'") if raw else ""
        for label, intent in _ALLOWED.items():
            if label in token:
                return intent
        return None
