"""Runtime configuration for local inference.

Values are tuned for the ADTC budget-laptop profile: 4 vCPU, 8 GB RAM,
integrated GPU only. Everything is overridable by environment variable so the
profiler and benchmark script can sweep configurations without code changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_DIR = REPO_ROOT / "model"


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class ModelConfig:
    model_path: Optional[str] = None
    n_ctx: int = 4096
    n_threads: int = 4
    n_gpu_layers: int = 0
    n_batch: int = 256
    temperature: float = 0.3
    max_tokens: int = 512
    seed: int = 42
    verbose: bool = False

    @classmethod
    def from_env(cls) -> "ModelConfig":
        return cls(
            model_path=os.environ.get("SHTRADER_MODEL_PATH") or discover_model_path(),
            n_ctx=_env_int("SHTRADER_N_CTX", 4096),
            n_threads=_env_int("SHTRADER_N_THREADS", os.cpu_count() or 4),
            n_gpu_layers=_env_int("SHTRADER_N_GPU_LAYERS", 0),
            n_batch=_env_int("SHTRADER_N_BATCH", 256),
            temperature=_env_float("SHTRADER_TEMPERATURE", 0.3),
            max_tokens=_env_int("SHTRADER_MAX_TOKENS", 512),
            seed=_env_int("SHTRADER_SEED", 42),
            verbose=os.environ.get("SHTRADER_VERBOSE", "0") == "1",
        )


def discover_model_path(model_dir: Optional[Path] = None) -> Optional[str]:
    """Return the first .gguf file in model/, or None when weights are absent."""
    directory = model_dir or DEFAULT_MODEL_DIR
    if not directory.is_dir():
        return None
    candidates = sorted(directory.glob("*.gguf"))
    return str(candidates[0]) if candidates else None
