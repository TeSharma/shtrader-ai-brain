"""Shared data contracts for the Shtrader LA intelligence layer.

These are plain dataclasses on purpose: the core must import cleanly with only
the standard library so that tools, router and knowledge retrieval keep working
even if optional dependencies (llama-cpp-python, fastapi) are absent.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Intent(str, Enum):
    """Intents the router can resolve. Extend deliberately — each intent maps to
    a tool selection strategy in the orchestrator."""

    GENERAL_TRADING = "general_trading"
    RISK_CALCULATION = "risk_calculation"
    TRADE_ANALYSIS = "trade_analysis"
    TRADING_PLAN = "trading_plan"
    KNOWLEDGE_QUERY = "knowledge_query"
    POSITION_SIZING = "position_sizing"


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

    @property
    def is_long(self) -> bool:
        return self is Side.BUY


@dataclass
class TradeIdea:
    """A structured trade idea. All prices are in instrument quote units."""

    symbol: Optional[str] = None
    side: Optional[Side] = None
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_percent: Optional[float] = None
    account_balance: Optional[float] = None
    notes: Optional[str] = None

    def is_complete(self) -> bool:
        return None not in (self.symbol, self.side, self.entry, self.stop_loss, self.take_profit)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if isinstance(self.side, Side):
            data["side"] = self.side.value
        return data


@dataclass
class ToolResult:
    """Deterministic tool output. `ok=False` carries a human-readable error and
    never raises into the reasoning layer."""

    tool: str
    ok: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeHit:
    doc_id: str
    title: str
    score: float
    excerpt: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentRequest:
    query: str
    context: Dict[str, Any] = field(default_factory=dict)
    session_id: str = "default"


@dataclass
class AgentResponse:
    """What the agent returns. `answer` is for humans, everything else is for
    programmatic consumers such as the Shtrader platform."""

    intent: Intent
    answer: str
    structured: Dict[str, Any] = field(default_factory=dict)
    tool_results: List[ToolResult] = field(default_factory=list)
    knowledge: List[KnowledgeHit] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    disclaimer: str = (
        "Informational only. Not financial advice. Shtrader LA does not guarantee "
        "profits and never executes trades."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value,
            "answer": self.answer,
            "structured": self.structured,
            "tool_results": [t.to_dict() for t in self.tool_results],
            "knowledge": [k.to_dict() for k in self.knowledge],
            "recommendations": self.recommendations,
            "disclaimer": self.disclaimer,
        }


@dataclass
class TradeProposal:
    """Output of the execution *interface*. Shtrader LA only ever produces
    proposals; authorization and execution live outside the AI core."""

    trade: TradeIdea
    rationale: str
    checks: Dict[str, Any] = field(default_factory=dict)
    requires_authorization: bool = True
    status: str = "proposed"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade": self.trade.to_dict(),
            "rationale": self.rationale,
            "checks": self.checks,
            "requires_authorization": self.requires_authorization,
            "status": self.status,
        }
