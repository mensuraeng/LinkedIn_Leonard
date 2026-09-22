# LinkedIn Leonard

Sistema de Social Intelligence e operação de LinkedIn orquestrado por **Leonard — Agente Hermes**.

## Estado

- Status: Wave 04 local-only simulator and contract expansion
- Owner operacional: Leonard / Hermes
- Repositório canônico: `mensuraeng/LinkedIn_Leonard`
- Branch canônica: `main`
- Governança: branch → testes → evidência → commit → PR → merge
- Ações públicas: sempre sujeitas a Policy Engine e Approval Gate conforme o PRD

## Documentos canônicos

- `docs/PRD.md` — requisitos completos do produto
- `docs/RUNBOOK.md` — implantação e rotina operacional do Leonard
- `AGENTS.md` — contrato dos agentes e regras de contribuição

## Fundação local-only

O pacote Python em `src/linkedin_leonard` implementa somente o circuito simulado:

```text
Mission → Policy → Approval → Mock Gateway → Verification → Audit
```

- `PolicyEngine` nega ações desconhecidas e mantém todos os writes desligados por padrão. Um write exige, ao mesmo tempo, chave global, política explícita da conta/ação e capability de escrita.
- `Snapshot` canoniza o payload e vincula aprovação, ação e conta por SHA-256. Aprovações expiram e não sobrevivem a qualquer alteração do snapshot.
- `AuditLog` é append-only pela API pública. Eventos expõem somente hash, contagem, chaves allowlisted e códigos sanitizados; conteúdo, segredos e PII não são registrados.
- `MockLinkedInGateway` existe apenas em memória, aceita falhas injetadas (`401`, `403`, `429`, `timeout`) e deduplica somente quando a chave de idempotência e o fingerprint ação/conta/payload são idênticos; colisões são recusadas. O simulador aceita apenas sua identidade canônica e capability mock-only, recusando subclasses, adaptadores e objetos substitutos antes de qualquer leitura ou escrita.
- `MockVerificationBoundary` é uma fronteira distinta, também apenas em memória e mock-only. Ela confirma o receipt vinculado ao snapshot ou devolve `not_found`, `mismatch` ou `timeout`.
- `Simulator` confirma uma missão somente depois de resultado positivo do gateway e de confirmação positiva da verificação do receipt/snapshot.
- `AgentRegistry` aplica capability, conta autorizada, teto de autonomia, orçamento e timeout; ausência de agente, capability ou conta é negada. Um subagente não pode executar write/publicação.
- `BrandRegistry` e `AccountRegistry` separam as políticas mínimas de MENSURA, MIA, PCS e perfil pessoal.
- `QuotaBudget` degrada autonomia em `NORMAL`, `WATCH`, `CONSERVE` e `CRITICAL`; `CircuitBreaker` abre para writes após a quantidade configurada de falhas mock `401`, `403`, `429` ou `timeout`.
- `CortexEventLog` mantém somente eventos sanitizados em memória (`content`, `approval`, `publication_simulated`), com hash de payload e sem integração Córtex.

Não há adapter real, transporte HTTP, navegador, OAuth, cookie, token, endpoint ou dependência de terceiros. A arquitetura não oferece ponto de injeção para transporte real; o teste estrutural em `tests/test_foundation.py` protege esse limite.

## Execução local

Requer Python 3.11 ou superior e nenhuma instalação adicional:

```bash
python -m unittest discover -v
```

## Regra de ouro

Nenhuma mudança persistente deve existir apenas no host do Leonard.  
Se mudou o sistema, a configuração versionável, a documentação, um schema, um teste ou uma política, a mudança deve terminar em Git com rastreabilidade.

## Segurança

Nunca commitar:

- tokens OAuth;
- client secrets;
- cookies de sessão;
- senhas;
- arquivos `.env`;
- PII bruta;
- dumps de produção;
- credenciais do LinkedIn ou de terceiros.

Segredos devem residir fora do GitHub em um Secret Manager ou mecanismo equivalente.

## Fluxo

```text
Objetivo
  ↓
Leonard / Hermes
  ↓
Planejamento + subagentes
  ↓
Policy / Approval
  ↓
Implementação
  ↓
Testes + evidência
  ↓
Commit
  ↓
Pull Request
  ↓
Merge
  ↓
main = estado canônico
```
