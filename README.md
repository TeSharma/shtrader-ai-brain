# Shtrader Agent Core

Shtrader LA — Modular AI Brain & Hackathon Build Specification

1. Project Vision

Build Shtrader LA (Local Agent) as a modular, offline-first AI intelligence engine.

The immediate goal is to submit Shtrader LA to the Africa Deep Tech Challenge 2026 under the Autonomous AI Agents domain. The system must run a useful language-model-powered agent locally on commodity hardware, including laptops with approximately 8 GB RAM and integrated graphics.

However, the architecture must also support the long-term vision:

Shtrader LA will become the intelligence layer—or “AI brain”—of the broader Shtrader decentralized trading platform.

Therefore, do not build a one-off hackathon chatbot. Build a modular AI core with clean interfaces that can later connect to the Shtrader web application, market-data services, Supabase backend, blockchain infrastructure, and trading execution systems.

The hackathon version must remain fully functional offline and independent of cloud AI APIs.

2. Product Definition

Shtrader LA is an AI agent designed to help users understand markets, analyze trading scenarios, manage risk, structure trading plans, and automate trading research workflows.

For the hackathon, the core system should provide:

 Trading and market reasoning

 Strategy analysis

 Risk/reward analysis

 Position and account risk calculations

 Trading plan generation

 Structured extraction of trade ideas

 Local knowledge retrieval

 Tool-based workflow automation

The system must not claim to guarantee profits or autonomously execute real trades.

The product positioning is:

Shtrader LA is an offline-first AI trading intelligence engine that brings market analysis, risk management, and workflow automation to commodity laptops without requiring expensive cloud AI infrastructure or constant internet access.

3. Long-Term Shtrader Architecture

Design the project so it can evolve into:

                         SHTRADER ECOSYSTEM

 ┌──────────────────────────────────────────────────────────────┐

 │                       Shtrader Platform                      │

 │                                                              │

 │  Web App / Mobile App                                        │

 │          │                                                   │

 │          ▼                                                   │

 │       API Layer                                              │

 │          │                                                   │

 └──────────┼───────────────────────────────────────────────────┘

            │

            ▼

 ┌──────────────────────────────────────────────────────────────┐

 │                     SHTRADER LA CORE                         │

 │                                                              │

 │  ┌───────────────┐     ┌──────────────────┐                 │

 │  │ Agent Router  │────▶│ Reasoning Engine │                 │

 │  └───────────────┘     └──────────────────┘                 │

 │          │                         │                         │

 │          ▼                         ▼                         │

 │  ┌───────────────┐     ┌──────────────────┐                 │

 │  │ Tool Registry │     │ Knowledge Engine │                 │

 │  └───────────────┘     └──────────────────┘                 │

 │          │                         │                         │

 │          ▼                         ▼                         │

 │  Risk Engine              Market Knowledge                  │

 │  Position Sizing          Strategy Knowledge                │

 │  Trade Analysis           User Context                      │

 │                                                              │

 └───────────────────────────┬──────────────────────────────────┘

                             │

                  Future Integrations

                             │

          ┌──────────────────┼──────────────────┐

          ▼                  ▼                  ▼

      Market Data        Supabase         Trading Execution

      Providers          Backend          / Smart Contracts

The AI core must not directly depend on these future services to function.

Use adapters and interfaces so integrations can be added later.

4. Critical Architectural Principle

Separate the system into two layers:

Intelligence Layer

Responsible for:

 Understanding user intent

 Reasoning

 Planning

 Analyzing data

 Selecting tools

 Explaining results

 Structuring outputs

Execution Layer

Responsible for:

 Fetching live market data

 Accessing user information

 Connecting wallets

 Interacting with blockchain infrastructure

 Executing trades

 Managing permissions

The AI must never directly execute sensitive actions without an explicit authorization layer.

The long-term flow should be:

User Request

     │

     ▼

Shtrader LA analyzes and creates a proposal

     │

     ▼

Structured Action Plan

     │

     ▼

User Review / Authorization

     │

     ▼

Execution Layer

     │

     ▼

Blockchain / Broker / Trading Infrastructure

5. Core Technology Stack

For the initial hackathon build:

AI Runtime

Use:

llama.cpp

 GGUF-compatible models

 Quantized local inference

The inference layer must be abstracted.

Do not tightly couple the application logic to one specific model.

Create an interface similar to:

class LLMProvider:

def generate(self, prompt, config):

pass

Initial implementation:

LlamaCppProvider

Future implementations may include:

LocalModelProvider

CloudModelProvider

FineTunedShtraderModelProvider

The hackathon version must use local inference only.

6. Repository Structure

Use a structure similar to:

shtrader-la/

├── README.md

├── REPORT.md

├── metadata.json

├── requirements.txt

├── .gitignore

├── download_model.sh

│

├── core/

│   ├── agent.py

│   ├── router.py

│   ├── orchestrator.py

│   ├── memory.py

│   └── schemas.py

│

├── llm/

│   ├── base.py

│   ├── llama_cpp.py

│   └── config.py

│

├── tools/

│   ├── base.py

│   ├── registry.py

