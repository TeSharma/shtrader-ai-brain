# ShTrader LA — pre-submission hardening plan

## Baseline observed just now

- Branch: `edit/edt-de5712e2-...`, working tree clean.
- Python core present: `core/` (router, orchestrator, memory, prompts, schemas), `tools/` (risk_reward, position_sizing, trade_formatter, trade_analysis, registry), `knowledge/` (BM25 retrieval + 5 docs), `llm/` (base, config, llama_cpp).
- **Missing entirely**: `core/agent.py`, FastAPI app (`api/` holds only `__init__.py`), CLI (`app/` holds only `__init__.py`), `integrations/` implementations, `REPORT.md`, `requirements.txt` / `pyproject.toml`, `model/` directory, and tests for orchestrator/knowledge/memory.
- Tests present: `test_router.py`, `test_tools.py`, `test_trade_formatter.py`. **`python -m pytest` cannot run here** — pytest is not installed in this sandbox's Python env and the env is read-only in places, so the baseline "61 passed, 2 failed" you reported is the number I will work against. I will re-verify by installing pytest into a local `.venv` at the start of the work.
- `.gitignore` already excludes `model/`, `*.gguf`, `__pycache__/`, `.venv/`. `metadata.json` still contains `FILL_ME_*` placeholders.
- Frontend is the TanStack app in `src/`; `src/routes/index.tsx` is still the blank placeholder — no console UI exists yet.

## What I cannot verify inside this environment (must run on your laptop)

- `bash download_model.sh` (2 GB GGUF pull) and real llama.cpp inference — no GGUF and no `llama-cpp-python` build here.
- `adtc-profiler run ... --mode participant` — the profiler binary is not installed here, and `measured_on: participant_laptop` is only meaningful when measured on your machine.

So this plan makes those paths **correct and runnable**, ships a `scripts/verify_offline.py` preflight, and gives you exact commands. I will not claim they passed.

## Work

### 1. Router fixes (Phase 1) + regression tests
Adjust `core/router.py` inside the existing signal architecture — no string-literal exception lists:
- Add a `conceptual` override: when a definitional lead-in (`what is`, `define`, `explain`, `what does ... mean`, `difference between`) is present and no trade numbers/levels appear, force `KNOWLEDGE_QUERY` regardless of topic keywords ("define position sizing" currently loses to the sizing keyword).
- Add a `sizing_request` signal (`position size`, `lot size`, `how many lots/units`, `size my`). When present, `POSITION_SIZING` outranks both `TRADE_ANALYSIS` (levels present) and `RISK_CALCULATION` (balance+risk% present). This fixes both the `entry 1.1000 stop 1.0950` case and the `50 pip stop` case.
- Keep `TRADE_ANALYSIS` for level-bearing queries without a sizing request; keep `TRADING_PLAN` on plan wording.
- New tests in `tests/test_router.py` for every query listed in Phases 1 and 8.

### 2. Trade formatter (Phase 2)
Verify all listed cases against the current claim-based parser; add `stop_pips` claiming (`50 pip stop`, `stop 50 pips`) to `TradeIdea` and its dict output if not already carried through. Add `tests/test_trade_formatter.py` cases for the full Phase 2 list, including `$5000` forms.

### 3. Deterministic tools (Phase 3)
Add tests asserting the exact expected numbers (risk 50 / 200 / 12.50; EUR/USD 3:1, 50 pips, 0.02 lots / 2000 units, $10 risk; GBP/USD 2:1) plus every invalid case (SL on wrong side, missing entry/SL/TP, non-positive balance, non-positive risk, excessive risk). Formulas change only where a test exposes a genuine arithmetic error.

### 4. Agent facade, API, CLI
- `core/agent.py`: `ShTraderAgent` facade wrapping provider selection + `Orchestrator`, exposing `ask()` and `status()` (model loaded?, tool count, knowledge doc count, offline flag).
- `shtrader_la/api/server.py`: FastAPI app — `GET /health`, `GET /status`, `POST /query`, `GET /tools`. CORS allowing localhost origins plus the Lovable preview origin so the browser console can reach `127.0.0.1:8000`.
- `shtrader_la/app/cli.py`: `python -m shtrader_la.app.cli` one-shot and interactive REPL (matches `metadata.json` entrypoint).
- `requirements.txt` (fastapi, uvicorn, pydantic, pytest) and `requirements-model.txt` (llama-cpp-python) so core install never pulls the model runtime.

### 5. ADTC submission structure (Phase 4)
- Fill `metadata.json` from your real details (see question below); keep exactly 2 test prompts.
- Create `model/.gitkeep` + `model/README.md`; confirm no GGUF tracked.
- Write `REPORT.md` covering problem, architecture, design decisions, offline constraints, model choice, quantization, deterministic tools, knowledge retrieval, benchmarks/testing, limitations.
- Rewrite `README.md`: setup, `download_model.sh`, run API, run CLI, run console, run tests, profiler command.

### 6. Offline validation (Phase 5)
`scripts/verify_offline.py` asserts: no API-key env read anywhere in `shtrader_la/`, no cloud SDK imports, tools + retrieval run with zero network, GGUF path resolves, and prints a PASS/FAIL table. You then run `download_model.sh`, the inference command, and the profiler; I fix whatever the output shows.

### 7. Demo console (Phases 6–7)
Rewrite `src/routes/index.tsx` as the console — dark trading/AI aesthetic via `src/styles.css` tokens, no animations, no fake data:
- Header "ShTrader LA — Offline AI Trading Intelligence".
- Status strip: OFFLINE / LOCAL MODEL (`local_model` vs `deterministic_only`, honest) / DETERMINISTIC TOOLS / KNOWLEDGE BASE, polled from `/status`; explicit "backend not reachable" state with the exact start command when the API is down.
- Query box + the 4 example prompt buttons.
- Result area rendering only what the backend returns: intent, confidence, model mode, tools used, calculations, knowledge sources, warnings, recommendations — with dedicated layouts for risk (big `$50.00`), sizing (risk amount / stop distance / size / lots / units), trade analysis (symbol → warnings), and knowledge (answer + sources).
- Backend base URL from `VITE_SHTRADER_API_URL`, default `http://127.0.0.1:8000`, editable in a settings field. **No financial math in TypeScript** — the console posts to `/query` and renders.

### 8. End-to-end + green suite (Phases 8–10)
Drive every Phase 8 query through the FastAPI path (httpx/TestClient script committed as `tests/test_api_e2e.py`), then `python -m pytest tests -q` until 0 failed / 0 errors, then a repo audit (`git status`, no GGUF, no keys, no placeholders).

## Reporting
I will close with only the requested headings: TEST RESULTS, ROUTER RESULTS, TOOL RESULTS, FRONTEND, ADTC SUBMISSION, PROFILER, REMAINING BLOCKERS — marking profiler and real-GGUF inference as "requires your laptop" rather than claiming a pass.

## One thing I need from you
`metadata.json` needs your real `team_id`, full name, email, and GitHub handle — I cannot invent those and placeholders fail submission validation. Paste them and I will fill the file in this pass; otherwise I leave the placeholders and flag it as a blocker.
