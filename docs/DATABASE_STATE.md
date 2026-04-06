# Database State - Infinity Agent

Documento tecnico com o estado atual de dados no repositorio, incluindo persistencia real e stores em memoria.

## 1) Resumo Executivo

Hoje o projeto usa **modelo hibrido de dados**:

| Camada | Tecnologia | Persistente | Uso principal |
|---|---|---|---|
| Memoria conversacional do swarm | SQLite (LangGraph checkpointer) | Sim | Historico de estado por `thread_id` |
| Base de conhecimento RAG | ChromaDB (local persistent) | Sim | Vetores + metadados dos chunks |
| Dados de suporte (clientes/transacoes) | Repositorio in-memory | Nao | Mock deterministico para demo |
| Tickets de suporte | Repositorio in-memory | Nao | Criacao e consulta de tickets da sessao |
| Sessoes de handoff humano | Session store in-memory | Nao | Ponte chat <-> WhatsApp |

## 2) Onde os dados ficam

### Variaveis de ambiente

- `CHROMA_PERSIST_DIR` (default local: `./data/chroma_db`)
- `SQLITE_DB_PATH` (default local: `./data/langgraph.sqlite`)

### Docker Compose

No `docker-compose.yml`, os paths sao sobrescritos para dentro do container:

- `CHROMA_PERSIST_DIR=/app/data/chroma_db`
- `SQLITE_DB_PATH=/app/data/sqlite_db/langgraph.sqlite`

Volumes nomeados:

- `chroma_data` -> `/app/data/chroma_db`
- `sqlite_data` -> `/app/data/sqlite_db`

## 3) SQLite (LangGraph Checkpointer)

### Finalidade

Persistir checkpoints e writes do estado do grafo para manter memoria de conversa entre requests.

### Arquivo local atual

- `data/langgraph.sqlite`
- arquivos WAL associados:
  - `data/langgraph.sqlite-wal`
  - `data/langgraph.sqlite-shm`

### Tabelas observadas (snapshot local em 2026-04-06)

- `checkpoints`: **149 rows**
- `writes`: **625 rows**

### Schema observado

`checkpoints`:

- `thread_id` (TEXT, PK parte 1)
- `checkpoint_ns` (TEXT, PK parte 2)
- `checkpoint_id` (TEXT, PK parte 3)
- `parent_checkpoint_id` (TEXT)
- `type` (TEXT)
- `checkpoint` (BLOB)
- `metadata` (BLOB)

`writes`:

- `thread_id` (TEXT, PK parte 1)
- `checkpoint_ns` (TEXT, PK parte 2)
- `checkpoint_id` (TEXT, PK parte 3)
- `task_id` (TEXT, PK parte 4)
- `idx` (INTEGER, PK parte 5)
- `channel` (TEXT)
- `type` (TEXT)
- `value` (BLOB)

### Observacao tecnica importante

No snapshot atual, todos os registros estao com `checkpoint_ns=''` (vazio), mesmo o app logando `checkpoint_ns=chat`.
Isso nao quebrou o fluxo, mas vale monitorar se o namespace logico esta sendo efetivamente aplicado no saver.

## 4) ChromaDB (RAG)

### Finalidade

Armazenar chunks vetorizados e metadados para recuperacao semantica no Knowledge Agent.

### Diretoria local atual

- `data/chroma_db/chroma.sqlite3` (metastore interno do Chroma)
- `data/chroma_db/<uuid>/` com arquivos de indice HNSW:
  - `header.bin`
  - `data_level0.bin`
  - `length.bin`
  - `link_lists.bin`

### Colecao

- Nome: `infinitepay_knowledge`
- Espaco de similaridade: `cosine` (`metadata={"hnsw:space":"cosine"}`)

### Snapshot local (2026-04-06)

- Total de documentos/chunks: **533**
- Total de fontes: **28**

Exemplos de fonte com maior volume de chunks:

- `https://www.infinitepay.io` -> 44
- `https://www.infinitepay.io/conta-pj` -> 22
- `https://www.infinitepay.io/boleto` -> 21
- `https://www.infinitepay.io/cartao` -> 19
- Conteudos `ajuda.infinitepay.io` (JIM) tambem presentes

### Estrutura logica por documento (preview admin)

Cada item exposto em `GET /v1/admin/knowledge` inclui:

- `id`
- `snippet`
- `char_count`
- `source_url`
- `title`
- `chunk_index`

