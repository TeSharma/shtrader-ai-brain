# Shtrader LA — Stabilization and Completion Pass

## Verified current state (checked this turn)

- Present and byte-compiling cleanly: `core/schemas.py`, `core/router.py`, `core/memory.py`, all five tools + `base.py`/`registry.py`, `knowledge/retrieval.py`, all three `llm/` modules, five knowledge docs.
- Missing entirely: `core/prompts.py`, `core/orchestrator.py`, `core/agent.py`, everything under `integrations/`, `api/`, `app/` (only empty `__init__.py`), `tests/`, `requirements.txt`, `pytest.ini`, `scripts/`, `docs/`, `REPORT.md`.
- No mojibake found in any `.py`/`.md` file (scanned for `â€`, `Â£`, `â‚¬`); files are already UTF-8. Phase 0 encoding work is therefore verification + a guard test, not a mass rewrite.
- `fastapi` and `pytest` are not installed in this sandbox; they will be installed to run the validation gate.
- Frontend has only `src/routes/__root.tsx` and `src/routes/index.tsx`. `/tools` and `/architecture` do **not** exist yet — they will be created. `/` is still the template placeholder.

## Router fix (Phase 0)

Reproduce the misroute first, then restructure `_rule_scores` into three signal groups instead of flat keyword hits:

- conceptual signals: leading `what is/what are/explain/define/teach me/difference between/meaning of`
- action signals: `calculate/compute/size/analyze/analyse/review/check this setup`
- numeric signals: price levels, risk %, account money (existing regexes)

Rules: conceptual signal with no numeric signal wins `KNOWLEDGE_QUERY` even when a topic phrase like "risk reward" matches; numeric levels or an action verb suppress the conceptual boost so calculation/setup queries stay on `TRADE_ANALYSIS` / `RISK_CALCULATION` / `POSITION_SIZING`. Topic keywords stay in their intents — no removal.

## Phases 1–5 (Python)

- `core/prompts.py`: system persona + templates that inject deterministic context and forbid the model from recomputing numbers.
- `core/orchestrator.py`: `AgentRequest` → route → select tools/knowledge per intent → run tools via registry → build structured context → call provider → `AgentResponse`. Merges session memory facts (balance, risk %) so follow-ups resolve.
- Deterministic fallback formatter: when the provider is `StubProvider` (or generation fails), the answer is composed from tool/knowledge results, never the raw stub placeholder. A `model` flag in `structured` reports whether real weights are active.
- `core/agent.py`: `Agent.respond(query, context=None, session_id="default")` wrapping the orchestrator, plus memory writes.
- Knowledge: add `forex-basics.md`, `crypto-terms.md`, `trading-psychology.md`.
- `integrations/`: `base.py` adapter protocols, `market_data.py`, `user_data.py`, `execution.py` — execution returns `TradeProposal` only, `requires_authorization=True`, no send path; stub adapters for offline tests.
- `api/schemas.py` + `api/server.py`: FastAPI `GET /health`, `GET /tools`, `POST /agent/query`, `POST /trade/proposal`; dependency-injected agent, structured errors, boots with no GGUF.
- `app/cli.py`: `python -m shtrader_la.app.cli "query"` one-shot plus `--interactive`.

## Phase 6 — Web console

Keep the existing design system; no redesign.

- Rewrite `src/routes/index.tsx` as the console: query input, intent badge, answer, tool-result cards, knowledge hits, disclaimer, and a model-status line that says "stub — no weights loaded" unless the API reports otherwise.
- New `src/routes/tools.tsx` (tool list from `GET /tools`) and `src/routes/architecture.tsx` (the real pipeline diagram).
- API base URL is configurable (default `http://127.0.0.1:8000`) and persisted locally. **The Python API cannot run inside the Lovable preview**, so when it is unreachable the console shows a clear "local API not connected" state and falls back to a small deterministic TypeScript port of the risk / R:R / position-sizing math so the hosted demo still computes real numbers — clearly labelled as the browser fallback, never as model output.
- Per-route `head()` metadata on all three routes.

## Phases 7–9 — Tests, deps, docs

- `tests/` covering schemas, router (all seven required cases), orchestrator, each calculator, parser, trade analysis, registry, BM25 retrieval (incl. new docs), agent-with-stub, proposal authorization, API endpoints via `TestClient`, plus error cases: invalid SL/TP, missing fields, unknown tool, zero stop distance, leverage violation, and a UTF-8/no-mojibake guard test over the repo.
- `requirements.txt` (core: fastapi, uvicorn, pytest, httpx) with `requirements-llm.txt` for optional `llama-cpp-python`; `pytest.ini`; `scripts/run_local.sh`, `scripts/benchmark.sh`.
- `REPORT.md`, `docs/architecture.md`, `docs/roadmap.md`, README with exact Windows PowerShell commands (including backtick-escaped `` `$1000 `` guidance and preferring pytest over `python -c`). Docs split strictly into VERIFIED vs PLANNED; no benchmark or llama.cpp performance claims.

## Phase 10 — Validation gate

`python -m compileall`, install core deps, run `pytest -q` until green, import smoke tests for Router/ToolRegistry/knowledge/Agent/API app, and live API checks for `GET /health` plus both required `POST /agent/query` payloads with no GGUF present. Final message reports files created/modified, tests actually run with their output, remaining blockers, the exact next local command, and whether the repo is ready for GGUF installation.

## Scope guard

No cloud APIs, no blockchain, no autonomous execution, no refactor of the working calculators beyond what the router fix requires.
