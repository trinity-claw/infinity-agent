# Infinity Agent - InfinitePay AI Swarm

Multi-agent AI system for InfinitePay support, built for the CloudWalk coding challenge.

## Overview

Infinity Agent processes chat requests from web and WhatsApp, routes them through specialized agents, and returns grounded responses with guardrails.

Core flow:

1. `POST /v1/chat` receives user message
2. Input guard validates unsafe requests
3. Router agent classifies intent and language
4. Request is dispatched to a specialized agent
5. Output guard masks sensitive data before response

## Agent Swarm

- Router Agent (`src/agents/nodes/router_node.py`)
  - Classifies intent (`knowledge`, `support`, `escalation`)
  - Selects next node in LangGraph
- Knowledge Agent (`src/agents/nodes/knowledge_node.py`)
  - Uses RAG over InfinitePay content
  - Uses web search for general queries
- Support Agent (`src/agents/nodes/support_node.py`)
  - Uses customer tools (lookup user, transactions, tickets, status)
- Sentiment Agent (`src/agents/nodes/sentiment_node.py`) [bonus]
  - Detects urgency and escalates to human support when needed

Orchestration: `src/agents/graph.py` (LangGraph StateGraph).

## Tech Stack

- Backend: FastAPI + Uvicorn
- Orchestration: LangGraph + SQLite Checkpointer
- LLM gateway: OpenRouter
- Vector DB: ChromaDB
- Frontend: React + Vite + WebGL shader background
- Auth: Google OAuth (frontend allowlist)
- WhatsApp bridge: Evolution API

## Frontend (React)

Active frontend lives in `frontend-react/`.

Dev:

```bash
cd frontend-react
npm install
npm run dev
```

Build:

```bash
cd frontend-react
npm run build
```

Frontend env (`frontend-react/.env`):

```env
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
VITE_ALLOWED_EMAILS=you@example.com,another@example.com
VITE_API_BASE_URL=http://localhost:8002
```

## Local Backend Setup

Prerequisites:

- Python 3.12+
- `uv`

Install:

```bash
uv venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
uv pip install -e .
```

Configure env:

```bash
cp .env.example .env
```

Required minimum:

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx
```

Ingest knowledge base:

```bash
python -m scripts.ingest
```

Run API:

```bash
uv run uvicorn src.main:app --reload --port 8002
```

## Docker

```bash
cp .env.example .env
docker-compose up --build
```

## API

`POST /v1/chat`

Request:

```json
{
  "message": "Quais sao os produtos da InfinitePay?",
  "user_id": "client789",
  "user_name": "Nome Exemplo",
  "user_email": "user@example.com"
}
```

`GET /v1/health`

Interactive docs: `http://localhost:8002/docs`

## Tests

Backend:

```bash
uv run pytest -q
```

Frontend build check:

```bash
cd frontend-react
npm run build
```

## Deploy Guides

- General VPS + Docker + Evolution: `docs/DEPLOYMENT.md`
- Recommended split deploy (Vercel + Railway + Evolution staging):
  - `docs/DEPLOY_VERCEL_RAILWAY_EVOLUTION.md`

## Security and Ops Notes

- Do not commit real `.env` files
- Keep `AUTHENTICATION_API_KEY`, `OPENROUTER_API_KEY`, and OAuth secrets only in platform env vars
- Configure `CORS_ALLOW_ORIGINS` in production to explicit domains
- Keep checkpointer SQLite persistence mounted on persistent storage in production
