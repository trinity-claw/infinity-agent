# Deployment Guide

## Por que não o Vercel

O Vercel foi projetado para aplicações serverless (JavaScript/TypeScript com edge functions). O Infinity Agent não é compatível por três razões:

1. **Timeout de 10s** — chamadas de LLM + RAG levam 3-15s facilmente
2. **Sem processos persistentes** — o ChromaDB precisa de um processo rodando com acesso a disco
3. **Sem volumes** — não há onde guardar `./data/chroma_db` entre requests

---

## Opção Recomendada: Railway

Railway é a escolha mais simples. Deploy via Docker, volume persistente para ChromaDB, $5/mês no plano Hobby.

### Passo a passo

**1. Criar projeto no Railway**
```bash
# Instalar CLI
npm install -g @railway/cli
railway login
railway init   # cria novo projeto
```

**2. Adicionar variáveis de ambiente**

No dashboard do Railway → Settings → Variables:
```
OPENROUTER_API_KEY=sk-or-...
APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=INFO
CHROMA_PERSIST_DIR=/data/chroma_db
```

**3. Configurar volume persistente**

No dashboard: Add Volume → Mount path: `/data`

Isso garante que o ChromaDB sobrevive a redeploys.

**4. Deploy**
```bash
railway up
```

O Railway detecta automaticamente o `Dockerfile`.

**5. Popular o banco (uma vez)**
```bash
# Abrir shell no container remoto
railway run python -m scripts.ingest
```

### URL do deploy
Após o deploy, o Railway gera uma URL pública: `https://infinity-agent-production.up.railway.app`

---

## Alternativa: Render

Render tem free tier (com sleep após inatividade) e é igualmente simples.

1. Conectar repositório GitHub em [render.com](https://render.com)
2. Selecionar "Web Service" → Docker
3. Adicionar variáveis de ambiente
4. Adicionar Persistent Disk: Mount path `/data`, size 1GB
5. Deploy

---

## Alternativa: Fly.io

```bash
fly auth login
fly launch   # detecta Dockerfile automaticamente
fly volumes create chroma_data --size 1
fly deploy
```

---

## ChromaDB no deploy

O ChromaDB usa armazenamento local em `./data/chroma_db`. No Docker, isso precisa de um volume montado.

No `docker-compose.yml` (já configurado):
```yaml
volumes:
  - chroma_data:/app/data/chroma_db
```

No Railway/Render/Fly.io, o volume persistente é montado em `/data` e a variável `CHROMA_PERSIST_DIR=/data/chroma_db` aponta para lá.

**Verificar o banco após deploy:**
```
GET https://seu-app.up.railway.app/v1/admin/knowledge
```

Retorna todos os documentos ingeridos, fontes e contagem de chunks.

---

## Inspecionar o banco localmente

```bash
# Ver estatísticas
curl http://localhost:8000/v1/admin/knowledge

# Paginar documentos
curl "http://localhost:8000/v1/admin/knowledge?limit=10&offset=0"
```

Ou diretamente via Python:
```python
import chromadb
client = chromadb.PersistentClient(path="./data/chroma_db")
collection = client.get_collection("infinitepay_knowledge")
print(collection.count())  # total de chunks
# Ver primeiros 5 documentos
results = collection.get(limit=5, include=["documents", "metadatas"])
for doc, meta in zip(results["documents"], results["metadatas"]):
    print(meta.get("source_url"), ":", doc[:100])
```

---

## Persistência de conversas

Atualmente o histórico de chat é apenas no browser (sem salvar no servidor). As sessões de escalamento (WhatsApp) são in-memory e perdidas ao reiniciar.

Para salvar conversas: adicionar SQLite (simples, sem infra extra):
```python
# Instalação:
# uv add aiosqlite

# Tabela simples:
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    messages JSON,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

Isso pode ser adicionado como uma fase posterior do projeto.

---

## Google Auth (implementação simples)

Para personalizar o chat com o nome do usuário via Google:

**Abordagem cliente (sem backend):**

```html
<!-- Adicionar no <head> -->
<script src="https://accounts.google.com/gsi/client" async></script>

<!-- Botão de login -->
<div id="g_id_onload"
  data-client_id="SEU_GOOGLE_CLIENT_ID"
  data-callback="handleGoogleLogin"
  data-auto_prompt="false">
</div>
<div class="g_id_signin" data-type="standard"></div>

<script>
function handleGoogleLogin(response) {
  // Decodificar JWT do Google
  const payload = JSON.parse(atob(response.credential.split('.')[1]));
  const name = payload.given_name || payload.name;
  const email = payload.email;
  
  // Usar nome no chat
  document.getElementById('userIdInput').value = email;
  document.querySelector('.welcome-screen h2').textContent = `Olá, ${name}!`;
}
</script>
```

**Setup:**
1. Criar projeto no [Google Cloud Console](https://console.cloud.google.com)
2. Ativar Google Identity API
3. Criar OAuth 2.0 Client ID (tipo: Web application)
4. Adicionar `http://localhost:8000` como Authorized JavaScript origin
5. Substituir `SEU_GOOGLE_CLIENT_ID` no HTML
