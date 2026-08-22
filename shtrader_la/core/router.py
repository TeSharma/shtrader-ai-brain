"""Intent router.

Rules first, model second. Regex classification is free, deterministic and
testable; the LLM is only consulted when the rules are genuinely ambiguous, and
its answer is constrained to the known Intent set. The router never computes
numbers and never calls tools.

Classification combines four independent signal groups:

* topic keywords      -> which subject the trader is talking about
* conceptual language -> "what is", "explain", "teach me" (educational intent)
* action language     -> "calculate", "analyse", "size" (compute intent)
* numeric signals     -> price levels, risk percentages, account balances

A conceptual query with no numbers and no action verb is a KNOWLEDGE_QUERY even
when its topic keyword ("risk reward") belongs to another intent. As soon as
levels or an action verb appear, the topic intent wins again.
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
_MONEY = re.compile(
    r"[$€£₦]\s?\d"
    r"|(?:\d[\d,]*(?:\.\d+)?)\s*(?:usd|eur|gbp|ngn|kes|zar|k\b)"
    # bare balance: "a 5000 account", "account of 10,000", "balance 2500"
    r"|(?:\d[\d,]{2,}(?:\.\d+)?)\s*(?:dollar|usd)?\s*(?:account|balance|capital|equity|portfolio)"
    r"|(?:account|balance|capital|equity|portfolio)\D{0,10}?\d[\d,]{2,}",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\d")

# Phrasing that asks "how much am I risking" — a quantity question, not a concept.
_RISK_QUANTITY = re.compile(
    r"\b(?:my\s+(?:max(?:imum)?\s+)?risk|am\s+i\s+risking|risking|risk\s+amount|"
    r"max(?:imum)?\s+risk|capital\s+at\s+risk|how\s+much\s+money|how\s+much\s+(?:do\s+)?i\s+risk|"
    r"\d+(?:\.\d+)?\s*%\s*risk|risk\s+of\s+\d|risk\s+per\s+trade)\b",
    re.IGNORECASE,
)


# Educational / definitional phrasing.
_CONCEPTUAL = re.compile(
    r"(?:^|\b)(?:what\s+(?:is|are|does|do)|whats|what's|explain|explanation\s+of|"
    r"define|definition\s+of|teach\s+me|tell\s+me\s+about|meaning\s+of|"
    r"difference\s+between|how\s+does|how\s+do|why\s+does|why\s+do|"
    r"learn\s+about|introduction\s+to)\b",
    re.IGNORECASE,
)

# Compute / evaluate phrasing.
_ACTION = re.compile(
    r"\b(?:calculate|calc|compute|work\s+out|size|sizing|size\s+me|how\s+many|"
    r"how\s+much\s+(?:should|to|can)|analyse|analyze|review|evaluate|assess|"
    r"check\s+this|rate\s+this|build\s+me|give\s+me\s+a\s+plan)\b",
    re.IGNORECASE,
)

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


@dataclass
class Signals:
    conceptual: bool
    action: bool
    levels: bool
    percent: bool
    money: bool
    numbers: bool
    risk_quantity: bool = False

    @property
    def computational(self) -> bool:
        """True when the message asks for (or supplies data for) a calculation."""
        return (
            self.action
            or self.levels
            or (self.percent and self.money)
            or (self.risk_quantity and self.numbers)
        )

    def to_dict(self) -> Dict[str, bool]:
        return {
            "conceptual": self.conceptual,
            "action": self.action,
            "price_levels": self.levels,
            "risk_percent": self.percent,
            "money": self.money,
            "risk_quantity": self.risk_quantity,
        }


def extract_signals(text: str) -> Signals:
    return Signals(
        conceptual=bool(_CONCEPTUAL.search(text)),
        action=bool(_ACTION.search(text)),
        levels=bool(_PRICE_LEVEL.search(text)),
        percent=bool(_RISK_PERCENT.search(text)),
        money=bool(_MONEY.search(text)),
        numbers=bool(_NUMBER.search(text)),
        risk_quantity=bool(_RISK_QUANTITY.search(text)),
    )



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

        signals = extract_signals(text)

        # Educational question with nothing to compute -> knowledge retrieval.
        if signals.conceptual and not signals.computational:
            return RouteDecision(
                Intent.KNOWLEDGE_QUERY, 0.9, "rules", ["conceptual question"]
            )

        rules = self._rule_scores(text, signals)
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

    def _rule_scores(self, text: str, signals: Optional[Signals] = None):
        lowered = text.lower()
        signals = signals or extract_signals(text)
        scores: Dict[Intent, float] = {}
        matched: Dict[Intent, List[str]] = {}

        def bump(intent: Intent, amount: float, label: Optional[str] = None) -> None:
            scores[intent] = scores.get(intent, 0.0) + amount
            if label:
                matched.setdefault(intent, []).append(label)

        for intent, phrases in _KEYWORDS.items():
            for phrase in phrases:
                if phrase in lowered:
                    # Generic conceptual openers only count when the message is
                    # not asking for a computation.
                    if intent is Intent.KNOWLEDGE_QUERY and signals.computational:
                        continue
                    bump(intent, 1.0, phrase)

        if signals.levels:
            bump(Intent.TRADE_ANALYSIS, 1.5, "price levels")
        if signals.percent and signals.money:
            bump(Intent.RISK_CALCULATION, 1.0, "balance + risk %")
        # A full setup (levels + balance + risk) is an analysis, not a bare calc.
        if signals.levels and signals.percent:
            bump(Intent.TRADE_ANALYSIS, 0.75)
        # Conceptual phrasing that still carries numbers stays computational,
        # but keep a small educational weight so mixed questions can surface docs.
        if signals.conceptual and signals.computational:
            bump(Intent.KNOWLEDGE_QUERY, 0.25, "conceptual phrasing")

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
