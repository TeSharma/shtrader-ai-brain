"""HTTP request/response models for the Shtrader LA local API.

These deliberately mirror the core contracts (AgentRequest) without re-implementing
any logic — the FastAPI layer only marshals JSON in and out of the orchestrator.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Body for ``POST /api/v1/chat`` — the wire form of core ``AgentRequest``."""

    query: str = Field(
        ...,
        min_length=1,
        description="The trader's message in natural language.",
    )
    session_id: str = Field(
        default="default",
        max_length=128,
        description="Stable ID so the agent can remember facts across turns.",
    )

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be blank")
        return stripped


class HealthResponse(BaseModel):
    status: str
    provider: str
    model_active: bool
    mode: str