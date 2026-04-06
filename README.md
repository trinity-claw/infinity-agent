# Infinity Agent - InfinitePay AI Swarm

Production-oriented multi-agent system built for the CloudWalk coding challenge.

It serves web chat and WhatsApp handoff use cases with:
- LangGraph-based agent orchestration
- RAG over InfinitePay content
- Guardrails (input/output)
- Human escalation workflow
- Docker-first deployment

## Challenge Requirement Mapping

| Challenge Requirement | Status | Where Implemented |
|---|---|---|
| At least 3 distinct agents | Met (4 agents) | `src/agents/nodes/` |
| Router as primary entrypoint | Met | `src/agents/nodes/router_node.py`, `src/agents/graph.py` |
| Knowledge agent with RAG + web search | Met | `src/agents/nodes/knowledge_node.py`, `src/agents/tools/knowledge_tools.py`, `src/rag/` |
| Support agent with at least 2 tools | Met (6 tools) | `src/agents/tools/support_tools.py` |
| HTTP endpoint with JSON payload | Met | `src/api/v1/routes/chat.py`, `src/api/v1/schemas.py` |
| Dockerization | Met | `Dockerfile`, `docker-compose.yml` |
| Testing strategy and automated tests | Met | `tests/`, `promptfooconfig.yaml` |
| Bonus: fourth agent | Met | `src/agents/nodes/sentiment_node.py` |
| Bonus: guardrails | Met | `src/agents/guardrails/` |
| Bonus: human redirect | Met | `src/api/v1/routes/escalation.py`, `src/api/v1/routes/webhook.py` |

## Architecture at a Glance

Message flow:
1. `POST /v1/chat` receives message and user context.
2. Input guard blocks prompt injection / unsafe content.
3. Router classifies intent: `knowledge`, `support`, `escalation`.
4. Specialized agent handles request.
5. Personality/finalization layer (implemented by agent prompt style + output guard) normalizes and sanitizes final text.
6. Response is returned to UI.

Graph orchestration: `src/agents/graph.py`

### Agents

- Router Agent
  - Intent and language classification.
  - Deterministic safety override: service-status/outage queries route to `support`.
- Knowledge Agent
  - Internal RAG retrieval (`search_knowledge_base`).
  - External search for general questions (`search_web`).
  - Safe overlap fallback for misrouted support-style operational questions.
- Support Agent
  - Personalized support with account/tool access.
- Sentiment Agent
  - Detects frustration/urgency and triggers human handoff path.

Diagram alignment note:
- Router -> specialized agents -> final response layer is explicitly implemented.
- "Tools" nodes in the challenge diagram are represented by LangChain tools bound to each specialized agent.
- The optional custom agent requirement is covered by the Sentiment Agent.

## Public API

### `POST /v1/chat`

Request:

```json
{
  "message": "Quais sao as taxas da Maquininha Smart?",
  "user_id": "client_123",
  "user_name": "User Name",
  "user_email": "user@example.com",
  "session_id": null,
  "session_token": null
}
```

Response:

```json
{
  "response": "...",
  "agent_used": "knowledge",
  "intent": "knowledge",
  "language": "pt-BR",
  "metadata": {
    "escalated": false,
    "guardrail_blocked": false
  },
  "timestamp": "2026-04-06T00:00:00Z"
}
```

### Other routes
- `POST /v1/chat/stream` (SSE status + chunked response streaming)
- `GET /v1/health`
- `POST /v1/escalation/session/start`
- `GET /v1/escalation/session/{session_id}`
- `GET /v1/messages/{session_id}` (requires `session_token`)
- `POST /v1/messages/{session_id}` (requires `session_token`)
- `POST /v1/webhook` (Evolution API inbound)

OpenAPI docs: `/docs`

Sensitive-route auth policy:
- In `production`, sensitive routes require `X-API-Key` (or `apikey`) matching `SENSITIVE_API_KEY`.
- In non-production environments, this check is bypassed for local development.

## Local Development

### 1) Backend

Prerequisites:
- Python 3.12+
- `uv`

Setup:

```bash
uv venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
uv pip install -e .
cp .env.example .env
```

Minimum required variables:

```env
OPENROUTER_API_KEY=sk-or-v1-...
BRAVE_SEARCH_API_KEY=your-brave-api-key
```

Recommended in production:

```env
SENSITIVE_API_KEY=change-this-in-production
```

Ingest knowledge base:

```bash
python -m scripts.ingest
```

Run API:

```bash
uv run uvicorn src.main:app --reload --port 8000
```

### 2) Frontend

```bash
cd frontend-react
npm install
npm run dev
```

Frontend env (`frontend-react/.env`):

```env
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
VITE_ALLOWED_EMAILS=you@example.com,another@example.com
VITE_ALLOWED_EMAIL_CONTAINS=le,leo,frisso
VITE_API_BASE_URL=http://localhost:8000
```

