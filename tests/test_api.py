"""API tests — the local FastAPI bridge must reuse the core contracts and add no math.

These exercise the real HTTP surface (`/health`, `/api/v1/chat`) against the
offline orchestrator. Skipped cleanly if FastAPI (and its test client) are absent.
"""

from __future__ import annotations

import pytest

from shtrader_la.api.app import app

fastapi_installed = True
try:
    from fastapi.testclient import TestClient
except Exception:  # pragma: no cover - exercised when fastapi is missing
    fastapi_installed = False


pytestmark = pytest.mark.skipif(
    not fastapi_installed,
    reason="fastapi is not installed (install requirements.txt to run the API tests)",
)


def test_health_reports_offline_deterministic_mode() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["provider"] == "stub"
    assert payload["model_active"] is False
    assert payload["mode"] == "deterministic_only"


def test_chat_returns_full_agent_contract() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={
            "query": (
                "My account balance is $1,000 and I risk 1% per trade. "
                "Buy EUR/USD near 1.0800 with stop 1.0750 and target 1.0950. "
                "Analyse this and give the risk/reward and capital at risk."
            ),
            "session_id": "test-session",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    # Core contract fields exposed on the wire.
    for key in (
        "intent",
        "answer",
        "structured",
        "tool_results",
        "knowledge",
        "recommendations",
        "disclaimer",
    ):
        assert key in payload
    assert payload["intent"] in {
        "general_trading",
        "risk_calculation",
        "trade_analysis",
        "trading_plan",
        "knowledge_query",
        "position_sizing",
    }


def test_chat_rejects_blank_query() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/chat", json={"query": "   ", "session_id": "x"})
    assert response.status_code == 422