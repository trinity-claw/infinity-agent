# Infinity Agent — InfinitePay AI Swarm

> Sistema multi-agente de IA para atendimento inteligente da InfinitePay, desenvolvido para o desafio técnico da **CloudWalk**.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Visão Geral

O **Infinity Agent** é um sistema de IA que processa mensagens de usuários da web ou WhatsApp nativo, e as roteia para agentes especializados usando [LangGraph](https://langchain-ai.github.io/langgraph/). Cada agente tem ferramentas específicas e modelos LLM otimizados para sua função.

```
                    ┌─────────────┐
                    │   FastAPI   │  POST /v1/chat
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Input Guard │  Detecta injeções e tópicos bloqueados
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Router    │  Classifica intenção (GPT-4o-mini)
                    └──────┬──────┘
                           │
          ┌────────────────┼──────────────────┐
          ▼                ▼                  ▼
   ┌─────────────┐  ┌────────────┐  ┌───────────────┐
   │  Knowledge  │  │  Support   │  │   Sentiment   │
   │   Agent     │  │  Agent     │  │   Agent       │
   │ RAG + Web   │  │ Conta/Suporte│  │ Escalamento  │
   └──────┬──────┘  └─────┬──────┘  └───────┬───────┘
          │               │                  │
          └───────────────┴──────────────────┘
                           │
                    ┌──────▼──────┐
                    │Output Guard │  PII masking
                    └─────────────┘
```

---

## Agentes

### 🧠 Router Agent
- **Modelo**: `openai/gpt-4o-mini`
- **Função**: Classifica a intenção do usuário (`knowledge`, `support`, `escalation`) e detecta o idioma
- **Saída**: Roteamento determinístico para o agente correto

### 📚 Knowledge Agent
- **Modelo**: `openai/gpt-4o-mini`
- **Função**: Responde perguntas sobre produtos InfinitePay (via RAG) e questões gerais (via busca web)
- **Ferramentas**:
  - `search_knowledge_base` — busca vetorial no ChromaDB com documentação scrapeada
  - `search_web` — busca DuckDuckGo para informações gerais

### 🎧 Support Agent
- **Modelo**: `anthropic/claude-sonnet-4.5`
- **Função**: Suporte personalizado com acesso ao perfil do cliente e criação de tickets
- **Ferramentas**:
  - `lookup_user` — perfil e dados da conta
  - `get_transaction_history` — histórico de transações
  - `create_support_ticket` — abertura de chamado
  - `check_service_status` — status operacional dos serviços
  - `reset_password_request` — solicitação de redefinição de senha
  - `get_account_balance` — saldo e limites

### 💬 Sentiment & Escalation Agent _(bônus)_
- **Modelo**: `openai/gpt-4o-mini`
- **Função**: Analisa sentimento e frustrações; escala para humano quando necessário
- **Ferramentas**:
  - `analyze_sentiment` — pontuação de sentimento (-1.0 a 1.0)
  - `detect_urgency` — classificação de urgência (low/medium/high/critical)
  - `escalate_to_human` — acionamento de atendente humano
  - `generate_escalation_summary` — resumo para o agente humano

---

## Guardrails

| Tipo | Mecanismo |
|------|-----------|
| **Input Guard** | Detecta prompt injection (regex + padrões), tópicos bloqueados |
| **Output Guard** | Mascara PII (CPF, CNPJ, email, telefone) com regex |

---

## Pipeline RAG

1. **Scraping** (`scripts/ingest.py`): 18 URLs do site da InfinitePay scrapeadas com `httpx` + `BeautifulSoup`
2. **Chunking** (`src/rag/chunker.py`): Divisão em chunks de 512 caracteres com overlap de 100
3. **Storage** (`src/infrastructure/vector_store/chroma_store.py`): ChromaDB persistente com embeddings padrão
4. **Retrieval**: Busca por similaridade coseno, retorna top-5 chunks com score de relevância

---

## Tecnologias

| Camada | Tecnologia |
|--------|------------|
| API & Webhooks | FastAPI 0.115 + Uvicorn + BackgroundTasks |
| Orquestração | LangGraph 0.4 (StateGraph) + SQLite Checkpointer |
| WhatsApp Bridge | Evolution API (Daemon Nativo p/ conversas) |
| LLMs | OpenRouter (GPT-4o-mini + Claude Sonnet 4.5) |
| Vector DB | ChromaDB (embedded, persistente) |
| Avaliação (Evall) | Promptfoo (Integração customizada com LangGraph) |
| Busca Web | DuckDuckGo Search |
| Frontend | HTML/CSS/JS (Glassmorphism minimalista) |

---

## Setup Local

### Pré-requisitos

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (gerenciador de pacotes)
- Conta no [OpenRouter](https://openrouter.ai) com créditos

### 1. Clonar e instalar dependências

```bash
git clone https://github.com/seu-usuario/infinity-agent.git
cd infinity-agent
uv venv && source .venv/bin/activate   # Linux/Mac
# ou: .venv\Scripts\activate           # Windows

uv pip install -e .
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Editar .env e adicionar sua OPENROUTER_API_KEY
```

Mínimo necessário:
```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx
```

### 3. Popular a base de conhecimento

```bash
python -m scripts.ingest
```

Isso scrapeará 18 páginas do site da InfinitePay e as armazenará no ChromaDB.

### 4. Iniciar o servidor

```bash
uvicorn src.main:app --reload --port 8000
```

Abrir `http://localhost:8000` para acessar o chat.

---

## Setup com Docker

```bash
# Copiar e configurar .env
cp .env.example .env
# Adicionar OPENROUTER_API_KEY no .env

# Build e start
docker-compose up --build

# Popular base de conhecimento (na primeira vez)
docker-compose exec infinity-agent python -m scripts.ingest
```

O chat estará disponível em `http://localhost:8000`.

---

## API

### `POST /v1/chat`

```json
// Request
{
  "message": "Quais são as taxas da Maquininha Smart?",
  "user_id": "client789"
}

// Response
{
  "response": "A **Maquininha Smart** da InfinitePay possui as seguintes taxas...",
  "agent_used": "knowledge",
  "intent": "knowledge",
  "language": "pt-BR",
  "metadata": {
    "escalated": false,
    "guardrail_blocked": false,
    "router_reasoning": "Pergunta sobre produto InfinitePay"
  },
  "timestamp": "2024-01-15T14:30:00"
}
```

### `GET /v1/health`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "llm": "configured",
    "knowledge_base": "operational (847 documents)"
  }
}
```

**Documentação interativa**: `http://localhost:8000/docs`