Authentication policy:
- `VITE_ALLOWED_EMAILS`: exact allowlist (comma-separated).
- `VITE_ALLOWED_EMAIL_CONTAINS`: token-based allowlist (comma-separated).  
  Login is allowed when the email local part (before `@`) or Google display name contains any token.
- If both variables are empty, login is open to any Google account.

Evaluator tip:
- Sidebar defaults to `user_id=client789` so support flows work immediately with seeded mock data.
- Full mock account list: `docs/MOCK_DATA.md`.

### Evaluator Authentication Experience (End-to-End)

1. Evaluator opens the app.
2. Google login modal appears.
3. The app decodes the Google credential and applies access rules:
   - exact email match against `VITE_ALLOWED_EMAILS`, or
   - token match against `VITE_ALLOWED_EMAIL_CONTAINS`.
4. On success, evaluator profile is stored locally and chat is unlocked.
5. The app auto-assigns a deterministic `user_id` from email (if not already set).
6. Evaluator can immediately test support flows using seeded users (`client789`, etc.).

## Docker

```bash
cp .env.example .env
docker compose up -d --build
```

Default behavior:
- Starts the core service (`infinity-agent`) only.
- This guarantees evaluator-friendly startup even if WhatsApp/Evolution is not configured.

- API: `http://localhost:8000`
- Health: `http://localhost:8000/v1/health`

If this is your first run and the knowledge base is empty, ingest content once:

```bash
docker compose exec infinity-agent python -m scripts.ingest
```

To also run Evolution API from this compose file:

```bash
docker compose --profile whatsapp up -d evolution-api
```

If you already have an external Evolution API instance, keep the profile disabled and point:
- `WHATSAPP_API_URL`
- `WHATSAPP_API_TOKEN`
- `WHATSAPP_INSTANCE`

### Evaluator Quick Start (5-Minute Path)

1. Configure API keys:
```bash
cp .env.example .env
# edit .env and set OPENROUTER_API_KEY + BRAVE_SEARCH_API_KEY
```
2. Start services:
```bash
docker compose up -d --build
```
3. Run smoke validation (routes + guardrails):
```bash
python scripts/evaluator_smoke.py --base-url http://localhost:8000 --user-id client789
```
Or run inside the Docker container (no local Python setup needed):
```bash
docker compose exec infinity-agent python scripts/evaluator_smoke.py --base-url http://localhost:8000 --user-id client789
```
4. Open API docs:
```text
http://localhost:8000/docs
```
5. (Optional) Open frontend (served by FastAPI static mount):
```text
http://localhost:8000
```
6. Run final deploy checks before demo:
```text
docs/POST_DEPLOY_CHECKLIST.md
```

## RAG Pipeline

- Source ingestion defined in `src/rag/scraper.py`
- Chunking strategy in `src/rag/chunker.py`
- Embedding + persistence in `src/rag/ingest_pipeline.py`
- Retrieval path used by knowledge tools in `src/agents/tools/knowledge_tools.py`

Runtime behavior:
- Product/service questions -> vector retrieval
- General world questions -> web search

## How LLM Tools Were Used in This Case

- LangGraph orchestrates the swarm state machine (`src/agents/graph.py`).
- Router uses structured JSON classification prompt for intent/language (`router_prompt.py`).
- Knowledge agent uses tool-calling:
  - `search_knowledge_base` for RAG-grounded answers
  - `search_web` for general-purpose questions
- Support agent uses tool-calling for account lookup, transactions, ticketing, balance, and service status.
- Sentiment agent uses tools for urgency detection and human escalation.
- Prompt-level guardrails + output sanitization control unsafe input and sensitive output patterns.

## Prompt Curation Policy (Quick Suggestions)

Quick suggestions must:
- be answerable with high confidence by implemented agents/tools
- map clearly to one expected route (`knowledge`, `support`, or `escalation`)
- avoid ambiguous operational wording unless route is explicitly covered

Current curated suggestions are maintained in:
- `frontend-react/src/components/Sidebar.jsx`

## Testing Strategy

### Automated

```bash
uv run pytest -q
```

Prompt evaluation:

```bash
npx promptfoo@latest eval
```

Evaluator smoke test:

```bash
python scripts/evaluator_smoke.py --base-url http://localhost:8000 --user-id client789
# or:
docker compose exec infinity-agent python scripts/evaluator_smoke.py --base-url http://localhost:8000 --user-id client789
```

### Coverage intent
- Unit tests for guards, container lifecycle, sentiment tools, deterministic routing and overlap fallback.
- Integration tests for API behavior.
- Prompt-level regression scenarios in promptfoo.

## WhatsApp Handoff (Evolution API)

This repo supports human handoff through Evolution API webhook integration.
Main integration points:
- `src/api/v1/routes/webhook.py`
- `src/api/v1/routes/escalation.py`
- `src/infrastructure/whatsapp/`

## Documentation Index

See `docs/README.md` for the complete documentation map.
