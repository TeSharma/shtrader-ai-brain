# ShTrader LA — Phases 0 to 7

This pass covers Phase 0 through Phase 7 of the roadmap. Phases 8+ (frontend integration, real GGUF model, auth, market data, execution, deployment) come in later passes; nothing here blocks them.

## Confirmed bugs (verified just now by running the current code)

```text
"calculate my risk on a 5000 account risking 1%"
  -> entry=5000, account_balance=1.0, risk_percent=1.0      (both wrong)
"5000 USD account risking 2%"
  -> account_balance=2.0                                    (wrong)
"I have $2000 and want to risk 1%"
  -> account_balance missing                                (wrong)
"What is 2% risk on a 10000 account?"
  -> account_balance missing                                (wrong)
"What is my maximum risk?"
  -> knowledge_query                                        (want risk_calculation)
knowledge "what is forex"   -> top hit position-sizing      (no forex doc exists)
knowledge "what is crypto"  -> top hit position-sizing      (no crypto doc exists)
knowledge "trading psychology" -> top hit trend-analysis    (no psychology doc exists)
pytest is not installed in this environment
```

Cause of the numeric bugs: in `trade_formatter.py` the balance pattern
`(?:balance|account|...)\D{0,15}?\$?\s*NUM` scans forward from the keyword, so
"account risking 1%" captures the `1`, and the entry pattern's `at|near|around`
alternatives grab the bare `5000`.

## Phase 0 — Stabilize the core

`shtrader_la/tools/trade_formatter.py`

- Rewrite numeric extraction as an ordered, single-pass claim system instead of independent regexes: find every number with its span, classify each once (percent-suffixed -> risk, keyword-prefixed -> balance/entry/stop/target), and never let two fields claim the same span.
- Balance: accept the number *before* the keyword ("5000 account", "5000 USD account", "$2000") as well as after ("account of 10,000", "balance 2500"), require 3+ digits or an explicit currency marker, and reject a number already claimed as a percent.
- Entry: only from explicit entry wording (`entry`, `enter`, `@`, `buy/sell/long/short at|near|around`) — drop the bare `at|near|around` catch that stole `5000`.
- Risk percent: any `N%` near risk wording, or a lone `N%` when no other percent exists.
- Keep the existing symbol whitelist logic (already correct: prose yields no symbol).

`shtrader_la/core/router.py`

- "What is my maximum risk?" (risk-quantity phrasing with no numbers) must beat the conceptual short-circuit and route to `risk_calculation`; plain concept questions ("what is forex", "what is market structure") stay `knowledge_query`.
- Re-verify the full intent table from the roadmap after the change.

`shtrader_la/tools/*`

- Confirm/repair input validation so invalid inputs return `ok=False`, never a number: zero/negative balance, zero/negative risk, risk > 100%, equal entry and stop, BUY with stop above entry or target below entry, and the mirror cases for SELL.

pytest in the user's venv (documented in README, not run here — this sandbox is Linux and has no access to `C:\Users\USER\shtrader-ai-brain\.venv`):

```text
.venv\Scripts\activate
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

Add `requirements.txt` (runtime: fastapi, uvicorn, pydantic; llama-cpp-python optional) and `requirements-dev.txt` (pytest), plus `pytest.ini`. pytest gets installed locally in this sandbox too so the suite is actually run before reporting.

## Phase 1 — Test foundation

```text
tests/__init__.py   conftest.py (shared agent/orchestrator/knowledge fixtures)
test_router.py      every intent + ambiguous input + empty input fallback
test_trade_formatter.py  forex/crypto symbols, no fabricated symbols, side,
                    entry/stop/target, balance, risk %, word-order variants,
                    and the exact roadmap input list as parametrized cases
test_tools.py       risk (5000/1%=50, 10000/2%=200, 2500/0.5%=12.5) + all
                    invalid inputs; R:R valid/invalid BUY and SELL;
                    position sizing EUR/USD, GBP/USD, JPY pair, crypto,
                    equal entry/stop rejection
test_orchestrator.py end-to-end: query in -> intent + max_risk_amount out
test_knowledge.py   retrieval acceptance table (Phase 3)
test_memory.py      session facts, isolation, bounded transcript
test_agent.py       facade surface (Phase 2)
```

Gate: `python -m pytest tests -q` fully green before Phase 2. Regressions get fixed, not skipped.

## Phase 2 — ShTraderAgent facade

New `shtrader_la/core/agent.py`: `ShTraderAgent` with `chat(query, session_id=None)`, `analyze_trade(trade_data)`, `calculate_risk(account_balance, risk_percent)`, `calculate_position_size(data)`, `health()`. It constructs provider/registry/knowledge/memory/router and delegates — zero business logic, zero math of its own. Orchestrator stays as-is internally.

## Phase 3 — Knowledge quality

Add missing documents under `shtrader_la/knowledge/documents/`: `forex-basics.md`, `crypto-basics.md`, `support-resistance.md`, `trading-psychology.md`, `liquidity.md`, `supply-demand.md`, `trading-plans.md`, `technical-analysis.md` (market-structure, trend-analysis, risk-management, risk-reward, position-sizing already exist). Each is real teaching content with a clear title and topic-dense body.

Retrieval: add title-field weighting and a definitional-query boost in `retrieval.py` so "what is forex" ranks `forex-basics` first. Acceptance tests assert top-1 for: what is forex, what is crypto, what is market structure, trading psychology, how does risk reward work, how do I manage risk — and that top-3 contains no unrelated doc.

## Phase 4 — Structured session memory

Introduce an explicit `SessionState` (account_balance, risk_percent, preferred_symbol, entry/stop when supplied) behind the existing `MemoryStore` interface, and make sure the orchestrator *uses* remembered facts to compute follow-ups. Target conversation, as a test:

```text
"My account is $5,000 and I risk 1%."  -> stores 5000 / 1
"What is my maximum risk?"             -> $50 from risk_calculator
"Position size for EUR/USD with a 50 pip stop?" -> 0.10 standard lots
```

Explicit request context still overrides memory; parsed text overrides stored facts.

## Phase 5 — Proposal-only integrations

`shtrader_la/integrations/`: `base.py` (`BaseIntegration` with `name`/`health()`), `market_data.py` (`get_price`, `get_candles`; local mock provider, prices only ever come from the provider), `user_data.py` (read-only profile), `execution.py` (produces a `TradeProposal` with `status="PROPOSED"` and has no code path that can execute — asserted by a test).

## Phase 6 — FastAPI backend

```text
shtrader_la/api/main.py, dependencies.py, schemas.py
shtrader_la/api/routes/{health,chat,risk,position,trade}.py
```

`GET /health`, `POST /api/v1/chat`, `/api/v1/risk/calculate`, `/api/v1/position-size`, `/api/v1/trade/analyze` — all delegating to `ShTraderAgent`, no duplicated math. `tests/test_api.py` via `TestClient`, skipped cleanly if FastAPI is absent.

## Phase 7 — CLI

`python -m shtrader_la.cli` — interactive `ShTrader LA >` prompt on the stub provider (no GGUF needed), formatted risk/position/analysis output, `exit` to quit.

## Docs

README: run commands, Windows PowerShell notes (escape `$` as `` `$ `` or use single quotes so `$5000` is not eaten by PowerShell), venv/pytest instructions, architecture summary; `REPORT.md` with the phase-by-phase result, exact test commands, and pass/fail counts.

## Invariants

Deterministic tools own every number; the model only narrates; router picks intent; provider stays optional with the stub working fully offline; no autonomous execution; no cloud calls. The web console at `src/routes/index.tsx` is untouched in this pass (Phase 8).
