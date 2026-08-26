/**
 * Fetch client for the local Shtrader LA HTTP API.
 *
 * The console talks to the Python engine running on a local FastAPI server
 * (default `http://127.0.0.1:8000`). Override the address with the
 * `VITE_SHTRADER_API_URL` env var. Everything is offline — no cloud AI is
 * called; a missing local server surfaces as a clear `LocalAgentOfflineError`.
 */

import type { ShtraderAgentResponse, ShtraderHealth } from "./types";

const DEFAULT_BASE_URL = "http://127.0.0.1:8000";

function getBaseUrl(): string {
  const fromEnv =
    (import.meta.env["VITE_SHTRADER_API_URL"] as string | undefined) ?? "";
  if (fromEnv.trim().length > 0) {
    return fromEnv.replace(/\/+$/, "");
  }
  return DEFAULT_BASE_URL;
}

export class LocalAgentOfflineError extends Error {
  constructor() {
    super(
      "The local Shtrader LA engine is not running. Start it with: " +
        ".venv\\Scripts\\python -m uvicorn shtrader_la.api.app:app --host 0.0.0.0 --port 8000",
    );
    this.name = "LocalAgentOfflineError";
  }
}

async function toJson(response: Response): Promise<Record<string, unknown>> {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return {};
  }
}

/** Send a message to the engine and return the typed agent response. */
export async function sendMessage(
  query: string,
  sessionId = "default",
): Promise<ShtraderAgentResponse> {
  let response: Response;
  try {
    response = await fetch(`${getBaseUrl()}/api/v1/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, session_id: sessionId }),
    });
  } catch {
    throw new LocalAgentOfflineError();
  }

  if (!response.ok) {
    throw new LocalAgentOfflineError();
  }

  return (await toJson(response)) as unknown as ShtraderAgentResponse;
}

/** Lightweight probe of the engine's health/status. */
export async function getHealth(): Promise<ShtraderHealth> {
  let response: Response;
  try {
    response = await fetch(`${getBaseUrl()}/health`, {
      method: "GET",
      headers: { Accept: "application/json" },
    });
  } catch {
    throw new LocalAgentOfflineError();
  }
  if (!response.ok) {
    throw new LocalAgentOfflineError();
  }
  return (await toJson(response)) as unknown as ShtraderHealth;
}