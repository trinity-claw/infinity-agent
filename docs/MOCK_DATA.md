# Mock Data Guide (Evaluator UX)

The support flow uses an in-memory repository with seeded users and transactions.
This allows evaluators to test support scenarios immediately, without external databases.

Source:
- `src/infrastructure/persistence/in_memory_user_repo.py`

## Recommended Demo User IDs

| user_id | Profile | Typical Scenarios |
|---|---|---|
| `client789` | Active PF account | login/help flow, balance, transaction checks |
| `client001` | Active PJ account | business transactions, support troubleshooting |
| `client002` | Active PJ, higher volume | transfer/pending transaction checks |
| `client003` | Inactive account | blocked account / documentation issue |
| `client004` | Active PJ (link de pagamento) | payment-link support scenarios |
| `client_pelissarog_gmail_com` | Active PF account (demo owner) | escalation/handoff demo, WhatsApp contact enrichment |
| `client_pelissarog_gmail.com` | Alias ID for same profile | compatibility with historical session identifiers |
| `client_peli` | Short alias for same profile | quick manual demo ID |

## Frontend Default

The sidebar default mock user is set to `client789` to improve first-run evaluator experience.

File:
- `frontend-react/src/components/Sidebar.jsx`

## Suggested Support Test Prompts

Use one of these with `user_id=client789`:
- `Nao consigo acessar minha conta.`
- `Quero ver meu saldo disponivel.`
- `Mostre meu historico de transacoes.`
- `Quero abrir um ticket de suporte.`

Use this with `user_id=client003`:
- `Minha conta foi bloqueada e nao consigo entrar.`

## Notes

- Data is intentionally in-memory for challenge demo simplicity.
- Restarting the process resets tickets created during the session.
- If the evaluator uses a non-seeded `user_id`, support tools will return "user not found".
  For a successful support walkthrough, use one of the seeded IDs above (recommended: `client789`).
- `InMemoryUserRepository` also attempts normalized ID matching (alphanumeric only),
  which improves compatibility for IDs coming from email-derived sanitization.