### Tabelas internas do metastore Chroma (snapshot)

Exemplos:

- `collections` (1)
- `embeddings` (533)
- `embedding_metadata` (2665)
- `embedding_fulltext_search` (533)
- `segments` (2)
- `migrations` (18)

Importante: estas tabelas sao internas do Chroma e nao devem ser manipuladas manualmente.

## 5) Dados de Suporte (In-Memory User Repository)

### Implementacao

- Arquivo: `src/infrastructure/persistence/in_memory_user_repo.py`
- Nao persiste em disco.
- Reiniciar processo reseta para o seed.

### Snapshot do seed (2026-04-06)

- Usuarios: **8**
- Ativos: **7**
- Inativos: **1**
- PF: **5**
- PJ: **3**
- Transacoes totais: **20**
- Status transacoes:
  - `completed`: 18
  - `pending`: 1
  - `failed`: 1

Campos de `User`:

- `user_id`, `name`, `email`, `phone`, `document`
- `account_type`, `plan`, `balance`, `is_active`
- `created_at`, `metadata`

Campos de `Transaction`:

- `transaction_id`, `user_id`, `amount`, `transaction_type`
- `description`, `status`, `created_at`

## 6) Tickets (In-Memory Ticket Repository)

### Implementacao

- Arquivo: `src/infrastructure/persistence/in_memory_ticket_repo.py`
- Store em memoria (`self._tickets: dict[...]`)
- Ticket ID gerado em runtime: `TKT-XXXXXXXX`
- Reiniciar processo apaga tickets criados durante a sessao.

Campos de ticket:

- `ticket_id`, `user_id`, `issue`
- `priority`, `status`
- `assigned_to`, `resolution`
- `created_at`, `updated_at`, `metadata`

## 7) Sessoes de Handoff (In-Memory Session Store)

### Implementacao

- Arquivo: `src/infrastructure/whatsapp/session_store.py`
- Nao persiste em disco.
- Reiniciar processo encerra contexto de sessoes ativas.

Campos de sessao:

- `session_id` (`ESC-XXXXXXXX`)
- `session_token` (gerado com `secrets.token_urlsafe(24)`)
- `user_id`, `operator_number`
- `messages[]`, `created_at`, `active`, `detail_notice_sent`

Controle de seguranca:

- Validacao de token por `secrets.compare_digest`
- Pareamento por usuario e operador
- Matching tolerante de numero para webhook WhatsApp

## 8) Fluxo de leitura/escrita por componente

### `/v1/chat` e `/v1/chat/stream`

- Le:
  - Chroma (queries knowledge)
  - repositorio in-memory de usuarios/transacoes
  - session store (handoff)
- Escreve:
  - SQLite checkpointer (estado do grafo)
  - session store (mensagens de sessao, quando escalado)
  - ticket repo in-memory (quando tool cria ticket)

### `/v1/admin/knowledge`

- Le:
  - Chroma (preview paginado + agregacao de fontes)

### `/v1/messages/{session_id}` e webhooks de escalacao

- Le/Escreve:
  - session store in-memory

## 9) Limites atuais e implicacoes

- Nao existe banco relacional persistente para dominio de suporte (clientes/tickets).
- Em producao real, dados de suporte deveriam migrar para adapter persistente (ex: Postgres).
- Chroma e SQLite estao persistidos, mas stores de suporte/handoff ainda sao efemeros.
- `EMBEDDING_MODEL` esta definido em config, mas no estado atual o Chroma usa embedding default local (nao provedor externo).

## 10) Comandos de auditoria rapida

Contagem de memoria conversacional:

```bash
uv run python - <<'PY'
import sqlite3
conn=sqlite3.connect('data/langgraph.sqlite')
cur=conn.cursor()
for t in ('checkpoints','writes'):
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    print(t, cur.fetchone()[0])
conn.close()
PY
```

Contagem da base RAG:

```bash
uv run python - <<'PY'
import asyncio
from src.infrastructure.vector_store.chroma_store import ChromaKnowledgeStore
async def main():
    store = ChromaKnowledgeStore()
    print(await store.get_collection_stats())
asyncio.run(main())
PY
```

Preview de fontes ingeridas:

```bash
curl -s "http://127.0.0.1:8000/v1/admin/knowledge?limit=5&offset=0" | jq '.sources[:10]'
```

