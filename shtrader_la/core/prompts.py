"""Prompt templates.

The model is a narrator, never a calculator. Every prompt states this
explicitly and hands the model a deterministic context block produced by tools
and knowledge retrieval.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .schemas import Intent, KnowledgeHit, ToolResult

SYSTEM_PROMPT = (
    "You are Shtrader LA, an offline trading intelligence assistant.\n"
    "Rules you must never break:\n"
    "1. All numbers come from the DETERMINISTIC CONTEXT block. Never recalculate, "
    "re-round or invent a number. If a number is absent, say it is unavailable.\n"
    "2. You explain, structure and teach. You do not place trades and you never "
    "promise profit.\n"
    "3. Be concise and practical. Prefer short paragraphs and bullet points.\n"
    "4. Always frame guidance as risk management education, not financial advice.\n"
)

INTENT_GUIDANCE: Dict[Intent, str] = {
    Intent.GENERAL_TRADING: "Answer the trader's question directly and briefly.",
    Intent.RISK_CALCULATION: (
        "Explain the capital-at-risk figures and what they mean for survivability."
    ),
    Intent.TRADE_ANALYSIS: (
        "Walk through the setup: risk, reward, ratio, position size, and the verdict."
    ),
    Intent.TRADING_PLAN: (
        "Produce a structured plan: market, setup criteria, entry, invalidation, "
        "targets, risk per trade, and review rules."
    ),
    Intent.KNOWLEDGE_QUERY: (
        "Teach the concept using the retrieved knowledge. Define it, then give one "
        "concrete example."
    ),
    Intent.POSITION_SIZING: (
        "Explain the position size, the stop distance it assumes, and any assumptions "
        "flagged in the context."
    ),
}


def format_tool_context(results: List[ToolResult]) -> str:
    lines: List[str] = []
    for result in results:
        if result.ok:
            lines.append(f"- tool {result.tool}: {result.explanation}".rstrip())
            lines.append(f"  data: {json.dumps(result.data, default=str)}")
        else:
            lines.append(f"- tool {result.tool}: FAILED - {result.error}")
    return "\n".join(lines)


def format_knowledge_context(hits: List[KnowledgeHit]) -> str:
    return "\n".join(
        f"- [{hit.doc_id}] {hit.title} (score {hit.score}): {hit.excerpt}" for hit in hits
    )


def build_user_prompt(
    query: str,
    intent: Intent,
    tool_results: List[ToolResult],
    knowledge: List[KnowledgeHit],
    facts: Dict[str, Any] | None = None,
) -> str:
    parts = [f"TRADER MESSAGE:\n{query.strip()}", f"DETECTED INTENT: {intent.value}"]
    if facts:
        parts.append(
            "REMEMBERED FACTS:\n"
            + "\n".join(f"- {k}: {v}" for k, v in sorted(facts.items()))
        )
    tool_block = format_tool_context(tool_results)
    knowledge_block = format_knowledge_context(knowledge)
    if tool_block or knowledge_block:
        parts.append(
            "DETERMINISTIC CONTEXT (authoritative, computed by Shtrader LA tools):\n"
            + (tool_block or "- no tool output")
            + ("\n\nKNOWLEDGE EXCERPTS:\n" + knowledge_block if knowledge_block else "")
        )
    else:
        parts.append(
            "DETERMINISTIC CONTEXT: none available. Answer from general trading "
            "principles and do not state specific numbers."
        )
    parts.append("TASK: " + INTENT_GUIDANCE.get(intent, INTENT_GUIDANCE[Intent.GENERAL_TRADING]))
    return "\n\n".join(parts)
