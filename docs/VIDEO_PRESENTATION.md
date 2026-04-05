# Roteiro de Apresentação em Vídeo — Infinity Agent Swarm

Este documento é o seu guia técnico e narrativo para gravar a apresentação do desafio da InfinitePay/CloudWalk. Ele organiza os pontos altos do projeto em um fluxo lógico e engajador.

---

## 🕒 Parte 1: Introdução & Filosofia da Arquitetura (0:00 - 1:30)

**Abertura:**
- "Olá! Sou o Gustavo e vou apresentar minha solução para o Code Challenge do Infinity Agent, focado em suportar as operações da CloudWalk."

**A Arquitetura (O Grande Diferencial):**
- Mostre rapidamente o esquema de blocos em `AGENTS.md` ou o diagrama principal.
- Explique o que foi construído: um **Sistema Multi-Agente Stateful (LangGraph)** + FastAPI + Injeção de Dependências, operando como um **Daemon Nativo para WhatsApp** na VPS, ao invés de ser apenas um projetinho solto para terminal.
- Mencione os 3 agentes chave pedidos: **Router**, **Knowledge (RAG)** e **Support Agent**, além do seu "bônus": O **Sentiment & Escalation Agent**.

## 🛡️ Parte 2: A Blindagem / Guardrails (1:30 - 2:30)

**Demonstre Segurança desde o Começo:**
- Abra o arquivo `src/agents/guardrails/input_guard.py` e `blocklist.py`.
- Mostre que você traduziu e adaptou regras estritas para o **Português Brasileiro**. 
- Diga: *"O sistema detecta prompt injections (Modo DAN, etc.) e assuntos bloqueados (fraude, violência, compras Ilegais) **antes mesmo de gastar tokens** invocando agentes LLM."*
- **A Cereja:** Mostre também o *Output Guard* (`output_guard.py`) em ação: *"Desenvolvi um mascarador de PII. Nenhuma resposta final enviada pro usuário revelará dados críticos inteiros, como um CPF inteiro, para ele, evitando data leaks."*

## 🧠 Parte 3: O Router & Knowledge Agent - O Sistema RAG (2:30 - 4:00)

**A Execução do RAG:**
- Explique o Roteador, guiado por *Intenções Determinísticas* do LangGraph (`router_node.py`). Ele descobre se é dúvida de uso, consulta técnica ou frustração de conta.
- Abra um teste prático na interface (O web-chat escuro de testes).
- Digite uma dúvida como: *"Como uso o radar de boletos no JIM?"* 
- Destaque: *"Recentemente fiz a ingestão orgânica de chunks extraídos diretamente da base oficial de ajuda do JIM da InfinitePay para nosso banco **ChromaDB**. O bot consulta e traz a reposta embasada na realidade do produto."*
- Menção honrosa a Busca Genérica: *"Se perguntarem o fuso horário ou algo fora do produto, ele executa um DuckDuckGo Search nativamente."*

## 🎧 Parte 4: A Inteligência de Suporte & Escalonamento (4:00 - 5:30)

**O Agente Focado em Functions:**
- Mude o foco para o *Support Agent* (`support_node.py`).
- Mostre que ele possui 6 "Tool Calls" estritamente codadas (checar saldo, última transação, status log, redefinir senha, etc). 
- Diga: *"Ele varre os repositórios injetados em memória. O sistema está 100% blindado por Domain Driven Design.*"

**O Agente de Sentimento & Zap:**
- *"Aqui está outro "a mais" gigante: O 4º Agente de Sentimento".*
- Simule um cliente agressivo/em fúria. Digite: *"Vocês bloquearam minha conta, resolvam isso AGORA ou vou processar!"*
- O roteador direcionará direto pra linha de Contingência (Escalonamento Humano).
- A API **Silencia** o robô. E, ativando a Flag da `Evolution API`, lança a sessão do cliente para o WhatsApp de um operador real para ele assumir.

## 🚀 Parte 5: Deploy Real com Evolution API & Persistência (5:30 - 7:00)

**O Golpe de Misericórdia (Setup Produtivo):**
- Mostre o novo `docs/DEPLOYMENT.md` ou a rota `webhook.py`.
- Explique *"Um Bot Cloud não vive e morre no mesmo request REST. APIs de WhatsApp caem por timeout de LLMs."*
- Explique que o projeto conta com **sqlite_saver** injetado nativamente no `LangGraph`, registrando a "thread" baseada no telefone do WhatsApp. A pessoa te manda "Oi" de manhã e atarde ela pede "Diz meu saldo", o GPT se lembra de toda a conversa.
- Mostre que o endpoint `/webhook` devolve `200 OK` na hora pro Zap e enfileira a IA num `FastAPI BackgroundTasks` para responder via Cliente HTTP sem enroscar a fila.

## 🧪 Parte 6: Avaliação Contínua e QA Rigorosa (7:00 - 8:00)

**Validação Definitiva:**
- Dê destaque aos testes e avaliações:
- *"Rodamos 2 frentes de validação: O clássico framework Pytest com 100% de automação de testes de Unidade e Integração..."*
- (Nesta hora, mencione o que fez hoje:) *"E também implementei a exigência fina do **promptfoo**. Criei um custom provider de python que simula instâncias do LangGraph via JSON e aciona as baterias de testes avaliativos (`promptfooconfig.yaml`), testando de ponta a ponta todas as blindagens (jailbreaks) e rotas comportamentais dos LLMs em massa contra nossas Asserções (Asserts)."*

---

> [!TIP]
> **Dica para Gravação:** Abra suas abas organizadas! 
> 1. Terminal com `docker-compose up` e `npx promptfoo@latest eval` do lado esquerdo.
> 2. O seu Visual Studio Code.
> 3. O painel web de design *Glassmorphism* Premium ou o terminal mostrando a evolution conectando.
> Mostrar código bem identado com DDD e padrões organizados ganha absurdamente a empatia de eng. seniores!
