"""llama.cpp-backed provider (GGUF, quantized, CPU-only by default).

`llama_cpp` is imported lazily so that the rest of Shtrader LA — tools, router,
knowledge, API schemas, tests — works on a machine with no weights and no
inference dependency installed.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from .base import GenerationConfig, LLMProvider, Message
from .config import ModelConfig


class LlamaCppProvider(LLMProvider):
    name = "llama_cpp"

    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        self.config = config or ModelConfig.from_env()
        self._llm = None

    # -- lifecycle ---------------------------------------------------------

    def available(self) -> bool:
        if not self.config.model_path:
            return False
        try:
            import llama_cpp  # noqa: F401
        except ImportError:
            return False
        return True

    def load(self):
        if self._llm is not None:
            return self._llm
        if not self.config.model_path:
            raise RuntimeError(
                "No GGUF model found. Run `bash download_model.sh` first, or set "
                "SHTRADER_MODEL_PATH."
            )
        try:
            from llama_cpp import Llama
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "llama-cpp-python is not installed. Run "
                "`pip install -r requirements.txt`."
            ) from exc

        self._llm = Llama(
            model_path=self.config.model_path,
            n_ctx=self.config.n_ctx,
            n_threads=self.config.n_threads,
            n_gpu_layers=self.config.n_gpu_layers,
            n_batch=self.config.n_batch,
            seed=self.config.seed,
            verbose=self.config.verbose,
        )
        return self._llm

    # -- inference ---------------------------------------------------------

    def generate(self, prompt: str, config: Optional[GenerationConfig] = None) -> str:
        cfg = config or GenerationConfig(
            max_tokens=self.config.max_tokens, temperature=self.config.temperature
        )
        llm = self.load()
        out = llm(
            prompt,
            max_tokens=cfg.max_tokens,
            temperature=cfg.temperature,
            top_p=cfg.top_p,
            stop=cfg.stop or [],
        )
        return out["choices"][0]["text"].strip()

    def chat(
        self, messages: Iterable[Message], config: Optional[GenerationConfig] = None
    ) -> str:
        cfg = config or GenerationConfig(
            max_tokens=self.config.max_tokens, temperature=self.config.temperature
        )
        llm = self.load()
        payload: List[dict] = [{"role": m.role, "content": m.content} for m in messages]
        out = llm.create_chat_completion(
            messages=payload,
            max_tokens=cfg.max_tokens,
            temperature=cfg.temperature,
            top_p=cfg.top_p,
            stop=cfg.stop or [],
        )
        return (out["choices"][0]["message"]["content"] or "").strip()


def build_provider(config: Optional[ModelConfig] = None) -> LLMProvider:
    """Return llama.cpp when weights + runtime are present, else the stub.

    This keeps the CLI, API and tests usable before `download_model.sh` runs,
    without ever silently faking numeric output.
    """
    provider = LlamaCppProvider(config)
    if provider.available():
        return provider
    from .base import StubProvider

    return StubProvider()
