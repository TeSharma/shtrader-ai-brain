# Technical Report — Shtrader LA: Offline AI Trading Assistant

**Team ID:** [YOUR DEVPOST PROJECT ID]
**Domain:** Autonomous AI Agents
**Model:** [FINAL GGUF MODEL NAME]

---

## 1. Problem

### 1.1 Problem Definition

Financial trading tools are increasingly dependent on cloud services, proprietary platforms, and internet connectivity. This creates a practical limitation for users operating on bandwidth-constrained environments or hardware that cannot reliably support cloud-connected AI applications.

Shtrader LA addresses this problem by building an AI-native trading assistant designed to operate locally on consumer laptop hardware. The system combines a local language model with deterministic financial tools and an offline knowledge base to provide trading education, risk analysis, position-sizing guidance, and structured trade-plan assistance without requiring a cloud AI provider.

The target users are retail traders, trading students, and financially interested users who need accessible trading intelligence without depending entirely on centralized AI services.

### 1.2 Why Local AI Matters

Trading assistance often involves sensitive financial information such as account size, risk tolerance, position size, and trade plans. A locally running assistant can process this information without sending the user's prompts to a remote AI provider.

Local inference also makes the system more useful in environments where internet connectivity is limited, expensive, unreliable, or unavailable.

Shtrader LA therefore treats offline execution as a core product requirement rather than simply an optimization.

---

## 2. Solution Overview

Shtrader LA is an offline-first AI trading assistant built around four main layers:

1. **Intent Router**
2. **Orchestrator**
3. **Deterministic Trading Tools + Offline Knowledge Retrieval**
4. **Local GGUF Language Model running through llama.cpp**

The intended processing flow is:

```text
User Query
    ↓
Intent Router
    ↓
Orchestrator
    ├── Deterministic Trading Tools
    ├── Offline BM25 Knowledge Retrieval
    └── Local GGUF LLM via llama.cpp
    ↓
Natural-Language Response
```

The architecture separates numerical calculations from language generation. Deterministic tools are responsible for calculations such as risk and position sizing, while the language model is responsible for interpreting the request, using retrieved context, and composing a natural response.

This separation reduces the risk of the language model generating incorrect financial calculations.

---

## 3. Design Decisions

### 3.1 Local GGUF Model

Shtrader LA is designed around a GGUF-compatible language model that can run through `llama.cpp`.

GGUF was selected because it provides a practical format for quantized local language-model inference and is compatible with the execution requirements of the ADTC Laptop LLM challenge.

The final model and quantization will be selected based on the balance between:

* response quality,
* memory consumption,
* inference speed,
* and suitability for the ADTC standard laptop.

**Final model:** [FILL AFTER FINAL MODEL IS SELECTED]
**Quantization:** [FILL AFTER FINAL MODEL IS SELECTED]

### 3.2 llama.cpp

`llama.cpp` is used as the local inference runtime.

It was selected because the ADTC evaluation environment requires the submitted model to run through llama.cpp and because it enables CPU-based inference without requiring a discrete GPU.

### 3.3 Deterministic Trading Tools

Financial calculations are intentionally handled by deterministic Python tools rather than being left entirely to the language model.

The system includes tools for tasks such as:

* risk calculation,
* risk/reward analysis,
* position sizing,
* and trade-plan parsing.

For example, when a user asks:

> "I have a $5,000 account and risk 1%. How much can I lose?"

the deterministic risk calculator calculates the maximum risk as $50.

The language model can then explain that result naturally to the user without changing the numerical result.

This design was chosen because numerical correctness is particularly important in financial applications.

### 3.4 Offline Knowledge Retrieval

Shtrader LA uses a lightweight BM25 keyword-retrieval approach for its knowledge layer.

The knowledge base contains locally stored trading documents covering topics such as:

* risk management,
* position sizing,
* risk/reward,
* and trading concepts.

BM25 was selected instead of a larger embedding-based retrieval stack because it provides useful retrieval while keeping the system lightweight, deterministic, and suitable for constrained laptop hardware.

No external vector database or cloud retrieval service is required.

### 3.5 Orchestrator Architecture

The orchestrator coordinates the complete request pipeline.

Depending on the user's request, it can:

1. classify the user's intent,
2. select appropriate deterministic tools,
3. execute calculations,
4. retrieve relevant offline knowledge,
5. provide the resulting context to the local language model,
6. and compose the final response.

This architecture allows the system to combine deterministic computation with natural-language reasoning while keeping the core workflow local.

---

## 4. Alternatives Considered

### 4.1 Cloud-Based LLM APIs

Cloud APIs were not selected as the primary inference mechanism.

Although services such as hosted LLM APIs provide strong language performance, they introduce:

* internet dependency,
* external API dependency,
* potential privacy concerns,
* network latency,
* and recurring service costs.

These limitations conflict with the goal of building an AI assistant capable of running locally on constrained hardware.

### 4.2 Embedding-Based Retrieval

A local embedding-based retrieval system was considered.

However, BM25 was selected for the initial implementation because it provides a much smaller dependency footprint and does not require additional embedding models or vector infrastructure.

This makes the retrieval layer easier to run offline and reduces memory and compute requirements.

### 4.3 LLM-Based Financial Calculations

Allowing the language model to perform all financial calculations was rejected.

Instead, deterministic tools perform calculations such as account risk and position sizing.

This provides a more reliable separation between:

* **computation**, handled deterministically;
* **knowledge retrieval**, handled locally;
* **language generation**, handled by the local LLM.

