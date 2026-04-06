# Post-Deploy Validation Checklist

Last updated: 2026-04-06

Use this checklist after `git pull` + `docker compose up -d --build` on VPS.

## 1) Environment Sanity

Run inside VPS:

```bash
cd /opt/infinity-agent
docker compose exec infinity-agent env | egrep "OPENROUTER|BRAVE_SEARCH|WHATSAPP_"
```

Expected:
- `OPENROUTER_API_KEY` set
- `BRAVE_SEARCH_API_KEY` set
- `WHATSAPP_ENABLED=true` (if handoff demo enabled)
- `WHATSAPP_INSTANCE` matches Evolution instance connected in WhatsApp

## 2) API Health + OpenAPI

```bash
curl -sS http://127.0.0.1:8000/v1/health
```

Expected:
- JSON with healthy status.

Browser:
- `https://<your-domain>/docs` loads Swagger UI.

## 3) Streaming (SSE) Verification

Frontend test:
- Send: `Quais as principais notícias de São Paulo hoje?`

Expected in UI:
- Typing status progression (ex: router/knowledge/support phase statuses).
- Response appears progressively (chunked), not only at the end.

## 4) Brave Search Verification

API direct test:

```bash
curl -sS -X POST http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Quais as principais notícias de São Paulo hoje?","user_id":"client789"}' | python3 -m json.tool
```

Expected:
- `agent_used` should be `knowledge` (or compatible knowledge path).
- `response` must not echo user prompt verbatim.
- Answer should mention recent/current context instead of product-only fallback.

## 5) Human Handoff (Asynchronous Channel Policy)

### 5.1 Trigger handoff from UI

Send:
- `Quero falar com um atendente humano agora.`

Expected:
- UI response confirms escalation.
- Text explicitly states continuity is asynchronous via WhatsApp/email.

### 5.2 WhatsApp operator notification content

Expected message to operator includes:
- Session ID
- Reason
- Customer name
- Customer email
- Customer phone

This enriched notice should be sent once per session (no spam duplicates).

### 5.3 Continuation policy

Expected behavior for demo:
- Treat human continuity as asynchronous (WhatsApp/email).
- Do not depend on round-trip WhatsApp->UI for pass/fail of evaluator demo.

## 6) Regression Smoke

Run:

```bash
docker compose exec infinity-agent python scripts/evaluator_smoke.py --base-url http://localhost:8000 --user-id client789
```

Expected:
- script exits successfully.

## 7) Automated Tests (optional on VPS, mandatory pre-release)

```bash
docker compose exec infinity-agent uv run pytest -q
```

Expected:
- all tests pass.

## 8) Frontend UX Spot-check

Validate in UI:
- Portuguese accents rendered correctly:
  - `Router classificando intenção...`
  - `Sugestões guiadas`
  - `Escalação humana`
- Sidebar dropdown icon renders correctly (`▾`), no white broken area.

## 9) Go/No-Go Rule

GO if all below are true:
- Health and docs available.
- Streaming works and does not freeze.
- Brave query returns contextual answer (not echo).
- Handoff message arrives on operator WhatsApp with full contact details.
- UI text/encoding is clean and consistent.
