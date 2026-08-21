# Shtrader LA — Hackathon Acceptance Checklist

## Core

- [ ] Python modules compile successfully
- [ ] Router classifies deterministic intents correctly
- [ ] Orchestrator connects router → tools → knowledge → LLM
- [ ] AgentResponse is returned consistently
- [ ] StubProvider works without GGUF
- [ ] Real Llama.cpp provider can be selected when GGUF exists

## Router

- [ ] "what is risk reward" → knowledge_query
- [ ] "what is market structure" → knowledge_query
- [ ] "explain position sizing" → position_sizing or knowledge_query according to policy
- [ ] "calculate my risk on a 5000 account risking 1%" → risk_calculation
- [ ] "calculate position size for EUR/USD" → position_sizing
- [ ] Full trade setup → trade_analysis

## Deterministic tools

- [ ] Risk calculator produces exact risk amount
- [ ] Risk/reward calculator produces exact R:R
- [ ] Position sizing produces exact lot size
- [ ] Trade parser extracts setup fields
- [ ] Trade analysis combines deterministic tools

## Knowledge

- [ ] Market structure retrieval works
- [ ] Risk management retrieval works
- [ ] Risk/reward retrieval works
- [ ] Forex basics document exists
- [ ] Crypto terminology document exists
- [ ] Trading psychology document exists

## Safety

- [ ] AI never computes financial numbers itself
- [ ] AI never executes trades
- [ ] Execution interface only creates proposals
- [ ] Proposal requires authorization
- [ ] API cannot directly execute trades

## API

- [ ] FastAPI starts
- [ ] Health endpoint works
- [ ] Agent endpoint works
- [ ] Tool listing works
- [ ] API uses same core contracts

## CLI

- [ ] CLI works with StubProvider
- [ ] CLI can submit a trading question
- [ ] CLI can submit a trade setup
- [ ] CLI displays structured results

## Web

- [ ] Homepage demonstrates Shtrader LA
- [ ] Tools page lists deterministic tools
- [ ] Architecture page explains system
- [ ] Web console consumes API
- [ ] No placeholder homepage

## Tests

- [ ] schemas tests pass
- [ ] router tests pass
- [ ] orchestrator tests pass
- [ ] tools tests pass
- [ ] parser tests pass
- [ ] BM25 tests pass
- [ ] API tests pass
- [ ] proposal/authorization tests pass

## Final validation

- [ ] python -m compileall shtrader_la
- [ ] pytest passes
- [ ] API starts
- [ ] CLI demo works
- [ ] Web console works
- [ ] GGUF inference works
- [ ] README commands work
- [ ] Demo can be completed in <5 minutes