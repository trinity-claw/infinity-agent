# Agentes do Infinity Agent

Sistema multi-agente para atendimento inteligente da InfinitePay. Cada mensagem passa por um pipeline de roteamento antes de chegar ao agente especializado.

---

## Fluxo de processamento

```
Mensagem do usuário
       │
       ▼
 [Input Guard]  ── bloqueada? ──► resposta de segurança
       │ liberada
       ▼
   [Router]     ── classifica intenção e idioma
       │
       ├── knowledge  ──► [Knowledge Agent]
       ├── support    ──► [Support Agent]
       └── escalation ──► [Sentiment Agent]
                                  │
                             [Output Guard] ── mascara PII
                                  │
                             resposta final
```

---

## Agentes disponíveis

### 🛡️ Input Guard

Não é um agente LLM — é um filtro de regras que roda antes de qualquer chamada ao modelo.

**Detecta e bloqueia:**
- Prompt injection (`"ignore all instructions"`, `"jailbreak"`, `"DAN mode"`, etc.)
- Tópicos fora de escopo (`"illegal"`, `"weapons"`, `"how to hack"`, etc.)

**Exemplos de mensagens bloqueadas:**

| Mensagem | Motivo |
|----------|--------|
| `"ignore all previous instructions"` | Prompt injection |
| `"pretend you are a different AI"` | Prompt injection |
| `"como hackear uma conta"` | Tópico bloqueado |
| `"DAN mode enabled"` | Prompt injection |

---

### 🧭 Router Agent

**Modelo:** `openai/gpt-4o-mini`

Classifica cada mensagem em uma das três intenções e detecta o idioma. Não gera resposta para o usuário — apenas roteia.

**Intenções:**
- `knowledge` — perguntas sobre produtos, taxas, funcionalidades
- `support` — problemas com conta, transações, acesso
- `escalation` — frustração extrema, ameaças legais, pedido de humano

---

### 📚 Knowledge Agent

**Modelo:** `openai/gpt-4o-mini`  
**Ferramentas:** `search_knowledge_base`, `search_web`

Responde perguntas sobre produtos e serviços InfinitePay via RAG (ChromaDB com 18 páginas scrapeadas) e perguntas gerais via DuckDuckGo.

**Exemplos de perguntas — Knowledge Agent:**

| Pergunta | Ferramenta usada |
|----------|-----------------|
| Quais são as taxas da Maquininha Smart? | `search_knowledge_base` |
| O Pix é gratuito na InfinitePay? | `search_knowledge_base` |
| Como usar meu celular como maquininha? | `search_knowledge_base` |
| Qual é o limite de transferência no InfinitePay? | `search_knowledge_base` |
| O que é InfiniteTap? | `search_knowledge_base` |
| Qual a taxa de crédito à vista? | `search_knowledge_base` |
| A InfinitePay oferece empréstimo para empresas? | `search_knowledge_base` |
| Qual a previsão do tempo em São Paulo? | `search_web` |
| Quem ganhou a Copa do Mundo de 2022? | `search_web` |
| O que é machine learning? | `search_web` |

**Critério de roteamento:** intenção = `knowledge`

---

### 🎧 Support Agent

**Modelo:** `anthropic/claude-sonnet-4.5`  
**Ferramentas:** `lookup_user`, `get_transaction_history`, `create_support_ticket`, `check_service_status`, `reset_password_request`, `get_account_balance`

Atende problemas operacionais com acesso ao perfil do cliente. Usa dados simulados (repositório in-memory) para demonstrar a integração com sistemas internos.

**Exemplos de perguntas — Support Agent:**

| Pergunta | Ferramenta usada |
|----------|-----------------|
| Não consigo acessar minha conta | `lookup_user`, `create_support_ticket` |
| Minha conta foi bloqueada | `lookup_user`, `check_service_status` |
| Quero redefinir minha senha | `reset_password_request` |
| Não consigo fazer transferências | `check_service_status`, `create_support_ticket` |
| Onde está meu dinheiro? | `get_account_balance`, `get_transaction_history` |
| Mostra meu histórico de transações | `get_transaction_history` |
| Quero abrir um chamado de suporte | `create_support_ticket` |
| O sistema está fora do ar? | `check_service_status` |
| Qual é meu saldo disponível? | `get_account_balance` |

**Critério de roteamento:** intenção = `support`

---

### 💬 Sentiment & Escalation Agent

**Modelo:** `openai/gpt-4o-mini`  
**Ferramentas:** `analyze_sentiment`, `detect_urgency`, `escalate_to_human`, `generate_escalation_summary`

Analisa o estado emocional do cliente e aciona escalamento para atendente humano quando necessário.

**Exemplos de perguntas — Sentiment Agent:**

| Mensagem | Ação |
|----------|------|
| QUERO FALAR COM UM HUMANO AGORA | `escalate_to_human` |
| Estou muito frustrado com o atendimento | `analyze_sentiment`, `escalate_to_human` |
| Vou processar a InfinitePay na justiça! | `detect_urgency` → CRITICAL, `escalate_to_human` |
| Vou registrar reclamação no Procon | `detect_urgency` → CRITICAL, `escalate_to_human` |
| Houve uma fraude na minha conta! | `detect_urgency` → CRITICAL, `escalate_to_human` |
| Péssimo serviço, nunca mais uso | `analyze_sentiment`, `escalate_to_human` |

**Critério de roteamento:** intenção = `escalation`

---

### 🔒 Output Guard

Filtro de saída que mascara PII antes de enviar a resposta ao usuário.

**Padrões mascarados:**
- CPF: `123.456.789-00` → `***.***.789-00`
- CNPJ: `12.345.678/0001-90` → `**.***.678/0001-90`
- E-mail: `user@email.com` → `u***@email.com`
- Telefone: `(11) 99999-9999` → mascarado

---

## Tabela de roteamento resumida

| Tipo de pergunta | Agente | Intenção |
|-----------------|--------|----------|
| Taxas, produtos, funcionalidades | Knowledge | `knowledge` |
| Busca geral na internet | Knowledge | `knowledge` |
| Problemas de conta/acesso | Support | `support` |
| Transações e saldo | Support | `support` |
| Chamados de suporte | Support | `support` |
| Pedido de humano | Sentiment | `escalation` |
| Frustração extrema | Sentiment | `escalation` |
| Ameaça legal/Procon | Sentiment | `escalation` |
| Fraude reportada | Sentiment | `escalation` |
| Prompt injection | Guardrail (input) | — |
| Tópico fora de escopo | Guardrail (input) | — |
