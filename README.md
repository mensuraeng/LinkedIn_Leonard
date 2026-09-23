# LinkedIn Leonard

Sistema de Social Intelligence e operação de LinkedIn orquestrado por **Leonard — Agente Hermes**.

## Estado

- Status: Wave 04 local-only simulator — IMPLEMENTED; final-head review and promotion remain gated
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
Mission → AgentRegistry → AccountRegistry → BrandRegistry → Policy → Approval → Mock Gateway → Verification → Audit
```

- `PolicyEngine` nega ações desconhecidas e mantém todos os writes desligados por padrão. Um write exige, ao mesmo tempo, chave global, política explícita da conta/ação e capability de escrita.
- `Snapshot` canoniza o payload e vincula aprovação, ação e conta por SHA-256. Aprovações expiram e não sobrevivem a qualquer alteração do snapshot.
- `AuditLog` é append-only pela API pública. Eventos expõem somente hash, contagem, chaves allowlisted e códigos sanitizados; conteúdo, segredos e PII não são registrados.
- `MockLinkedInGateway` existe apenas em memória, aceita falhas injetadas (`401`, `403`, `429`, `timeout`) e deduplica somente quando a chave de idempotência e o fingerprint ação/conta/payload são idênticos; colisões são recusadas. O simulador aceita apenas sua identidade canônica e capability mock-only, recusando subclasses, adaptadores e objetos substitutos antes de qualquer leitura ou escrita.
- `MockVerificationBoundary` é uma fronteira distinta, também apenas em memória e mock-only. Ela confirma o receipt vinculado ao snapshot ou devolve `not_found`, `mismatch` ou `timeout`.
- `Simulator` confirma uma missão somente depois de resultado positivo do gateway e de confirmação positiva da verificação do receipt/snapshot.
- `AgentRegistry` aplica capability, conta autorizada, teto de autonomia, orçamento e timeout; ausência de agente, capability ou conta é negada. Um subagente não pode executar write/publicação.
- `BrandRegistry` e `AccountRegistry` governam o caminho crítico por tópico tipado e isolam políticas mínimas de MENSURA, MIA, PCS e perfil pessoal. Missões com identidade de agente sem `AgentRegistry`, ou com tópico incompatível, são negadas.
- `QuotaBudget` degrada autonomia em `NORMAL`, `WATCH`, `CONSERVE` e `CRITICAL`; em `CRITICAL` qualquer write é negado, inclusive L0. Reads continuam sujeitos ao teto de autonomia. `CircuitBreaker` abre para writes após a quantidade configurada de falhas mock `401`, `403`, `429` ou `timeout`.
- `CortexEventLog` aceita somente tipos allowlisted e trace IDs contratuais, mantém hash de payload e status sanitizado em memória, sem integração Córtex.
- Idempotência fecha somente em sucesso ou falha terminal mock `401`/`403`; `429` e `timeout` permanecem elegíveis para retry controlado sem duplicar sucesso.

Não há adapter real, transporte HTTP, navegador, OAuth, cookie, token, endpoint ou dependência de terceiros. A arquitetura não oferece ponto de injeção para transporte real; o teste estrutural em `tests/test_foundation.py` protege esse limite.

## Execução local

Requer Python 3.11 ou superior e nenhuma instalação adicional:

```bash
python -m unittest discover -v
```

## Regra de ouro

Nenhuma mudança persistente deve existir apenas no host do Leonard.  
Se mudou o sistema, a configuração versionável, a documentação, um schema, um teste ou uma política, a mudança deve terminar em Git com rastreabilidade.

## Estado de promoção

O ciclo de evidência é `IMPLEMENTED → REVIEWED → VALIDATED → PROMOTED`. `MERGED` é somente atributo Git e não substitui nenhuma etapa. Waves 00–03 permanecem `MERGED_WITH_FINDINGS` até a revisão do head final confirmar as correções; Wave 04 não deve ser promovida nem receber merge nesta fase.

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
