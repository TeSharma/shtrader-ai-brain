"""Deterministic tool contract.

Rule: language models never perform critical calculations. Every number a user
sees comes from a Tool subclass whose behaviour is covered by tests.
"""

from __future__ import annotations

import abc
from typing import Any, Dict

from ..core.schemas import ToolResult


class Tool(abc.ABC):
    name: str = "abstract"
    description: str = ""

    @abc.abstractmethod
    def run(self, **kwargs: Any) -> ToolResult:
        """Execute the tool. Must never raise for bad user input: return a
        ToolResult with ok=False instead."""

    # -- helpers -----------------------------------------------------------

    def fail(self, error: str) -> ToolResult:
        return ToolResult(tool=self.name, ok=False, error=error)

    def ok(self, data: Dict[str, Any], explanation: str = "") -> ToolResult:
        return ToolResult(tool=self.name, ok=True, data=data, explanation=explanation)

    @staticmethod
    def as_float(value: Any, field: str) -> float:
        if value is None:
            raise ValueError(f"'{field}' is required")
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError(f"'{field}' must be a number, got {value!r}")

    @staticmethod
    def positive(value: float, field: str) -> float:
        if value <= 0:
            raise ValueError(f"'{field}' must be greater than zero")
        return value
