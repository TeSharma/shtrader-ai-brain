# Shtrader LA — Step 1 & 2: ADTC-compliant scaffold + web console

Two deliverables in one repository:

1. `shtrader-la/` — the Python AI core (offline, llama.cpp, GGUF), laid out so the ADTC-required files sit at the repo root as the template demands.
2. The existing TanStack app becomes the **Shtrader LA Console** — a web UI that speaks the same API contract as the local core, with the deterministic trading math reimplemented in TypeScript so the console works before the local API is running.

Scope of this plan: repository scaffold, deterministic tools, agent orchestration skeleton, keyword knowledge retrieval, submission files, and the web console. No model download, inference run, or benchmark can happen inside this environment — those are local commands you run, and the plan ships the scripts and empty benchmark tables for them.

## ADTC compliance mapping

The template requires these at the **root** of the submitted repo:

```text
/
├── metadata.json        (2 test prompts, domain autonomous_ai_agents, budget_laptop_claim true)
├── download_model.sh    (fetches Llama-3.2-3B-Instruct-Q4_K_M.gguf -> model/)
├── REPORT.md            (problem, design, benchmarks)
├── model/               (gitignored)
├── .gitignore           (adds *.gguf, model/)
└── shtrader-la/         (the AI core; template allows extra files)
```

`.gitignore` gets `model/` and `*.gguf` appended. `download_model.sh` uses curl with a checksum print, resumable, no Python deps, and exits non-zero on failure.

## Python core layout (`shtrader-la/`)

```text
core/       agent.py, router.py, orchestrator.py, memory.py, schemas.py
llm/        base.py (LLMProvider), llama_cpp.py (LlamaCppProvider), config.py
tools/      base.py, registry.py, risk_reward.py, position_sizing.py,
            trade_analysis.py, trade_formatter.py
knowledge/  retrieval.py (KeywordKnowledgeProvider, BM25), documents/*.md
integrations/ base.py, market_data.py, user_data.py, execution.py  (interfaces + stubs)
api/        schemas.py, server.py (FastAPI: /analyze /chat /trade-plan
            /risk/calculate /position-size/calculate /health)
app/        cli.py
tests/      test_tools.py, test_agent.py, test_api.py
scripts/    run_local.sh, benchmark.sh
docs/       architecture.md, roadmap.md
```

Key contracts:

- `LLMProvider.generate(prompt, config)` — `LlamaCppProvider` wraps `llama-cpp-python`; a `StubProvider` lets tests and CI run with no weights.
- `Router` classifies intent with rules first (regex/keyword on symbols, prices, "risk %"), falling back to a single LLM classification call — cheap on CPU.
- `Orchestrator` runs: classify -> select tools -> run deterministic tools -> retrieve knowledge -> one LLM call with structured context -> return `AgentResponse` (human text + structured payload + disclaimer).
- Memory: `MemoryStore` interface, `SessionMemory` in-process implementation only.
- Execution: `propose_trade` returns a proposal object with `requires_authorization: true`. No execution path exists.

Deterministic tools (pure Python, no LLM):

- risk calculator: balance x risk% -> capital at risk
- risk/reward: entry/SL/TP/direction -> risk dist, reward dist, R:R, validity checks (SL on wrong side rejected)
- position sizing: interface supporting pip value, contract size, account currency; MVP implements linear (crypto/CFD-style) and forex pip-value sizing with a documented simplification
- trade plan parser: regex + dataclass validation, natural language -> `{symbol, side, entry, stop_loss, take_profit, risk_percent}`

Knowledge: 6-8 short markdown docs (risk management, position sizing, market structure, trend analysis, forex basics, crypto terms, trading psychology), indexed by a dependency-free BM25 implementation behind `KnowledgeProvider.search(query)`. An embedding provider can be dropped in later without touching the agent.

Tests use pytest and cover the tools, the router's intent classification, the parser, and the API routes against the stub provider — so `pytest` passes offline with no weights present.

## Web console (this app)

Routes:

- `/` — Shtrader LA console: intent-aware chat panel, structured-output inspector (renders the JSON payload the Python core returns), disclaimer banner.
- `/tools` — risk calculator, risk/reward calculator, position sizing, trade plan parser, all running the TypeScript ports of the deterministic math instantly in the browser.
- `/architecture` — the two-layer intelligence/execution diagram, integration adapter story, roadmap phases.

`src/lib/la/` holds the TS ports (`riskReward.ts`, `positionSizing.ts`, `tradePlanParser.ts`, `types.ts`) plus `client.ts`, a fetch client for the local API base URL (configurable in the UI, defaults `http://localhost:8000`). When the local core is unreachable the console stays useful: tools work locally and chat shows a clear "local agent offline" state. No cloud AI is called.

Design direction: dark terminal-adjacent trading console — near-black base, amber/green signal accents, monospace for numbers, tabular data density. All values as semantic tokens in `src/styles.css`; no hardcoded color utilities.

Each content route gets its own `head()` with unique title/description/og tags.

## Documentation and reporting

- `REPORT.md`: problem framing, offline-first rationale, architecture, model selection reasoning, benchmark table (headers + method, values to be filled from your local run), risk/limitations, no-financial-advice statement.
- `docs/architecture.md`: layer separation, interfaces, why no multi-agent framework.
- `docs/roadmap.md`: phases A/B/C.
- `shtrader-la/README.md` and root `README.md`: exact local commands for `download_model.sh`, `pytest`, CLI, API, `adtc-profiler run`.

## What you must run locally (cannot run here)

```text
bash download_model.sh
pip install -r shtrader-la/requirements.txt
python -m shtrader_la.app.cli            # or scripts/run_local.sh
bash shtrader-la/scripts/benchmark.sh    # fills the REPORT.md table
pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"
adtc-profiler run --submission . --mode participant --output submission.json --skip-accuracy
```

I will report back after the scaffold with: files created, what works, how to run it, tests written, blockers, and the recommended next step (model benchmarking).

## Open item

`metadata.json` needs your real `team_id`, name, email, and github handle. I will fill everything else (domain `autonomous_ai_agents`, model block for Llama-3.2-3B-Instruct Q4_K_M, two trading-domain test prompts, cross-disciplinary pairing = finance, load_bearing true) and mark only those four fields with an obvious `FILL_ME` marker plus a checklist line in the README, unless you paste them.