---

## 5. Constraints

### 5.1 Hardware

Shtrader LA is designed for the ADTC standard laptop environment.

The target environment includes:

* approximately 8 GB RAM,
* integrated graphics,
* CPU-based inference,
* and constrained consumer laptop hardware.

The model must remain within the challenge's memory constraints while providing useful responses.

### 5.2 Compute

Because the target device does not assume a discrete GPU, the system is designed around CPU-compatible local inference.

Model selection and quantization therefore need to balance response quality against:

* inference speed,
* RAM usage,
* and thermal load.

### 5.3 Connectivity

The core AI workflow is designed to operate without an internet connection.

The language model, knowledge base, and deterministic tools are intended to be available locally.

External network access is not required for the core inference workflow.

### 5.4 Data Availability

The knowledge layer uses locally stored documents rather than relying on live web search or cloud retrieval.

This ensures that the assistant remains functional when network connectivity is unavailable.

### 5.5 Financial Safety

Shtrader LA is an informational trading assistant.

It does not execute trades on behalf of the user.

Deterministic tools are used to calculate risk-related values, while responses include appropriate informational disclaimers.

---

## 6. Tools and Technologies

### Programming and Application Layer

* Python
* FastAPI
* React
* TypeScript
* TanStack
* Node.js

### AI / Inference

* llama.cpp
* GGUF model format
* Local language-model inference

### Knowledge Retrieval

* BM25 keyword retrieval
* Local Markdown knowledge documents

### Deterministic Trading Tools

* Risk calculator
* Position sizing calculator
* Risk/reward calculator
* Trade-plan parser

### Development and Testing

* pytest
* TypeScript compiler
* ADTC profiler
* Git/GitHub

---

## 7. Performance and Benchmarks

The following values are intended to be measured on the development machine and reported as self-reported development benchmarks.

| Metric              | Value                |
| ------------------- | -------------------- |
| Machine             | [FILL IN]            |
| CPU                 | [FILL IN]            |
| RAM                 | [FILL IN]            |
| Model               | [FILL IN]            |
| Quantization        | [FILL IN]            |
| Peak RAM            | [FILL IN]            |
| Time to first token | [FILL IN]            |
| Generation speed    | [FILL IN] tokens/sec |
| Thermal throttling  | [FILL IN]            |

These are development measurements. Official ADTC scores are determined using the ADTC evaluation environment and profiler.

---

## 8. Functional Testing

The application has been tested across its main deterministic components and API workflow.

Example:

### Risk Calculation

Input:

> I have a $5,000 account and risk 1%. How much can I lose?

Deterministic result:

> Maximum capital at risk: $50.

The system correctly calculates:

* Account balance: $5,000
* Risk percentage: 1%
* Maximum risk: $50
* Remaining balance after the maximum loss: $4,950

### Knowledge Retrieval

The offline knowledge system successfully retrieves relevant documents for trading questions involving:

* risk management,
* position sizing,
* and risk/reward concepts.

### API

The local Shtrader LA API exposes the AI assistant through the application API and supports local chat requests.

### Test Suite

Automated project tests have been used to validate the core functionality.

**Latest test result:** 66 tests passed.

---

## 9. Offline Operation

A central requirement of Shtrader LA is that the core intelligence can operate locally.

The intended production/evaluation workflow is:

```text
Local Laptop
    │
    ├── Shtrader LA Application
    │
    ├── Local GGUF Model
    │
    ├── llama.cpp
    │
    ├── Offline Knowledge Base
    │
    └── Deterministic Trading Tools
            │
            ▼
       AI Response
```

The system does not require a cloud LLM API for its core inference.

This architecture is intended to make the assistant practical in low-connectivity environments and on affordable consumer hardware.

---

## 10. Current Limitations

The current prototype is still under active development.

The primary remaining engineering tasks are:

1. Finalizing the local GGUF model selection.
2. Connecting the final GGUF model to the LLM provider layer.
3. Completing local llama.cpp inference validation.
4. Running the complete ADTC profiler workflow.
5. Recording final memory, throughput, and thermal benchmarks.
6. Refining natural-language response composition around deterministic tool results.
7. Completing final submission documentation and demonstration materials.

These limitations are part of the prototype-development stage and will be addressed before the final model package is submitted.

---

## 11. Development Journey

Shtrader LA began from the idea of creating a trading assistant that could combine financial-domain knowledge with AI reasoning.

The project evolved toward an offline-first architecture after identifying the practical limitations of cloud-dependent AI systems on constrained hardware.

The development process focused on progressively separating responsibilities:

* deterministic financial calculations were isolated into tools;
* trading knowledge was moved into an offline retrieval layer;
* intent classification and orchestration were separated from computation;
* and the language-model layer was designed around local GGUF inference through llama.cpp.

This architecture allows the project to demonstrate how a domain-specific AI assistant can be designed for real-world hardware and connectivity constraints rather than assuming access to high-end cloud infrastructure.

---

## 12. Conclusion

Shtrader LA is an offline-first AI trading assistant designed for practical deployment on consumer laptop hardware.

Its key architectural principle is to combine:

**local language-model inference + deterministic financial tools + offline knowledge retrieval**

rather than relying on a cloud chatbot to perform every task.

The project aims to demonstrate that useful domain-specific AI assistance can be built around constrained hardware while maintaining a strong separation between language generation and numerical financial computation.

The final evaluation will focus on the quality, efficiency, and resource requirements of the selected local GGUF model under the ADTC evaluation environment.
