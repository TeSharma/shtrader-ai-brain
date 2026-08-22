# Shtrader LA — Fix routing/parsing, then formal validation and remaining layers

Order of work is strict: fix router → fix symbol parsing → build tests → run pytest → fix regressions → then agent/integrations/API/CLI/web/docs.

## Phase 1 — Router fix (numeric risk queries)

`shtrader_la/core/router.py`

- Treat a message as computational when it carries a money amount **or** a risk percentage together with any risk/account wording, not only `action or levels or (percent and money)`. `"calculate my risk on a 5000 account risking 1%"` has no `$` sign, so `_MONEY` misses it: add a bare-balance pattern (`\d{3,}` near `account|balance|capital|equity`, with thousands separators) so it counts as money.
- Add a "risk-quantity" signal: phrasing like `my risk`, `am i risking`, `risking N%`, `maximum risk`, `how much money`, plus a number → RISK_CALCULATION weight.
- Keep the conceptual short-circuit, but require the query to have **no** numeric/risk-quantity signal before it returns KNOWLEDGE_QUERY. `"what is my maximum risk on a 10000 account at 2%"` then falls through to the scoring path where RISK_CALCULATION wins.
- Keep POSITION_SIZING / TRADE_ANALYSIS scoring untouched (price levels still dominate), so existing conceptual and analysis routing does not regress.

Target routing (all become regression tests):

```text
KNOWLEDGE_QUERY      what is risk reward / explain position sizing /
                     what is market structure / how does leverage work
RISK_CALCULATION     calculate my risk on a 5000 account risking 1%
                     what is my maximum risk on a 10000 account at 2%
                     how much money am I risking with 2% risk on a $5000 account
                     calculate 1% risk on a $10,000 account
```

## Phase 2 — Symbol parsing fix

`shtrader_la/tools/trade_formatter.py`

The bogus symbols come from the last pattern, `\b([A-Z]{6})\b`, matched against `text.upper()` — so "MARKET" → `MAR/KET`, "REWARD" → `REW/ARD`.

- Match symbols against the original text, requiring the token to be genuinely uppercase in the source (so ordinary lowercase prose can never produce a symbol).
- Replace the blind 6-letter rule with a whitelist of currency codes (USD, EUR, GBP, JPY, CHF, AUD, NZD, CAD, plus USDT/USDC for crypto quotes) — a pair is only recognized when both halves are known codes, whether written `EURUSD`, `EUR/USD`, or `EUR USD`.
- Keep explicit crypto bases (BTC, ETH, …), metals and index tickers as they are; drop the loose `[A-Z]{2,10}[-/][A-Z]{2,10}` catch-all in favor of known-code / known-ticker checks.
- Result: conceptual queries produce `symbol = None`, so `structured.inputs` has no fabricated symbol.

## Phase 3 — Test suite

New `tests/` with `pytest.ini` (rootdir config, quiet default) and `pytest` added to `requirements.txt` (pytest is not currently installed in this environment; it will be installed to run the suite).

- `test_schemas.py` — enum values, `TradeIdea.to_dict`, `ToolResult` ok/fail shape, `AgentResponse` serialization.
- `test_router.py` — the conceptual and risk-calculation regression tables above, plus position-sizing and trade-analysis routing and empty input.
- `test_orchestrator.py` — knowledge query, risk calculation, position sizing, trade analysis, StubProvider determinism, no fabricated symbol in `structured.inputs`, structured keys (`route`, `model`, `inputs`, `tools_used`, `tools_failed`, `knowledge_docs`), tool failure surfaced as `tools_failed` without raising, disclaimer present in the answer.
- `test_tools.py` — risk calculator, R:R calculator, position sizing, trade analysis; invalid inputs (missing/non-numeric/negative) return `ok=False`; boundary cases (zero stop distance, 100% risk, tiny balance).
- `test_trade_parser.py` — the two full trade strings, risk percent, account balance, incomplete text (`missing` populated), and explicit negative cases asserting "market structure" / "risk reward" yield no symbol.
- `test_bm25.py` — each of the five existing documents is the top hit for its own topic query; no new knowledge documents fabricated here.
- `test_api.py`, `test_proposals.py` — written in Phase 5/6 alongside the API and integration interfaces; skipped cleanly until those modules exist.

Validation: `python -m compileall shtrader_la` then `python -m pytest -q`, with targeted per-file reruns on failure. Regressions get fixed before moving on.

## Phase 4 — `core/agent.py`

Thin facade over Orchestrator: construct provider/registry/knowledge/memory, expose `ask(query, session_id, context)`, no business logic of its own.

## Phase 5 — Integrations (proposal-only)

`integrations/base.py` defines a `Proposal` record and an authorization gate that always returns "requires human approval". `market_data.py` and `user_data.py` are read-only interfaces with local/mock implementations; `execution.py` can only *produce* proposals — never execute. `test_proposals.py` asserts no code path can execute without explicit authorization.

## Phase 6 — API and CLI

`api/schemas.py` (request/response models reusing core contracts), `api/server.py` (FastAPI: `/health`, `/ask`, `/tools/*`, `/knowledge/search`, `/architecture`) delegating to the orchestrator with zero duplicated math. `app/cli.py` runs interactively on StubProvider without GGUF. `test_api.py` covers routes via `TestClient`, skipped if FastAPI is absent.

## Phase 7 — Web console

Replace the template placeholder at `src/routes/index.tsx` with the Shtrader LA console (chat + structured response inspector), plus `/tools` (calculator forms) and `/architecture` (layer diagram, authorization boundary). Pages call the API contracts; when the local Python API is unreachable they show a clear "start the local agent" state rather than reimplementing the math in TypeScript. Each route gets its own `head()` metadata.

## Phase 8 — Docs and scripts

`REPORT.md`, `docs/architecture.md`, `docs/roadmap.md`, README command section, `scripts/run_local.sh`, `scripts/benchmark.sh`.

## Invariants held throughout

Deterministic tools own every number; the LLM never calculates; router picks intent; orchestrator coordinates; provider stays optional with StubProvider working offline; no cloud APIs, no blockchain, no autonomous execution; no GGUF install in this pass; working calculators are not refactored beyond the confirmed symbol fix.

## Completion report will include

Exact test commands run, pass/fail counts, remaining failures, current commit, files created/modified, known limitations.
