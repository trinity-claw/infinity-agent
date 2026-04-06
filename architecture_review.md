# Architecture Review - Infinity Agent (Current)

This is the active architecture review for the current implementation.

> Legacy planning artifacts were archived to `docs/archive/`.

## 1) System Purpose

Infinity Agent is a multi-agent support system for InfinitePay challenge scenarios.
It handles:
- product/feature Q&A with RAG grounding
- account/support troubleshooting via tool-enabled support agent
- escalation to human handoff path
- WhatsApp webhook interoperability through Evolution API

## 2) Runtime Architecture

### Main Components

- API layer (FastAPI)
  - `src/api/v1/routes/chat.py`
  - `src/api/v1/routes/health.py`
  - `src/api/v1/routes/escalation.py`
  - `src/api/v1/routes/webhook.py`

- Agent orchestration (LangGraph)
  - graph: `src/agents/graph.py`
  - shared state: `src/agents/state.py`

- Agent nodes
  - router: `src/agents/nodes/router_node.py`
  - knowledge: `src/agents/nodes/knowledge_node.py`
  - support: `src/agents/nodes/support_node.py`
  - sentiment: `src/agents/nodes/sentiment_node.py`

- Guardrails
  - input: `src/agents/guardrails/input_guard.py`
  - output: `src/agents/guardrails/output_guard.py`

- RAG and retrieval
  - ingestion/chunking: `src/rag/`
  - vector store adapter: `src/infrastructure/vector_store/chroma_store.py`
  - knowledge tools: `src/agents/tools/knowledge_tools.py`

- Support tools and repositories
  - support tools: `src/agents/tools/support_tools.py`
  - user/ticket repositories: `src/infrastructure/persistence/`

## 3) Message Flow

1. Client sends `POST /v1/chat`.
2. Input guard checks injection/unsafe patterns.
3. Router classifies intent and route.
4. One specialized node runs:
   - `knowledge`
   - `support`
   - `sentiment`
5. Finalization/personality layer is applied through prompt style rules plus output guard sanitization.
6. API returns `ChatResponse`.

Challenge diagram mapping:
- Router node: `router_node.py`
- Specialized agents: `knowledge_node.py`, `support_node.py`, `sentiment_node.py`
- Agent tools: `src/agents/tools/*.py`
- Personality/output stage: agent prompt style + `output_guard.py`

## 4) Routing Hardening and Fallback Policy

### Deterministic Router Override

The router includes a deterministic path for operational status/outage language.
Requests like service-status/instability/down now force route to `support`.

Why:
- avoids ambiguous LLM-only classification for a critical support case
- prevents user-facing dead-end fallback from knowledge path

### Knowledge Overlap Safety Fallback

Knowledge node detects support-style operational/account overlap text.
If misrouted, it returns a support/handoff guidance response directly and skips LLM/tool execution for that turn.

Why:
- safer behavior under uncertain route boundaries
- avoids generic "knowledge not found" loops for operational incidents

## 5) Design Tradeoffs

- LangGraph state machine instead of ad-hoc function chaining:
  - pro: explicit route graph and maintainable flow
  - con: additional abstraction overhead

- Embedded Chroma + SQLite defaults:
  - pro: local/dev simplicity and reproducibility
  - con: requires persistent volume setup in production

- Mixed-model strategy by role:
  - pro: cost/performance tuning by agent task
  - con: multi-provider configuration complexity

## 6) Quality and Verification

- Unit + integration test suite under `tests/`
- Prompt-level evaluation via `promptfooconfig.yaml`
- Added automated checks for:
  - deterministic support routing for service status/outage prompts
  - removal of unsupported quick suggestion in UI
  - knowledge overlap fallback behavior

## 7) Known Limits and Next Steps

- Observability can be expanded (structured metrics/tracing).
- Frontend e2e automation can be added for full escalation round-trip validation.
- Retrieval quality can be extended with reranking/hybrid search.
