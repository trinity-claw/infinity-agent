# Infinity Agent - Architecture Review and Excalidraw Guide (Current Implementation)

This is the canonical architecture review for the repository as implemented today.
Use this document as the presenter guide for a 10-15 minute demo video.

## 1) Current Project State

The project is fully implemented and evaluator-ready, with:
- 4-agent swarm (Router, Knowledge, Support, Sentiment)
- FastAPI backend with standard and streaming chat endpoints
- RAG pipeline (scraping + chunking + Chroma retrieval)
- External web search via Brave Search API
- Human handoff workflow with WhatsApp bridge
- Docker-first local and server run path
- Unit/integration tests and prompt-level evaluation

## 2) Architecture Summary

Main runtime stack:
- Orchestration: LangGraph StateGraph
- API: FastAPI (`/v1/*`)
- LLM access: OpenRouter (role-specific models)
- Vector store: ChromaDB (persistent volume)
- Search: Brave Search
- State/checkpoint: SQLite (persistent volume)
- Optional handoff channel: Evolution API (WhatsApp)

### Active model mapping by role

From `src/settings.py`:
- Router: `openai/gpt-4o-mini`
- Knowledge: `google/gemini-2.5-flash`
- Support: `anthropic/claude-sonnet-4.5`
- Sentiment: `openai/gpt-4o-mini`
- Guardrail: `openai/gpt-4o-mini`

## 3) Real Code Map (by Layer)

### API / Presentation
- `src/main.py`
- `src/api/v1/routes/chat.py`
- `src/api/v1/routes/health.py`
- `src/api/v1/routes/escalation.py`
- `src/api/v1/routes/webhook.py`
- `src/api/v1/schemas.py`

### Agent Orchestration
- `src/agents/graph.py`
- `src/agents/state.py`
- `src/agents/swarm_config.py`

### Agent Nodes
- `src/agents/nodes/router_node.py`
- `src/agents/nodes/knowledge_node.py`
- `src/agents/nodes/support_node.py`
- `src/agents/nodes/sentiment_node.py`

### Guardrails
- `src/agents/guardrails/input_guard.py`
- `src/agents/guardrails/output_guard.py`
- `src/agents/guardrails/blocklist.py`

### Agent Tools
- `src/agents/tools/knowledge_tools.py`
- `src/agents/tools/support_tools.py`
- `src/agents/tools/sentiment_tools.py`

### Domain and Infrastructure
- Ports/interfaces: `src/domain/ports/`
- Models/enums: `src/domain/models/`
- Repositories: `src/infrastructure/persistence/`
- Search adapter: `src/infrastructure/search/brave_searcher.py`
- Vector adapter: `src/infrastructure/vector_store/chroma_store.py`
- WhatsApp bridge/session store: `src/infrastructure/whatsapp/`

### RAG Ingestion
- `src/rag/scraper.py`
- `src/rag/chunker.py`
- `src/rag/ingest_pipeline.py`
- `scripts/ingest.py`

## 4) Runtime Flow (Actual)

### Standard chat endpoint
1. Client sends `POST /v1/chat` with `message`, `user_id` (optional profile fields too).
2. API builds initial LangGraph state.
3. `input_guard` validates request safety.
4. `router` classifies route (`knowledge`, `support`, `escalation`).
5. Specialized agent runs.
6. `output_guard` sanitizes output.
7. API returns `ChatResponse`.

### Streaming endpoint
- `POST /v1/chat/stream` streams:
  - status events (`event: status`)
  - token chunks (`event: token`)
  - final payload (`event: final`)
  - completion marker (`event: done`)

## 5) Agent Graph Diagram (for Excalidraw)

```text
                      +------------------+
                      |      START       |
                      +---------+--------+
                                |
                                v
                     +----------+-----------+
                     |     INPUT_GUARD      |
                     +----------+-----------+
                                |
                   blocked=true | blocked=false
                                |
                +---------------+----------------+
                |                                |
                v                                v
             +--+---+                     +------+------+
             | END  |                     |    ROUTER   |
             +------+                     +------+------+
                                               |
                            +------------------+------------------+
                            |                  |                  |
                            v                  v                  v
                   +--------+------+   +-------+------+   +-------+------+
                   |  KNOWLEDGE    |   |   SUPPORT     |   |  SENTIMENT   |
                   |    NODE       |   |    NODE       |   |    NODE      |
                   +--------+------+   +-------+------+   +-------+------+
                            \                |                   /
                             \               |                  /
                              \              |                 /
                               v             v                v
                            +------------------------------------+
                            |            OUTPUT_GUARD            |
                            +----------------+-------------------+
                                             |
                                             v
                                          +--+--+
                                          | END |
                                          +-----+
```

