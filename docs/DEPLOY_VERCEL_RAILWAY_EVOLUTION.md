# Deploy Completo (Vercel + Railway + Evolution API)

Este guia cobre o fluxo recomendado para producao:

- Frontend React no **Vercel**
- Backend FastAPI no **Railway** (com persistencia em disco)
- Evolution API em **staging** (para handoff humano via WhatsApp)

## 1) Arquitetura final

- `frontend-react` publica no Vercel
- API roda separada no Railway
- Frontend chama backend via `VITE_API_BASE_URL`
- Backend persiste:
  - Chroma em `/app/data/chroma_db`
  - SQLite em `/app/data/langgraph.sqlite`

## 2) Pre-requisitos

- Conta Vercel
- Conta Railway
- Conta Google Cloud (OAuth Web Client)
- Chave OpenRouter ativa
- (Opcional staging) Evolution API disponivel

## 3) Backend no Railway

### 3.1 Criar servico

1. Criar novo projeto no Railway
2. Conectar este repositorio
3. Build usando `Dockerfile` da raiz

### 3.2 Variaveis de ambiente (Backend)

Defina no Railway:

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
SQLITE_DB_PATH=/app/data/langgraph.sqlite

# Coloque aqui os dominios reais do frontend (CSV)
CORS_ALLOW_ORIGINS=https://seu-app.vercel.app,https://seu-dominio.com

# Produção inicial recomendada: desligado
WHATSAPP_ENABLED=false
WHATSAPP_API_URL=
WHATSAPP_API_TOKEN=
WHATSAPP_INSTANCE=main
WHATSAPP_OPERATOR_NUMBER=
```

### 3.3 Persistencia

No Railway, anexe volume/disco persistente para `/app/data`.

Sem isso, Chroma/SQLite perdem estado a cada restart.

### 3.4 Validacao backend

- `GET /v1/health` => `200`
- `POST /v1/chat` => `200`

## 4) Frontend no Vercel

### 4.1 Configurar projeto

1. Importar repositorio no Vercel
2. Root directory: `frontend-react`
3. Build: `npm run build`
4. Output: `dist`

### 4.2 Variaveis de ambiente (Frontend)

```env
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
VITE_ALLOWED_EMAILS=you@example.com,another@example.com
VITE_API_BASE_URL=https://seu-backend.railway.app
```

### 4.3 Validacao frontend

- Login Google abre sem erro de origem
- Chat envia pergunta e recebe resposta real do backend

## 5) Google OAuth (evitar origin_mismatch)

No Google Cloud Console > APIs & Services > Credentials > OAuth 2.0 Client ID (Web):

Em **Authorized JavaScript origins**, adicione:

- `http://localhost:5173` (dev Vite)
- `http://localhost:8002` (quando servir frontend/backend local)
- `https://seu-app.vercel.app`
- `https://seu-dominio.com` (se houver)

Se faltar qualquer origem ativa, o Google retornara `Erro 400: origin_mismatch`.

## 6) Evolution API (staging)

Recomendacao: manter Evolution ligado em **staging** primeiro.

### 6.1 Subir Evolution

Pode ser em Railway, VPS ou container separado.
Garanta:

- URL publica acessivel
- Header `apikey` configurado

### 6.2 Backend (staging) - variaveis WhatsApp

```env
WHATSAPP_ENABLED=true
WHATSAPP_API_URL=https://evolution-staging.seu-dominio.com
WHATSAPP_API_TOKEN=sua_api_key_forte
WHATSAPP_INSTANCE=infinity_bot
WHATSAPP_OPERATOR_NUMBER=5511999999999
```

### 6.3 Criar instancia na Evolution

```bash
curl --request POST \
  --url https://evolution-staging.seu-dominio.com/instance/create \
  --header 'apikey: sua_api_key_forte' \
  --header 'content-type: application/json' \
  --data '{
    "instanceName": "infinity_bot",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }'
```

### 6.4 Registrar webhook para o backend

Use a URL publica do backend staging:

```bash
curl --request POST \
  --url https://evolution-staging.seu-dominio.com/webhook/set/infinity_bot \
  --header 'apikey: sua_api_key_forte' \
  --header 'content-type: application/json' \
  --data '{
    "webhook": {
      "enabled": true,
      "url": "https://seu-backend-staging.railway.app/v1/webhook",
      "events": ["MESSAGES_UPSERT"]
    }
  }'
```

## 7) Checklist final de release

- `uv run pytest -q` passando
- `cd frontend-react && npm run build` passando
- Sem `node_modules` e `private_docs` versionados
- Sem credenciais reais em arquivos tracked
- `CORS_ALLOW_ORIGINS` com dominios reais
- `VITE_API_BASE_URL` apontando para backend certo

## 8) Troubleshooting rapido

- `origin_mismatch` no Google:
  - faltou origem em Authorized JavaScript origins
- `Checkpointer requires configurable keys`:
  - backend antigo/stale em execucao
  - reinicie o processo e valide logs de `thread_id/checkpoint_ns`
- `Falha de conexao` no frontend:
  - `VITE_API_BASE_URL` errado ou backend indisponivel
