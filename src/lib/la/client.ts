/**
 * Fetch client for the Shtrader LA HTTP API (FastAPI engine).
 *
 * The console talks to the Python engine over HTTP. Resolution order:
 *   1. a runtime override persisted across reloads (setEngineBaseUrl),
 *   2. the `VITE_SHTRADER_API_URL` env var baked in at build time,
 *   3. a stable default.
 *
 * The default points at the local engine (`npm run start:all`). When the console
 * is deployed (e.g. the Lovable preview), point it at the *public* hosted engine
 * URL by configuring `VITE_SHTRADER_API_URL` at build time or by using the in-app
 * endpoint setting at runtime. Everything is offline-capable: the engine's
 * deterministic `StubProvider` needs no model, and no cloud AI is called.
 */

import type { ShtraderAgentResponse, ShtraderHealth } from "./types";

const DEFAULT_BASE_URL = "http://127.0.0.1:8000";
const STORAGE_KEY = "shtrader.engineUrl";

function normalize(raw: string | undefined): string {
  const value = (raw ?? "").trim().replace(/\/+$/, "");
  return value;
}

/** Resolve the engine base URL from runtime override, then env, then default. */
export function getBaseUrl(): string {
  if (typeof localStorage !== "undefined") {
    const stored = localStorage.getItem(STORAGE_KEY);
    const norm = normalize(stored ?? "");
    if (norm) return norm;
  }
  const fromEnv = (import.meta.env["VITE_SHTRADER_API_URL"] as string | undefined) ?? "";
  return normalize(fromEnv) || DEFAULT_BASE_URL;
}

/** Persist a runtime override for the engine base URL. Pass "" to reset. */
export function setEngineBaseUrl(url: string): void {
  if (typeof localStorage === "undefined") return;
  const norm = normalize(url);
  if (norm) {
    localStorage.setItem(STORAGE_KEY, norm);
  } else {
    localStorage.removeItem(STORAGE_KEY);
  }
}

export class LocalAgentOfflineError extends Error {
  constructor() {
    super(
      "The Shtrader LA engine is not reachable at " +
        `${getBaseUrl()}. For a local console run ` +
        "`npm run start:all` and open http://localhost:8080. For the deployed " +
        "preview, the console must point at a publicly hosted engine URL — " +
        "check the engine endpoint setting and confirm the engine is running.",
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