│   │

│   ├── risk_reward.py

│   ├── position_sizing.py

│   ├── trade_analysis.py

│   └── trade_formatter.py

│

├── knowledge/

│   ├── retrieval.py

│   └── documents/

│

├── integrations/

│   ├── base.py

│   ├── market_data.py

│   ├── user_data.py

│   └── execution.py

│

├── api/

│   ├── schemas.py

│   └── server.py

│

├── app/

│   └── cli.py

│

├── tests/

│   ├── test_tools.py

│   ├── test_agent.py

│   └── test_api.py

│

├── scripts/

│   ├── run_local.sh

│   └── benchmark.sh

│

└── docs/

    ├── architecture.md

    └── roadmap.md

Adapt this as needed to comply with the official hackathon submission structure.

7. Agent Architecture

Do not use an unnecessarily heavy multi-agent framework.

Build a lightweight orchestrator.

The workflow should be:

User Input

    │

    ▼

Intent Classification

    │

    ├── General Trading Question

    ├── Risk Calculation

    ├── Trade Analysis

    ├── Trading Plan

    └── Knowledge Query

           │

           ▼

     Select Tools / Retrieval

           │

           ▼

     Gather Structured Results

           │

           ▼

       Local LLM

           │

           ▼

 Structured Response

The agent should return both:

 Human-readable output

 Structured data when appropriate

For example:

{

  "intent": "trade_analysis",

  "market": "EUR/USD",

  "direction": "long",

  "entry": 1.0800,

  "stop_loss": 1.0750,

  "take_profit": 1.0950,

  "risk_reward": 3.0,

  "analysis": "..."

}

This is important because the future Shtrader platform should be able to consume the agent's output programmatically.

8. Deterministic Trading Tools

LLMs should not perform critical calculations alone.

Create deterministic tools.

Risk Calculator

Input:

 Account balance

 Risk percentage

Output:

 Maximum capital at risk

Example:

Balance: $1,000

Risk: 1%

Maximum Risk: $10

Risk/Reward Calculator

Input:

 Entry

 Stop loss

 Take profit

 Direction

Calculate:

 Risk distance

 Reward distance

 Risk/reward ratio

Position Sizing Engine

Design the interface now, even if the first implementation supports simplified calculations.

Future versions should support:

 Forex pairs

 Pip values

 Account currency

 Leverage constraints

 Crypto assets

Trade Plan Parser

Convert natural language into structured data.

Example:

Input:

Buy EUR/USD near 1.0800. Stop at 1.0750. Target 1.0950. Risk 1%.

Output:

{

  "symbol": "EUR/USD",

  "side": "BUY",

  "entry": 1.0800,

  "stop_loss": 1.0750,

  "take_profit": 1.0950,

  "risk_percent": 1

}

Use validation schemas to ensure clean data.

9. Knowledge Engine

Build a lightweight local retrieval system.

Avoid heavy infrastructure.

The first version should support:

knowledge/documents/

Possible content:

 Risk management

 Position sizing

 Market structure

 Trend analysis

 Forex fundamentals

 Crypto terminology

 Trading psychology

Create a retrieval interface:

class KnowledgeProvider:

def search(self, query):

pass

Initial implementation can use lightweight keyword or local semantic search.

Future implementations should support:

 User trading journals

 Personal strategy documents

 Historical trade data

 Custom knowledge bases

Do not hardcode knowledge directly into prompts.

10. Memory Architecture

Design the agent with modular memory.

Initial hackathon version:

 Session-only memory

 Local storage

 No cloud dependency

Future versions:

Short-Term Memory

      │

      ▼

Session Context

      │

      ▼

User Memory Layer

      │

      ├── Trading Preferences

      ├── Risk Profile

      ├── Strategy Preferences

      └── Historical Interactions

Do not build complex persistent user memory yet.

Create interfaces that allow it to be added later.

11. API-First Future Integration

The AI core should eventually be accessible through an API.

After the CLI works, create a lightweight local API.

Possible endpoints:

POST /analyze

POST /chat

POST /trade-plan

POST /risk/calculate

POST /position-size/calculate

GET /health

Example:

POST /analyze

{

  "query": "Analyze this EUR/USD trade idea",

  "context": {

    "entry": 1.0800,

    "stop_loss": 1.0750,

    "take_profit": 1.0950

  }

}

Response:

{

  "analysis": "...",

  "risk_reward": 3.0,

  "recommendations": [],

  "disclaimer": "Informational only. Not financial advice."

}

The future Shtrader React application should be able to integrate with this API without changing the AI core.

12. Future Integration Adapters

Create interfaces, but do not implement unnecessary live integrations for the hackathon.

Examples:

class MarketDataProvider:

def get_price(self, symbol):

pass

Future implementations:

CachedMarketDataProvider

PolygonMarketDataProvider

ExternalForexProvider

Execution interface:

class ExecutionProvider:

def propose_trade(self, trade):

pass

Important:

For now, return proposals only.

Do not implement real-money execution.

The future Shtrader platform can implement:

PolygonExecutionProvider

SmartContractExecutionProvider

PaperTradingProvider