## 6) System Context Diagram (for Excalidraw)

```text
+-------------------+        HTTPS         +---------------------------+
|   Web Frontend    +--------------------->+      FastAPI Backend      |
| (React, Sidebar,  |<---------------------+  /v1/chat, /v1/chat/stream|
|  Auth, SSE UI)    |      JSON + SSE      |  /v1/health, webhooks     |
+---------+---------+                      +-------------+-------------+
          |                                                 |
          |                                                 |
          |                                   +-------------v-------------+
          |                                   |     LangGraph Swarm       |
          |                                   | input_guard -> router ->  |
          |                                   | specialized agents -> out |
          |                                   +------+------+------+-------+
          |                                          |      |      |
          |                                          |      |      |
          |                                  +-------v+   +-v------+-------+
          |                                  | Chroma  |   | Brave Search   |
          |                                  |   DB    |   | API Adapter    |
          |                                  +---------+   +----------------+
          |                                          |
          |                                  +-------v--------+
          |                                  | SQLite Checkpt |
          |                                  +----------------+
          |
          | optional human handoff
          |
          v
+---------------------+      webhook/events      +-----------------------+
|  Evolution API      +------------------------->+ /v1/webhook +         |
|  (WhatsApp bridge)  |<-------------------------+ /v1/webhook/whatsapp  |
+---------------------+      outbound send       | /v1/messages/*        |
                                                 +-----------------------+
```

## 7) Request Lifecycle (Presentation Script)

```text
Client -> POST /v1/chat
  -> build AgentState
  -> input_guard
  -> router
       if support/outage terms => deterministic support override
  -> selected agent node
       knowledge:
         - InfinitePay query => RAG
         - general query => deterministic Brave search path
         - support-overlap => safe support handoff guidance
       support:
         - account and ticket tools
       sentiment:
         - urgency/frustration analysis + escalation trigger
  -> output_guard
  -> return ChatResponse {response, agent_used, intent, language, metadata}
```

## 8) WhatsApp Escalation and Human Handoff

Current policy:
- Human continuity is asynchronous by design.
- Escalation response informs user that continuation happens via WhatsApp/email.
- Operator receives enriched handoff message with:
  - session ID
  - escalation reason
  - customer name
  - customer email
  - customer phone

Key files:
- `src/api/v1/routes/chat.py`
- `src/api/v1/routes/webhook.py`
- `src/api/v1/routes/escalation.py`
- `src/infrastructure/whatsapp/session_store.py`

## 9) Hardening Implemented (Important for Evaluator)

### Router deterministic support override
- Service status/outage/instability prompts are forced to `support`.
- Prevents low-quality route ambiguity for operational incidents.

File:
- `src/agents/nodes/router_node.py`

### Knowledge overlap fallback
- If support-style operational issues reach knowledge node, it avoids dead-end fallback and points to support/handoff flow.

File:
- `src/agents/nodes/knowledge_node.py`

### Deterministic general web path
- Non-InfinitePay questions trigger direct Brave web path in knowledge node.
- Includes echo-response detection fallback.

File:
- `src/agents/nodes/knowledge_node.py`

## 10) Docker and Runtime Topology

From `docker-compose.yml`:
- `infinity-agent` always available.
- `evolution-api` optional under `--profile whatsapp`.
- Persistent volumes:
  - `chroma_data`
  - `sqlite_data`
  - `evolution_instances` (optional profile)

Standard evaluator run:
```bash
cp .env.example .env
docker compose up -d --build
```

Optional WhatsApp profile:
```bash
docker compose --profile whatsapp up -d evolution-api
```

## 11) OpenAPI and Observability Entry Points

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- Health: `GET /v1/health`
- Knowledge admin preview: `GET /v1/admin/knowledge`