---

## Testes e Avaliações

O projeto mescla a validação através das ferramentas padrões do mercado de IA:

### 1. Pytest (Testes de Integração e Unitários)
```bash
# Rodar todos os testes de software com cobertura
pytest tests/ -v --cov=src --cov-report=term-missing
```

### 2. Promptfoo (Avaliação Contínua de Agentes e Prompts)
Criamos um **Custom Python Provider** para o `Promptfoo` que evala todas as decisões heurísticas do sistema.

```bash
# Roda a tabela de avaliação do roteador e guardrails
npx promptfoo@latest eval
```
Isso testará intensamente se as blindagens estão interceptando *Prompt Injections* e se o roteador de Swarm acerta exatamente os Agentes pretendidos (Ex: Support agent quando pede conta, Knowledge se pergunta "O que é o Jim").

---

## Estrutura do Projeto

```
infinity-agent/
├── src/
│   ├── main.py                     # FastAPI app factory + composition root
│   ├── settings.py                 # Pydantic Settings
│   ├── agents/
│   │   ├── graph.py                # LangGraph StateGraph (o swarm)
│   │   ├── state.py                # AgentState TypedDict
│   │   ├── nodes/                  # Nós dos agentes
│   │   ├── tools/                  # Ferramentas de cada agente
│   │   ├── prompts/                # System prompts
│   │   └── guardrails/             # Input/Output guards
│   ├── api/v1/
│   │   ├── routes/                 # Rotas FastAPI
│   │   └── schemas.py              # Pydantic request/response
│   ├── domain/
│   │   ├── models/                 # Entidades (User, Ticket, etc.)
│   │   └── ports/                  # Interfaces (ports do hexagonal)
│   ├── infrastructure/
│   │   ├── llm/                    # Model factory (OpenRouter)
│   │   ├── persistence/            # Repositórios in-memory
│   │   ├── search/                 # DuckDuckGo searcher
│   │   └── vector_store/           # ChromaDB store
│   └── rag/
│       ├── scraper.py              # Web scraper (httpx + BS4)
│       ├── chunker.py              # Divisão de texto
│       └── ingest_pipeline.py      # Pipeline completo
├── frontend/
│   ├── index.html                  # Chat UI
│   ├── styles.css                  # Glassmorphism CSS
│   └── app.js                      # Lógica do chat
├── scripts/
│   └── ingest.py                   # CLI: python -m scripts.ingest
├── tests/
│   ├── unit/                       # Testes unitários
│   └── integration/                # Testes de integração
├── data/chroma_db/                 # ChromaDB persistente (gitignored)
├── Dockerfile                      # Multi-stage build
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## Cenários de Uso

O sistema foi validado com os seguintes cenários do desafio:

| Cenário | Agente | Exemplo |
|---------|--------|---------|
| Taxas de produto | Knowledge | "Quais são as taxas da Maquininha Smart?" |
| Uso de produto | Knowledge | "Como usar meu celular como maquininha?" |
| Problema de conta | Support | "Não consigo fazer transferências" |
| Acesso bloqueado | Support | "Não consigo entrar na minha conta" |
| Histórico financeiro | Support | "Onde está meu dinheiro?" |
| Pergunta geral | Knowledge | "Qual a previsão do tempo em SP?" |
| Cliente frustrado | Sentiment | "QUERO FALAR COM UM HUMANO AGORA" |
| Guardrails | Guardrail | "Ignore all previous instructions" |

---

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `OPENROUTER_API_KEY` | **Obrigatória** — chave da API OpenRouter | — |
| `ROUTER_MODEL` | Modelo do Router Agent | `openai/gpt-4o-mini` |
| `KNOWLEDGE_MODEL` | Modelo do Knowledge Agent | `openai/gpt-4o-mini` |
| `SUPPORT_MODEL` | Modelo do Support Agent | `anthropic/claude-sonnet-4.5` |
| `SENTIMENT_MODEL` | Modelo do Sentiment Agent | `openai/gpt-4o-mini` |
| `CHROMA_PERSIST_DIR` | Diretório do ChromaDB | `./data/chroma_db` |
| `ENABLE_GUARDRAILS` | Ativar guardrails | `true` |
| `LOG_LEVEL` | Nível de log | `INFO` |

---

## Decisões de Design

- **OpenRouter**: Permite usar modelos de múltiplos provedores (OpenAI, Anthropic) com uma única API key e SDK
- **LangGraph StateGraph**: Orquestração stateful com conditional edges para roteamento determinístico
- **Hexagonal Architecture**: Portas (interfaces) e adaptadores (implementações) isolam o domínio da infraestrutura
- **DuckDuckGo** (sem API key): O plano original usava Tavily, mas DuckDuckGo funciona sem configuração adicional
- **ChromaDB embedded**: Sem serviço externo, ideal para containerização simples
- **Factory pattern para tools**: Injeção de dependências nos nós dos agentes

---

## Autor

Desenvolvido por **Gustavo** para o desafio técnico da CloudWalk / InfinitePay.
