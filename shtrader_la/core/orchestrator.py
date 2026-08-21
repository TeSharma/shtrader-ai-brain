"""Orchestrator: the single place where routing, tools, knowledge and the LLM meet.

Pipeline:

    AgentRequest -> Router -> tool selection -> deterministic results
                 -> knowledge retrieval -> structured context
                 -> LLM narration (optional) -> AgentResponse

Design invariants:

* Deterministic tools own every number. The model never computes.
* The provider is optional. With :class:`StubProvider` (no GGUF weights) the
  orchestrator composes a deterministic answer from tool and knowledge output,
  so the CLI, API and web console remain useful offline.
* Nothing here imports fastapi, llama_cpp or any optional dependency.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..knowledge.retrieval import BM25KnowledgeProvider, KnowledgeProvider
from ..llm.base import GenerationConfig, LLMProvider, Message, StubProvider
from ..tools.registry import ToolRegistry
from ..tools.trade_formatter import parse_trade_text
from .memory import MemoryStore, SessionMemory
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .router import RouteDecision, Router
from .schemas import (
    AgentRequest,
    AgentResponse,
    Intent,
    KnowledgeHit,
    ToolResult,
)

# Which deterministic tools each intent may use.
TOOL_PLAN: Dict[Intent, List[str]] = {
    Intent.RISK_CALCULATION: ["risk_calculator"],
    Intent.POSITION_SIZING: ["position_sizing"],
    Intent.TRADE_ANALYSIS: ["trade_analysis"],
    Intent.TRADING_PLAN: ["trade_analysis"],
    Intent.KNOWLEDGE_QUERY: [],
    Intent.GENERAL_TRADING: [],
}

# Which intents benefit from document retrieval.
KNOWLEDGE_INTENTS = {
    Intent.KNOWLEDGE_QUERY,
    Intent.GENERAL_TRADING,
    Intent.TRADING_PLAN,
    Intent.RISK_CALCULATION,
    Intent.POSITION_SIZING,
}

FACT_KEYS = ("account_balance", "risk_percent", "symbol", "leverage", "pip_value_per_lot")


class Orchestrator:
    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        registry: Optional[ToolRegistry] = None,
        knowledge: Optional[KnowledgeProvider] = None,
        memory: Optional[MemoryStore] = None,
        router: Optional[Router] = None,
        top_k: int = 3,
    ) -> None:
        self.provider = provider or StubProvider()
        self.registry = registry or ToolRegistry()
        self.knowledge = knowledge if knowledge is not None else BM25KnowledgeProvider()
        self.memory = memory or SessionMemory()
        self.router = router or Router(provider=self.provider)
        self.top_k = top_k

    # -- public API --------------------------------------------------------

    @property
    def model_active(self) -> bool:
        """True only when a real (non-stub) provider can serve requests."""
        return not isinstance(self.provider, StubProvider) and self.provider.available()

    def handle(self, request: AgentRequest) -> AgentResponse:
        query = (request.query or "").strip()
        session_id = request.session_id or "default"
        decision = self.router.classify(query)

        context = self._merge_context(session_id, request.context, query)
        tool_results = self._run_tools(decision.intent, query, context)
        knowledge = self._retrieve(decision.intent, query)

        structured = self._structured(decision, context, tool_results, knowledge)
        recommendations = _collect_recommendations(tool_results)

        answer = self._narrate(query, decision.intent, tool_results, knowledge, context)
        if not answer:
            answer = deterministic_answer(query, decision.intent, tool_results, knowledge)

        self.memory.append(session_id, "user", query)
        self.memory.append(session_id, "assistant", answer)
        self.memory.remember(session_id, **{k: context.get(k) for k in FACT_KEYS})

        return AgentResponse(
            intent=decision.intent,
            answer=answer,
            structured=structured,
            tool_results=tool_results,
            knowledge=knowledge,
            recommendations=recommendations,
        )

    # -- steps -------------------------------------------------------------

    def _merge_context(
        self, session_id: str, request_context: Optional[Dict[str, Any]], query: str
    ) -> Dict[str, Any]:
        """Remembered facts < parsed text < explicit request context."""
        merged: Dict[str, Any] = {}
        merged.update(self.memory.facts(session_id))

        idea = parse_trade_text(query) if query else None
        if idea is not None:
            parsed = idea.to_dict()
            for key in ("symbol", "side", "entry", "stop_loss", "take_profit",
                        "risk_percent", "account_balance"):
                value = parsed.get(key)
                if value is not None:
                    merged[key] = value

        for key, value in (request_context or {}).items():
            if value is not None:
                merged[key] = value
        return merged

    def _run_tools(
        self, intent: Intent, query: str, context: Dict[str, Any]
    ) -> List[ToolResult]:
        results: List[ToolResult] = []
        for name in TOOL_PLAN.get(intent, []):
            kwargs = self._tool_kwargs(name, query, context)
            if kwargs is None:
                continue
            results.append(self.registry.run(name, **kwargs))
        return results

    def _tool_kwargs(
        self, name: str, query: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if name == "risk_calculator":
            if context.get("account_balance") is None or context.get("risk_percent") is None:
                return None
            return {
                "account_balance": context["account_balance"],
                "risk_percent": context["risk_percent"],
            }
        if name == "position_sizing":
            required = ("account_balance", "risk_percent", "entry", "stop_loss")
            if any(context.get(key) is None for key in required):
                return None
            return {key: context[key] for key in required} | {
                "symbol": context.get("symbol"),
                "method": context.get("method"),
                "pip_value_per_lot": context.get("pip_value_per_lot"),
                "leverage": context.get("leverage"),
            }
        if name == "trade_analysis":
            if context.get("entry") is None or context.get("stop_loss") is None:
                return None
            return {"text": query, "context": context}
        return {"text": query, "context": context}

    def _retrieve(self, intent: Intent, query: str) -> List[KnowledgeHit]:
        if intent not in KNOWLEDGE_INTENTS or not query:
            return []
        top_k = self.top_k if intent is Intent.KNOWLEDGE_QUERY else max(1, self.top_k - 1)
        try:
            return self.knowledge.search(query, top_k=top_k)
        except Exception:
            return []

    def _structured(
        self,
        decision: RouteDecision,
        context: Dict[str, Any],
        tool_results: List[ToolResult],
        knowledge: List[KnowledgeHit],
    ) -> Dict[str, Any]:
        structured: Dict[str, Any] = {
            "route": decision.to_dict(),
            "model": {
                "provider": self.provider.name,
                "active": self.model_active,
                "mode": "local_model" if self.model_active else "deterministic_only",
            },
            "inputs": {k: v for k, v in context.items() if v is not None},
            "tools_used": [r.tool for r in tool_results if r.ok],
            "tools_failed": [
                {"tool": r.tool, "error": r.error} for r in tool_results if not r.ok
            ],
            "knowledge_docs": [hit.doc_id for hit in knowledge],
        }
        for result in tool_results:
            if result.ok:
                structured[result.tool] = result.data
        return structured

    def _narrate(
        self,
        query: str,
        intent: Intent,
        tool_results: List[ToolResult],
        knowledge: List[KnowledgeHit],
        context: Dict[str, Any],
    ) -> Optional[str]:
        if not self.model_active:
            return None
        prompt = build_user_prompt(query, intent, tool_results, knowledge, context)
        messages = [
            Message(role="system", content=SYSTEM_PROMPT),
            Message(role="user", content=prompt),
        ]
        try:
            text = self.provider.chat(messages, GenerationConfig(max_tokens=600, temperature=0.3))
        except Exception:
            return None
        text = (text or "").strip()
        return text or None


# -- deterministic fallback -------------------------------------------------


def deterministic_answer(
    query: str,
    intent: Intent,
    tool_results: List[ToolResult],
    knowledge: List[KnowledgeHit],
) -> str:
    """Compose a useful answer with no language model involved."""
    lines: List[str] = []
    ok_results = [r for r in tool_results if r.ok]
    failures = [r for r in tool_results if not r.ok]

    if ok_results:
        lines.append("Deterministic calculation (computed by Shtrader LA tools):")
        for result in ok_results:
            lines.append(f"- {result.tool}: {result.explanation or 'see structured data'}")
            for key, value in _headline_fields(result):
                lines.append(f"  - {key}: {value}")

    if failures:
        lines.append("Could not complete:")
        for result in failures:
            lines.append(f"- {result.tool}: {result.error}")

    if knowledge:
        lines.append("")
        lines.append("From the offline knowledge base:")
        for hit in knowledge:
            lines.append(f"- {hit.title}: {hit.excerpt}")

    if not lines:
        lines.append(
            "No deterministic calculation applied to this message and no matching "
            "knowledge document was found. Supply entry, stop loss, take profit, "
            "account balance and risk percentage for an exact analysis, or ask a "
            "concept question such as \"what is risk reward?\"."
        )

    lines.append("")
    lines.append(
        "Note: no local GGUF model is loaded, so this answer is deterministic tool "
        "and knowledge output only - no language-model narration."
    )
    return "\n".join(lines).strip()


_HEADLINES = {
    "risk_calculator": ("max_risk_amount", "remaining_balance_if_stopped"),
    "risk_reward_calculator": ("risk_reward", "breakeven_win_rate_percent", "meets_min_rr"),
    "position_sizing": ("units", "lots", "stop_pips", "notional"),
    "trade_analysis": ("symbol", "direction", "risk_reward", "max_risk_amount", "position_size"),
}


def _headline_fields(result: ToolResult):
    for key in _HEADLINES.get(result.tool, ()):  # pragma: no branch
        value = result.data.get(key)
        if value is not None:
            yield key, value


def _collect_recommendations(tool_results: List[ToolResult]) -> List[str]:
    out: List[str] = []
    for result in tool_results:
        if not result.ok:
            continue
        for key in ("recommendations", "warnings", "assumptions"):
            for item in result.data.get(key, []) or []:
                if item not in out:
                    out.append(str(item))
    return out
