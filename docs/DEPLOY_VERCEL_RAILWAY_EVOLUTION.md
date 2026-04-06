# Deployment Guide (Vercel + Railway + Evolution API)

Recommended production split:
- Frontend React on Vercel
- Backend FastAPI on Railway
- Evolution API in staging/ops environment

## 1) Target Topology

- `frontend-react` served by Vercel
- backend API served by Railway
- frontend calls backend via `VITE_API_BASE_URL`
- Evolution API sends inbound WhatsApp events to backend `/v1/webhook`

## 2) Backend on Railway

### 2.1 Create Service

- New Railway project
- Connect repository
- Build from root `Dockerfile`

### 2.2 Backend Environment Variables

Set at minimum:

```env
APP_ENV=production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

OPENROUTER_API_KEY=sk-or-v1-...
ROUTER_MODEL=openai/gpt-4o-mini
KNOWLEDGE_MODEL=openai/gpt-4o-mini
SUPPORT_MODEL=anthropic/claude-sonnet-4.5
SENTIMENT_MODEL=openai/gpt-4o-mini
GUARDRAIL_MODEL=openai/gpt-4o-mini

CHROMA_PERSIST_DIR=/app/data/chroma_db
SQLITE_DB_PATH=/app/data/sqlite_db/langgraph.sqlite

CORS_ALLOW_ORIGINS=https://YOUR_APP.vercel.app,https://YOUR_DOMAIN

WHATSAPP_ENABLED=false
WHATSAPP_API_URL=
WHATSAPP_API_TOKEN=
WHATSAPP_INSTANCE=main
WHATSAPP_OPERATOR_NUMBER=
```

Attach persistent volume to `/app/data`.

### 2.3 Validate Backend

- `GET /v1/health` returns `healthy`
- `POST /v1/chat` returns valid JSON payload

## 3) Frontend on Vercel

### 3.1 Project Setup

- Import repository
- Root Directory: `frontend-react`
- Build command: `npm run build`
- Output directory: `dist`

### 3.2 Frontend Environment Variables

```env
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
VITE_ALLOWED_EMAILS=you@example.com,another@example.com
VITE_ALLOWED_EMAIL_CONTAINS=le,leo,frisso
VITE_API_BASE_URL=https://YOUR_BACKEND.railway.app
```

Access rules:
- Exact allowlist via `VITE_ALLOWED_EMAILS`.
- Pattern allowlist via `VITE_ALLOWED_EMAIL_CONTAINS` (matches email local-part or Google display name).
- If both are empty, Google login is open.

### 3.3 Validate Frontend

- Google login renders and authenticates
- Chat round trip works against Railway backend

## 4) Google OAuth Origin Configuration

In Google Cloud Console -> OAuth 2.0 Client (Web), configure Authorized JavaScript Origins:

- `http://localhost:5173`
- `http://localhost:8000`
- `https://YOUR_APP.vercel.app`
- `https://YOUR_DOMAIN` (if custom domain)

Missing origins produce `origin_mismatch`.

## 5) Evolution API (Staging / Ops)

Set backend WhatsApp variables:

```env
WHATSAPP_ENABLED=true
WHATSAPP_API_URL=https://YOUR_EVOLUTION_HOST
WHATSAPP_API_TOKEN=YOUR_EVOLUTION_API_KEY
WHATSAPP_INSTANCE=infinity_bot
WHATSAPP_OPERATOR_NUMBER=5511999999999
```

Create instance:

```bash
curl -sS -X POST "https://YOUR_EVOLUTION_HOST/instance/create" \
  -H "apikey: YOUR_EVOLUTION_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"instanceName":"infinity_bot","qrcode":true,"integration":"WHATSAPP-BAILEYS"}'
```

Set webhook:

```bash
curl -sS -X POST "https://YOUR_EVOLUTION_HOST/webhook/set/infinity_bot" \
  -H "apikey: YOUR_EVOLUTION_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook": {
      "enabled": true,
      "url": "https://YOUR_BACKEND.railway.app/v1/webhook",
      "events": ["MESSAGES_UPSERT"],
      "webhook_by_events": false,
      "webhook_base64": false
    }
  }'
```

## 6) Release Checklist

- `uv run pytest -q` passes
- `npx promptfoo@latest eval` passes
- `cd frontend-react && npm run build` passes
- No real secrets committed
- CORS and OAuth origins match real domains
