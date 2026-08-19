"""Tool registry — the single place the orchestrator discovers capabilities."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..core.schemas import ToolResult
from .base import Tool
from .position_sizing import PositionSizingEngine
from .risk_reward import RiskCalculator, RiskRewardCalculator
from .trade_analysis import TradeAnalysisTool
from .trade_formatter import TradePlanParser


class ToolRegistry:
    def __init__(self, tools: Optional[Iterable[Tool]] = None) -> None:
        self._tools: Dict[str, Tool] = {}
        for tool in tools if tools is not None else default_tools():
            self.register(tool)

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def names(self) -> List[str]:
        return sorted(self._tools)

    def describe(self) -> List[Dict[str, str]]:
        return [
            {"name": t.name, "description": t.description}
            for t in sorted(self._tools.values(), key=lambda x: x.name)
        ]

    def run(self, name: str, **kwargs: Any) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            return ToolResult(tool=name, ok=False, error=f"unknown tool '{name}'")
        try:
            return tool.run(**kwargs)
        except Exception as exc:  # defensive: a tool bug must not kill the agent
            return ToolResult(tool=name, ok=False, error=f"tool error: {exc}")


def default_tools() -> List[Tool]:
    return [
        RiskCalculator(),
        RiskRewardCalculator(),
        PositionSizingEngine(),
        TradePlanParser(),
        TradeAnalysisTool(),
    ]
