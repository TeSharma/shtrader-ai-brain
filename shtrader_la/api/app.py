"""FastAPI HTTP bridge to the Shtrader LA orchestration core.

Run (from the project root):

    .venv\\Scripts\\python -m uvicorn shtrader_la.api.app:app --host 0.0.0.0 --port 8000

Design invariants (mirrored from the core):
* Deterministic tools own every number — this layer adds zero math.
* The default provider is the offline ``StubProvider``, so the API works with no
  GGUF weights and makes no cloud calls.
* A single module-level orchestrator keeps ``SessionMemory`` alive across
  requests so follow-up turns ("what's my max risk now?") resolve correctly.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..core.orchestrator import Orchestrator
from ..core.schemas import AgentRequest
from .schemas import ChatRequest, HealthResponse

# This is a local, offline, no-auth tool. The Vite dev server and Lovable previews
# may serve the page from any localhost port or proxied domain, so we allow any
# origin by default (mirrored as `Access-Control-Allow-Origin: *` when requests
# carry no credentials). A hosted build can pin specific origins via the
# SHTRADER_API_ALLOWED_ORIGINS env var (comma-separated).
def _allowed_origins() -> List[str]:
    raw = os.environ.get("SHTRADER_API_ALLOWED_ORIGINS", "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return ["*"]


_name = "shtrader-la-api"

app = FastAPI(title="Shtrader LA Local API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True if _allowed_origins() != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Module-level singleton: keeps per-session facts/transcript across HTTP requests.
_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


@app.get("/health", response_model=HealthResponse, tags=["agent"])
def health() -> HealthResponse:
    engine = get_orchestrator()
    return HealthResponse(
        status="ok",
        provider=engine.provider.name,
        model_active=engine.model_active,
        mode="local_model" if engine.model_active else "deterministic_only",
    )


@app.post("/api/v1/chat", tags=["agent"])
def chat(request: ChatRequest) -> Dict[str, object]:
    """Route a message through the Shtrader LA agent and return its response."""
    engine = get_orchestrator()
    agent_response = engine.handle(
        AgentRequest(query=request.query, session_id=request.session_id)
    )
    return agent_response.to_dict()