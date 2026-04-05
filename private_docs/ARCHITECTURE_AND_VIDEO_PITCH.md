# Roteiro de Vídeo e Defesa de Arquitetura (Confidencial/Privado)

> **ATENÇÃO:** Este diretório (`private_docs`) foi propositalmente incluído no `.gitignore` por boas práticas de DevSecOps, não subindo para o Github mantendo o repositório principal blindado. Use este documento como seu roteiro base de gravação e consulta rápida técnica (Cheat Sheet) das suas escolhas para apresentar aos recrutadores do Code Challenge da CloudWalk.

---

## 1. Defendendo as Decisões de Arquitetura e Trade-Offs

Este é o diferencial. Todo Tech Lead sênior julga por "trade-offs", e entender por que escolhemos caminho X ao invés de Y garante a senioridade do desafio.

### Por que usar rotinas `async / await` no Python inteiro (FastAPI)?
- **A Defesa (O "Porquê"):** Nossa aplicação é **I/O Bound**. Em um sistema de Agentes com LLM e Scraping, a aplicação passa 99% do seu tempo esperando a porta de rede da OpenRouter, banco de vetores e a DuckDuckGo responderem. Se utilizássemos funções síncronas convencionais (`def` comum padrão Django/Flask-antigo), uma única request "travaria" a thread principal da API (o servidor). Ao adotar `async def` nativo atrelado à engine Uvicorn/FastAPI, utilizamos um paradigma de *Event Loop Concorrente*. Isso significa que quando um "Agente" paralisa aguardando a API do GPT, o Event Loop do Python instantaneamente atende outros clientes na web ou WhatsApp, garantindo que mesmo usando apenas nossa simples VPN na DigitalOcean com 1 vCPU, a vazão suporte dezenas de transações por segundo.

### Controle de Agentes: Por que *LangGraph* ao invés do *LangChain* Clássico ou *CrewAI*?
- **O Problema:** A maioria dos frameworks (Autogen/Crew) adotam orquestração "Manager" (uma caixa preta que bate papo internamente ad-infinitum podendo alucinar ou gerar latência extrema) ou "Pipes Lineares" (LangChain raiz).
- **A Defesa (O "Porquê"):** O **LangGraph** injeta a premissa rigorosa de Máquina de Estados Cíclica e *Teoria de Grafos* em IA. Construímos grafos determinísticos. Eu extraí o LLM para um papel central (o **Router**), que acerta de fato qual Agente (Nó) processará o fluxo, enviando flags condicionais exatas pelas arestas (*Conditional Edges*). Isso significa previsibilidade bancária: Agente de Suporte trata Support e nunca vai misturar alucinação de RAG na conta do usuário, pois o grafo garante a trilha de segurança. Isso barateia a requisição e foca na segurança.

### A Questão do Frontend: Por que *React + Vite* com *Multi-Stage Dockerfile*?
- **O Problema:** O design do Vanilla HTML estava pronto e estético, porém pouco passível a manutenção no mercado.
- **A Defesa (O "Porquê"):** Reconstruí o projeto usando a tríade React, Vite e WebGL Hooks. A genialidade aqui não é usar framework modinha, mas a infraestrutura baseada no **Multi-Stage Dockerfile**: No momento da pipeline, no *Stage 1 (Node.js)*, orquestramos todas as bibliotecas da interface e buildamos. Em seguida, descartamos tudo, sugando apenas a pasta `dist/` estática gerada e a inserimos no *Stage 2 (Python Alpine)* nativamente pendurada no FastAPI (no `/v1/chat`). Essa decisão de DevSecOps reduziu a superfície de ataque a vulnerabilidades (descartando npm de produção) e otimizou imagens Docker para meros ~100MB.

### Por que o uso isolado de `SqliteSaver` no LangGraph?
- **O Problema:** Agentes em HTTP "Rest" nascem e morrem a cada request—Eles são Stateless. Ao usar num WhatsApp nativo, a IA esquecia do passado.
- **A Defesa (O "Porquê"):** Instalei a engine de interceptação SQLite (`checkpointer=SqliteSaver(conn)`) na inicialização do Swarm. Dessa forma, criei um conceito de *Long-Term Session*. O número de WhatsApp torna-se a *Thread ID* nativa no banco. Isso habilita o usuário reclamar "está ruim," nós darmos "handoff" pra atendente humano através de flags de status da thread e, semanas depois, o modelo acessar as mensagens vetoriais daquela linha em ms, tudo isso escalável pra uma instância Cloud leve.

### Evolution API + BackgroundTasks = Operação Daemon Imune a TimeOut
- **O Problema:** Webhooks oficiais (Meta) exigem HTTP 200 de retorno absoluto em até `15~30s`, senão cortam o script. A Inferência inteira RAG+IA passa de 15s fácil.
- **A Defesa (O "Porquê"):** Rompi o padrão MVC e adotei `FastAPI BackgroundTasks`. A Rota `/v1/webhook` bateu o json, minha API responde assíncronamente um `200 OK` isolado do processamento. Em *background worker*, a chain é ativada. O motor envia, de forma ativa (como cliente do WhatsApp), a requisição pro webhook Evolution da porta remota finalizar o delivery da mensagem.

---

## 2. A Apresentação — Checklist e Estrutura Narrativa

**(Duração recomendada: 4 a 6 Minutos)**

**A. Introdução (0:00)**
> "Olá! Aqui está o review da minha escalada completa do Infinity Agent. O foco primordial foi provar domínio ponta-a-ponta em Engenharia de Software Moderna (Security/Decoupling/State Machines) em prol de um Agent Swarm hiper-seguro."

**B. Apresentação do Escopo "LangGraph Mapeado Determinístico" (1:00)**
- Mostre o `container.py` e depois o block dos agents. A pontuação se dá pela Segurança. Mostre o arquivo de Injections (`guardrails/input_guard.py` e suas blocklists abrasileiradas e mascaradores de dados LGPD `output_guard.py`) operando na borda, economizando tokens e filtrando "Prompt Injections do Modo DAN" na raiz.

**C. Demo: RAG com JIM Atualizado + Grafo Roteador (2:30)**
- Abra a interface na porta que já ligamos `8002` (ou porta `8000`). Digite *"O que o JIM consegue rastrear nos boletos pra mim?"*. Deixe renderizar.
- Apresente que o orquestrador captou intention=Knowledge, vetorizou em ChromaDB chunks exatos extraídos via Beautiful Soup do guia da InfinitePay, provando um bot atrelado à realidade da empresa (E se não existe documento, o DuckDuckGo Search atua).

**D. Demo: Suporte + HandOff Humano Nativo do Whatsapp (4:00)**
- Abra os Testes. Explique o Flow de `Sentiment/Escalation`. Digite palavrões reclamando de fraude.
- O grafo envia o contexto para a aresta (edge) de escalonamento. *Neste momento, a thread fica bloqueada por sqlite_saver e o Bot é Desativado*, acionando a Evolution API pro WhatsApp da Central Humana e finalizando a rotina com zero estresse.

**E. Encerramento: Promptfoo & Containerização Multi-Stage (5:30)**
- Termine dando checkmate, abrindo seu terminal rodando o `promptfoo` que simula assertividades e mostra as métricas dos testes end-to-end de prompt validation, atreladas a uma arquitetura limpa em Docker Multi-Stage (Frontend em Node -> Backend Async).

> Bom show. Toda falha prevista do desafio está mitigada (Timeouts, Injections, Rotas lineares mal traçadas e UI acoplada). O código providenciará a autoridade natural para a vaga.
