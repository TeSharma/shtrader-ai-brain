/**
 * Wire types for the Shtrader LA local HTTP API.
 *
 * These mirror `shtrader_la/core/schemas.py::AgentResponse.to_dict()` so the
 * console can render intent, structured output, tool results and knowledge hits
 * without re-implementing any of the engine's logic in TypeScript.
 */

export type ShtraderIntent =
  | "general_trading"
  | "risk_calculation"
  | "trade_analysis"
  | "trading_plan"
  | "knowledge_query"
  | "position_sizing";

export interface ShtraderToolResult {
  tool: string;
  ok: boolean;
  data: Record<string, unknown>;
  error?: string | null;
  explanation: string;
}

export interface ShtraderKnowledgeHit {
  doc_id: string;
  title: string;
  score: number;
  excerpt: string;
}

export interface ShtraderAgentResponse {
  intent: ShtraderIntent;
  answer: string;
  structured: Record<string, unknown>;
  tool_results: ShtraderToolResult[];
  knowledge: ShtraderKnowledgeHit[];
  recommendations: string[];
  disclaimer: string;
}

export interface ShtraderHealth {
  status: string;
  provider: string;
  model_active: boolean;
  mode: "local_model" | "deterministic_only";
}