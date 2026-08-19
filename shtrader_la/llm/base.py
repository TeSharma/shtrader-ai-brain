"""LLM provider abstraction.

The application logic never imports a concrete model implementation. Swapping
llama.cpp for a fine-tuned Shtrader model later must not touch the agent.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass
class GenerationConfig:
    max_tokens: int = 512
    temperature: float = 0.3
    top_p: float = 0.9
    stop: Optional[List[str]] = None


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMProvider(abc.ABC):
    """Minimal surface: text in, text out."""

    name: str = "abstract"

    @abc.abstractmethod
    def generate(self, prompt: str, config: Optional[GenerationConfig] = None) -> str:
        """Complete a single prompt."""

    def chat(
        self, messages: Iterable[Message], config: Optional[GenerationConfig] = None
    ) -> str:
        """Default chat implementation flattens messages into a prompt.
        Providers with a native chat template should override this."""
        parts = []
        for m in messages:
            parts.append(f"{m.role.upper()}: {m.content}")
        parts.append("ASSISTANT:")
        return self.generate("\n\n".join(parts), config)

    def available(self) -> bool:
        """Whether this provider can actually serve requests right now."""
        return True


class StubProvider(LLMProvider):
    """Deterministic offline provider used by tests, CI and the
    'weights not downloaded yet' path. It never invents numbers: it reports the
    deterministic context it was handed."""

    name = "stub"

    def __init__(self, canned: Optional[str] = None) -> None:
        self.canned = canned
        self.calls: List[str] = []

    def generate(self, prompt: str, config: Optional[GenerationConfig] = None) -> str:
        self.calls.append(prompt)
        if self.canned is not None:
            return self.canned
        return (
            "[stub model] No local GGUF weights are loaded, so no natural-language "
            "reasoning was generated. All deterministic calculations below are exact "
            "and were produced by Shtrader LA's tools, not by a language model. "
            "Run `bash download_model.sh` to enable full reasoning."
        )