This keeps the AI brain independent from the blockchain layer.

13. Offline-First Requirements

For hackathon evaluation:

The following must work without internet:

 Model inference

 Agent routing

 Trading calculations

 Knowledge retrieval

 CLI

 Local API

The model must:

 Be local

 Use GGUF

 Be quantized

 Run efficiently on 8 GB RAM

Do not require:

 API keys

 Cloud databases

 Internet connectivity

 External LLM services

Optional future integrations may require connectivity, but they must never break offline functionality.

14. Performance Optimization

The hackathon target environment is resource-constrained.

Optimize for:

 Low RAM usage

 High tokens per second

 Stable CPU temperatures

 Good response quality

Benchmark:

 Multiple candidate models

 Multiple GGUF quantizations

 Context sizes

 Thread counts

Record:

Model

Quantization

RAM

Tokens/sec

CPU usage

Temperature

Response quality

Select the best overall configuration.

Avoid:

 Docker

 Heavy orchestration frameworks

 Multiple simultaneous models

 Large vector databases

 GPU requirements

15. Build Phases

Phase A — Hackathon MVP

Priority:

 Local GGUF model

 llama.cpp integration

 CLI

 Agent router

 Risk tools

 Trade analysis

 Local knowledge retrieval

 Benchmarks

 Official submission compatibility

Phase B — Shtrader AI Core

After the hackathon:

 Persistent agent memory

 Advanced trading tools

 Market-data adapters

 User context

 Local API

 React platform integration

 Supabase integration

 User-specific knowledge

 Advanced strategy analysis

Phase C — AI-Native Trading Infrastructure

Future:

Market Data

     │

     ▼

Shtrader LA

     │

     ▼

Trade Proposal

     │

     ▼

Risk Validation

     │

     ▼

User Authorization

     │

     ▼

Execution Layer

     │

     ▼

Polygon / Other Supported Infrastructure

No autonomous execution should bypass authorization or risk controls.

16. Immediate Development Order

Start now in this exact order:

Step 1

Inspect the official Africa Deep Tech Challenge submission template and profiler.

Step 2

Create the repository structure while preserving compatibility with the required submission format.

Step 3

Install and test llama.cpp.

Step 4

Identify and test 2–3 lightweight GGUF instruct models.

Step 5

Benchmark:

 Tokens per second

 RAM

 Response quality

Step 6

Select the best model.

Step 7

Build the local CLI.

Step 8

Build deterministic trading tools and automated tests.

Step 9

Implement lightweight intent routing and agent orchestration.

Step 10

Add local knowledge retrieval.

Step 11

Run the official profiler.

Step 12

Document all architecture and benchmark decisions.

17. Acceptance Criteria

The initial version is complete when:

Hackathon Requirements

 Runs on commodity hardware with 8 GB RAM

 Works without cloud AI APIs

 Uses a local quantized GGUF model

 Uses llama.cpp-compatible inference

 Can be reproduced from the repository

 Model download is automated

 Performance is benchmarked

 RAM usage is measured

 Tokens per second are measured

 Submission follows official ADTC requirements

Product Requirements

 User can ask trading questions

 Agent routes requests appropriately

 Deterministic tools handle calculations

 Agent produces structured outputs

 Local knowledge retrieval works

 CLI works offline

 Local API architecture is ready or implemented

 Code is modular and testable

 No future Shtrader integration is hardcoded into the AI core

18. Development Rules

Do not build a disposable hackathon demo.

 Build reusable production-oriented modules.

 Keep the hackathon MVP small and efficient.

 Prioritize working local inference over UI.

 Use deterministic code for calculations.

 Keep external integrations behind interfaces/adapters.

 Keep AI reasoning separate from execution.

 Never execute financial actions without explicit authorization.

 Document every major technical decision.

 Report progress after every major implementation step.

At the end of each step, provide:

 Files created/modified

 What works

 How to run it

 Tests performed

 Benchmark results

 Current blockers

 Recommended next step


```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```

## Running the web console against the local engine

The chat console talks to the Shtrader LA Python engine over a local FastAPI
server (`src/lib/la/` is just a typed fetch client — no math is re-implemented
in TypeScript). Run the two processes in separate terminals:

```sh
# Terminal 1 — start the Python engine API (port 8000 by default)
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn shtrader_la.api.app:app --host 0.0.0.0 --port 8000

# Terminal 2 — start the web console (Vite)
npm run dev
```

Endpoints:

- `GET /health` — `{ "status", "provider", "model_active", "mode" }`
- `POST /api/v1/chat` — body `{ "query", "session_id" }`, returns the agent's
  `intent`, `answer`, `structured`, `tool_results`, `knowledge`, `recommendations`
  and `disclaimer`.

The engine runs fully offline with its deterministic `StubProvider` by default —
no GGUF weights or internet needed. To use a real local model, drop a `.gguf`
into `model/`, install `llama-cpp-python`, and restart.

If the console can't reach the API, chat shows a clear "local agent offline"
message with the exact command to start the server. Override the API address at
dev time with `VITE_SHTRADER_API_URL` (default `http://127.0.0.1:8000`).
