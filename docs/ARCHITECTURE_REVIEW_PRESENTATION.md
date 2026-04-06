# Infinity Agent - Presentation Companion (Architecture Review)

Este roteiro acompanha o `architecture_review.md`.
Ele segue a mesma ordem das 14 fases do review original, mas adiciona os pontos de decisao arquitetural que costumam faltar na fala.

Como usar:
- Tela 1: `architecture_review.md`
- Tela 2: este roteiro
- App para demos curtas
- `/docs` para fechamento

Tempo alvo: 12 a 15 minutos.

---

## Fase 1 - Current Project State

O que mostrar:
- secao `1) Current Project State`

Como falar:
"Aqui eu posiciono o estado atual: o sistema ja esta pronto para avaliacao, com swarm de 4 agentes, API, RAG, web search, handoff humano, Docker e testes."

Decisao arquitetural:
- Escolhemos fechar o escopo em uma arquitetura completa fim a fim, nao em um prototipo de prompt.

Trade-off:
- Mais componentes para integrar.
- Em troca, mais confiabilidade e menos risco de demo quebrar por comportamento imprevisivel.

---

## Fase 2 - Architecture Summary

O que mostrar:
- secao `2) Architecture Summary`
- stack e model mapping

Como falar:
"Aqui esta a fundacao em runtime: LangGraph para orquestracao, FastAPI para API, Chroma para conhecimento, SQLite para checkpoint, Brave para web search e OpenRouter para modelos por papel."

Decisoes arquiteturais:
- Orquestracao por grafo (LangGraph) em vez de fluxo linear.
- Modelos por papel (router rapido, knowledge/support mais robustos).

Trade-off:
- Configuracao mais complexa.
- Beneficio: separacao clara de responsabilidade, previsibilidade e custo melhor controlado.

---

## Fase 3 - Real Code Map (by Layer)

O que mostrar:
- secao `3) Real Code Map (by Layer)`

Como falar:
"A estrutura esta em camadas: API, orquestracao, nodes, tools, dominio e infraestrutura. Isso evita acoplamento direto e facilita manutencao."

Decisao arquitetural:
- Adotar portas/adapters no dominio para trocar infraestrutura sem quebrar agente.

Exemplo rapido:
- O repositório de usuario pode sair de in-memory para banco real sem reescrever o fluxo dos agentes.

---

## Fase 4 - Runtime Flow (Actual)

O que mostrar:
- secao `4) Runtime Flow (Actual)`

Como falar:
"Toda mensagem passa por input guard, roteador, agente especializado e output guard. No streaming, enviamos status e chunks para nao deixar o usuario no escuro."

Decisoes arquiteturais:
- Guardrail em duas pontas: entrada e saida.
- Endpoint de streaming separado do endpoint padrao.

Trade-off:
- Mais logica de ciclo de resposta.
- Beneficio: UX melhor e menor risco de saida insegura.

---

## Fase 5 - Agent Graph Diagram

O que mostrar:
- secao `5) Agent Graph Diagram`

Como falar:
"Esse diagrama representa a politica de controle do sistema. O objetivo aqui foi ter um caminho simples de auditar: START, validacao, roteamento, especializacao e sanitizacao final."

Decisao arquitetural:
- Grafo explicito para tornar roteamento auditavel e testavel.

---

## Fase 6 - System Context Diagram

O que mostrar:
- secao `6) System Context Diagram`

Como falar:
"Aqui eu mostro as fronteiras do sistema: o que e interno, o que e externo e o que e opcional. Isso deixa claro onde estao dependencias criticas e pontos de falha."

Decisoes arquiteturais:
- Evolution API como dependencia opcional.
- Persistencia local de estado (SQLite) e conhecimento (Chroma) no core.

Trade-off:
- Menos acoplamento com canal de mensageria na demo.
- Handoff continua disponivel quando necessario.

---

## Fase 7 - Request Lifecycle

O que mostrar:
- secao `7) Request Lifecycle`

Como falar:
"O ciclo reforca uma escolha importante: antes de gerar resposta, o sistema escolhe o caminho certo. Em atendimento, roteamento correto vale tanto quanto qualidade de texto."

Decisao arquitetural:
- Override deterministico para termos operacionais de status/outage indo para Support.

