# Checklist — Maestria Técnica

Itens que demonstram boas práticas de engenharia para recrutadores e avaliadores técnicos.

---

## Arquitetura

- [x] **Hexagonal Architecture** — domínio isolado com ports (ABCs) e adapters de infraestrutura
- [x] **Dependency Injection** — dependências injetadas via factory functions, nunca instanciadas dentro dos nós
- [x] **Application Factory** — `create_app()` cria o FastAPI, permite testes sem efeitos colaterais
- [x] **Composition Root** — `src/container.py` centraliza a criação dos singletons; rotas e main importam dali
- [x] **Separation of Concerns** — agents, API, domain, infrastructure e rag são camadas independentes
- [x] **No circular imports** — container.py quebra o ciclo main ↔ routes
- [ ] **Event-driven entre agentes** — os nós comunicam-se via estado LangGraph, mas um bus de eventos explícito demonstraria desacoplamento ainda maior

---

## Qualidade de Código

- [x] **Type hints** em todas as funções públicas
- [x] **Pydantic v2** para validação de schemas de request/response e settings
- [x] **Docstrings** em todos os módulos e funções públicas
- [x] **`from __future__ import annotations`** para forward references
- [x] **Logging estruturado** — format com timestamp, nível e nome do módulo
- [x] **Sem imports inline dentro de funções** (exceto lazy deferral documentado no container)
- [ ] **Pre-commit hooks** — `ruff`, `mypy`, `black` configurados em `.pre-commit-config.yaml`
- [ ] **`pyproject.toml` com lint rules** — seção `[tool.ruff]` e `[tool.mypy]`

---

## Testes

- [x] **49 testes passando** — unitários e de integração
- [x] **Testes unitários sem I/O** — nenhum acesso real a DB, LLM ou rede
- [x] **Testes de integração com mocks de fronteira** — swarm e ChromaDB mockados via `unittest.mock`
- [x] **Fixtures reutilizáveis** — `conftest.py` com `mock_swarm` e `mock_store`
- [x] **Cenários negativos cobertos** — mensagem vazia, campos ausentes → 422
- [x] **Cobertura dos guardrails** — injection, tópicos bloqueados, PII masking
- [ ] **Coverage report acima de 80%** — `pytest --cov=src --cov-fail-under=80`
- [ ] **Testes de contrato** — validar que o schema de resposta `/v1/chat` não quebra entre versões
- [ ] **Testes de carga** — `locust` ou `k6` para medir RPS e p95 latency

---

## API

- [x] **OpenAPI automático** — `/docs` e `/redoc` gerados pelo FastAPI
- [x] **Versionamento** — prefixo `/v1/` em todos os endpoints
- [x] **Schemas tipados** — `ChatRequest`, `ChatResponse`, `HealthResponse` com Pydantic
- [x] **Health check** — `/v1/health` reporta status de cada serviço
- [x] **Error responses tipadas** — `ErrorResponse` mapeado nos `responses={}` do decorator
- [ ] **Rate limiting** — `slowapi` ou middleware customizado para proteger contra abuso
- [ ] **Request ID** — header `X-Request-ID` gerado no middleware, logado e retornado
- [ ] **Paginação** no histórico de conversas (se persistência for adicionada)

---

## Segurança

- [x] **Input guardrails** — detecta prompt injection com 13 padrões
- [x] **Output guardrails** — mascara PII (CPF, CNPJ, e-mail, telefone) na saída
- [x] **CORS configurado** — middleware com origens explícitas
- [x] **API key via variável de ambiente** — nunca hardcoded
- [x] **`.env.example`** documenta variáveis sem expor segredos
- [ ] **HTTPS enforced** — redirecionar HTTP → HTTPS em produção
- [ ] **Helmet headers** — `X-Content-Type-Options`, `X-Frame-Options`, `CSP`
- [ ] **Input sanitization** — limite de tamanho da mensagem validado no schema (atualmente só `min_length=1`)
- [ ] **Audit log** — registrar user_id, intent e agent_used em cada requisição

---

## Observabilidade

- [x] **Logging estruturado** com níveis configuráveis por `LOG_LEVEL`
- [x] **Logs de roteamento** — agent chamado, intent detectada, user_id
- [ ] **Tracing distribuído** — OpenTelemetry + Jaeger/Zipkin
- [ ] **Métricas** — Prometheus + Grafana: latência por agente, taxa de escalamento, hit rate do RAG
- [ ] **Alertas** — PagerDuty ou similar para taxa de erro > threshold
- [ ] **Sentry** para captura de exceções em produção

---

## Infraestrutura

- [x] **Docker multi-stage** — build stage separa dependências de dev; imagem final é enxuta
- [x] **docker-compose** — um comando sobe tudo
- [x] **Pydantic Settings** — todas as configs via env vars com defaults razoáveis
- [ ] **Health probe no Dockerfile** — `HEALTHCHECK` instrução para orquestradores
- [ ] **Non-root user no container** — adicionar `USER appuser` no Dockerfile
- [ ] **CI/CD pipeline** — `.github/workflows/ci.yml` rodando `pytest` e `ruff` em PR
- [ ] **Kubernetes manifests** — Deployment, Service, HPA para auto-scaling
- [ ] **ChromaDB remoto** — substituir embedded por ChromaDB server ou Qdrant em produção

---

## RAG Pipeline

- [x] **Scraping de 18 URLs** — httpx + BeautifulSoup4
- [x] **Chunking com overlap** — 512 chars, 100 de overlap
- [x] **IDs determinísticos** — hash do conteúdo garante idempotência no ingest
- [x] **Metadata preservada** — source_url e section em cada chunk
- [ ] **Re-ranking** — cross-encoder para reordenar os top-k resultados por relevância
- [ ] **Hybrid search** — combinar busca vetorial + BM25 para melhor recall
- [ ] **Avaliação do RAG** — RAGAS metrics: faithfulness, answer_relevancy, context_recall
- [ ] **Pipeline de atualização** — webhook ou cron para re-ingestar quando o site mudar

---

## Frontend

- [x] **Design system consistente** — CSS variables, tema escuro, glassmorphism
- [x] **Responsive** — breakpoints 900px, 768px, 480px
- [x] **Acessibilidade básica** — `aria-label`, elementos semânticos (`<aside>`, `<main>`, `<header>`)
- [x] **Typewriter effect** — simula streaming para UX mais fluida
- [x] **WebGL shader background** — animação Three.js com fragment shader customizado
- [x] **Markdown rendering** — respostas dos agentes renderizadas como markdown
- [ ] **Streaming real** — Server-Sent Events (SSE) para mostrar tokens conforme chegam
- [ ] **PWA** — `manifest.json` + Service Worker para uso offline e instalação
- [ ] **Dark/light toggle** — preferência salva em localStorage
- [ ] **Testes E2E** — Playwright cobrindo o fluxo completo de uma conversa

---

## Prioridades para produção

1. CI/CD pipeline (bloqueia deploy seguro)
2. Rate limiting (segurança mínima)
3. Request ID no middleware (rastreabilidade)
4. Coverage mínima 80% (confiança no código)
5. ChromaDB server ou Qdrant (persistência real)
6. Streaming SSE (UX esperada em 2025)