Por que isso importa:
- Reduz erro de rota em cenarios criticos, que eram os mais sensiveis do challenge.

---

## Fase 8 - WhatsApp Escalation and Human Handoff

O que mostrar:
- secao `8) WhatsApp Escalation and Human Handoff`

Como falar:
"No handoff, a decisao foi continuidade assincroma. Em vez de prometer atendimento humano instantaneo no mesmo canal, o sistema abre sessao e entrega contexto para o operador seguir com qualidade."

Decisao arquitetural:
- Handoff assincromo com payload enriquecido.

Trade-off:
- Nao e chat humano sincrono imediato.
- Em troca, temos resiliencia operacional e menos dependencia de disponibilidade em tempo real.

---

## Fase 9 - Hardening Implemented

O que mostrar:
- secao `9) Hardening Implemented`

Como falar:
"Aqui estao os mecanismos que deixam o comportamento menos fragil: override do router, fallback de sobreposicao no knowledge e caminho web deterministico para perguntas gerais."

Decisoes arquiteturais:
- Evitar fallback generico quando o caso e operacional.
- Evitar depender so de inferencia livre do modelo para decidir tudo.

---

## Fase 10 - Docker and Runtime Topology

O que mostrar:
- secao `10) Docker and Runtime Topology`

Como falar:
"O deploy foi pensado para avaliacao objetiva: sobe o core com um comando, e o WhatsApp entra por profile quando necessario."

Decisao arquitetural:
- `infinity-agent` sempre disponivel.
- `evolution-api` opcional por profile.

Por que foi escolhido:
- Minimiza pontos de falha na avaliacao e simplifica reproducao.

---

## Fase 11 - OpenAPI and Observability Entry Points

O que mostrar:
- secao `11) OpenAPI and Observability Entry Points`
- abrir `/docs`

Como falar:
"Aqui eu mostro governanca de API: contrato claro, health endpoint e ponto de inspecao. Isso facilita validacao tecnica sem depender do frontend."

Decisao arquitetural:
- Tratar API como produto de primeira classe para avaliador e operacao.

---

## Fase 12 - Excalidraw Build Guide

O que mostrar:
- secao `12) Excalidraw Build Guide`

Como falar:
"Essa parte nao muda o sistema, mas melhora comunicacao tecnica. Padronizar visual ajuda a reduzir ambiguidade na leitura da arquitetura."

---

## Fase 13 - 10-15 Minute Presentation Script

O que mostrar:
- secao `13) 10-15 Minute Presentation Script`

Como falar:
"Eu sigo essa distribuicao para equilibrar profundidade tecnica e demonstracao real. O foco nao e mostrar tudo, e mostrar as decisoes certas."

Dica de ritmo:
- Se estiver estourando tempo, reduza detalhes da fase 12 e mantenha fases 7, 8 e 9 completas.

---

## Fase 14 - Final Notes

O que mostrar:
- secao `14) Final Notes`

Como falar:
"Fechando: este review e orientado ao que esta implementado hoje. Se o comportamento do sistema muda, o documento muda junto para manter coerencia tecnica."

---

## Bloco de demo (prompts)

Use nessa ordem:
1. `Quais sao as taxas da Maquininha Smart?`
2. `Quais as principais noticias de Sao Paulo hoje?`
3. `Qual o status atual dos servicos da InfinitePay?`
4. `Quero falar com um atendente humano agora.`

Plano B:
- `Quando foi o ultimo jogo do Palmeiras?`

---

## Frases curtas de decisao (para parecer menos raso)

- "A decisao aqui foi priorizar previsibilidade sobre improviso do modelo."
- "Preferimos separar responsabilidade por agente para reduzir acoplamento."
- "Em cenarios operacionais, rota correta vem antes de resposta bonita."
- "O handoff foi desenhado para continuidade com contexto, nao so transferencia."
- "A topologia Docker privilegia reproducao para avaliacao tecnica."

---

## Encerramento curto (30s)

"Resultado final: arquitetura modular, com decisoes de robustez explicitas para roteamento, recuperacao de conhecimento, suporte operacional e escalonamento humano. A solucao atende o challenge com foco em confiabilidade, e nao apenas em geracao de texto."
