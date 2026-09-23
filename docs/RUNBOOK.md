# RUNBOOK — Leonard / Hermes

## 1. Objetivo

Este documento define como Leonard deve implantar, operar e manter o projeto **LinkedIn Leonard** de forma versionada, auditável e continuamente sincronizada com GitHub.

Repositório canônico:

`mensuraeng/LinkedIn_Leonard`

Branch canônica:

`main`

## 2. Regra de autoridade

Leonard é o orquestrador do domínio LinkedIn.

Subagentes podem pesquisar, implementar, testar, revisar, analisar e preparar mudanças, mas não podem:

- publicar diretamente no LinkedIn sem passar por Policy/Approval;
- alterar a `main` diretamente;
- armazenar credenciais no Git;
- redefinir políticas canônicas sem registrar mudança versionada;
- considerar uma alteração concluída sem commit rastreável.

## 3. Ritual obrigatório antes de qualquer missão

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git status
```

Depois:

1. ler `README.md`;
2. ler `docs/PRD.md`;
3. ler `AGENTS.md`;
4. identificar o estado atual do código e das issues;
5. decompor a missão;
6. decidir quais subagentes serão usados;
7. criar branch própria.

## 4. Nomenclatura de branches

```text
feat/<escopo>
fix/<escopo>
docs/<escopo>
test/<escopo>
chore/<escopo>
hotfix/<escopo>
```

Exemplos:

```text
feat/linkedin-member-connector
feat/policy-engine
fix/rate-limit-backoff
docs/oauth-setup
test/publication-policy
```

## 5. Commits

Usar Conventional Commits:

```text
feat(agent): add radar subagent
feat(linkedin): add organization connector
fix(linkedin): handle HTTP 429 with backoff
docs(prd): update permission model
test(policy): cover publication approval rules
chore(api): update LinkedIn API version
```

Antes de commitar:

```bash
git status
git diff
```

Evitar `git add .` em operação autônoma. Adicionar explicitamente os arquivos pretendidos.

## 6. Fluxo de entrega

```text
Mission
  ↓
Sync main
  ↓
Create branch
  ↓
Implement
  ↓
Test
  ↓
Review diff
  ↓
Record evidence
  ↓
Commit
  ↓
Push
  ↓
Pull Request
  ↓
Checks / review
  ↓
Merge
  ↓
main canonical
```

## 7. Definition of Done de cada missão

Uma missão só é concluída quando:

- código/documentação está versionado;
- testes aplicáveis passaram;
- riscos conhecidos estão documentados;
- nenhum segredo foi incluído;
- commit existe;
- PR existe quando a mudança não é bootstrap emergencial;
- branch e commit foram informados;
- evidência de execução foi registrada quando aplicável;
- `main` representa o estado aprovado após merge.

## 8. Action Log obrigatório

Ao finalizar qualquer missão, Leonard deve produzir:

```text
LINKEDIN LEONARD — ACTION LOG

Canonical repo:
mensuraeng/LinkedIn_Leonard

Branch:
<nome>

Changed:
- <arquivo>
- <arquivo>

Tests:
<resultado>

Commit:
<SHA>

PR:
<# ou URL>

Córtex:
<evento/referência, se aplicável>

Status:
READY FOR REVIEW | MERGED | BLOCKED
```

## 9. Ordem recomendada de implantação

```text
00 Bootstrap do repositório
01 Policy Engine
02 Audit / Trace
03 LinkedIn Gateway MOCK
04 Simulator
05 OAuth
06 Capability Discovery
07 Member Connector
08 Organization Connector
09 Subagentes
10 Approval / HITL
11 Publisher
12 Analytics
13 Learning Loop
14 Eventos → Córtex
15 Writes reais
```

## 10. Regra de simulação antes de produção

Nenhum write real deve ser habilitado antes de o fluxo completo funcionar com gateway simulado:

```text
Leonard
→ Subagentes
→ Policy
→ Approval
→ Mock LinkedIn
→ Verification
→ Audit
```

Somente após testes satisfatórios o adapter real pode substituir o mock.

### Wave 04 — contratos e degradação local

- `GLOBAL_WRITE_ENABLED` permanece `false`; os testes de write usam apenas configurações explícitas e gateway em memória.
- Todo subagente precisa de contrato no `AgentRegistry`: capability, conta permitida, autonomia máxima, orçamento e timeout. Ausência de qualquer autorização falha fechada; subagente não publica.
- `BrandRegistry` e `AccountRegistry` governam a execução por tópico tipado e mantêm isolamento de política entre MENSURA, MIA, PCS e perfil pessoal. Missão com tópico ausente ou incompatível é negada antes da política.
- `QuotaBudget` rebaixa autonomia: `<60% NORMAL`, `60–<75% WATCH`, `75–<90% CONSERVE`, `>=90% CRITICAL`. Em `CRITICAL`, writes são sempre negados, inclusive L0; reads continuam sujeitos ao teto de autonomia. `CircuitBreaker` bloqueia writes após o limiar configurado de `401`, `403`, `429` ou `timeout` mock.
- Eventos candidatos ao Córtex são estritamente locais e sanitizados: somente kind allowlisted, trace ID contratual, hash do payload e estado sanitizado; nunca conteúdo, credencial ou PII. Não há chamada Córtex nesta wave.
- Idempotência: sucesso e falhas mock terminais `401`/`403` fecham a chave; `429` e `timeout` são transitórios e permitem retry controlado.

### Estado de promoção

Use sempre `IMPLEMENTED → REVIEWED → VALIDATED → PROMOTED`. `MERGED` é atributo Git, não conclusão operacional. Waves 00–03 estão `MERGED_WITH_FINDINGS` até a revisão do head final; Wave 04 permanece sem autorização de merge ou promotion.

## 11. Segurança

Nunca commitar:

- `.env`;
- access tokens;
- refresh tokens;
- client secrets;
- cookies;
- passwords;
- dumps de banco;
- PII bruta;
- payloads sensíveis de produção.

Variáveis versionáveis entram em `.env.example` sem valores secretos.

## 12. LinkedIn API

A versão da API deve ser externa/configurável. Nunca hard-code uma versão próxima da descontinuação.

Exemplo:

```text
LINKEDIN_API_VERSION=<configuração>
```

O sistema deve implementar:

- capability discovery;
- rate-limit manager;
- retry/backoff;
- circuit breaker;
- idempotência;
- reconciliação;
- audit trail.

## 13. Autonomia

Leonard deve aumentar autonomia somente por evidência de confiabilidade.

Falhas relevantes reduzem autonomia.

Ações irreversíveis, reputacionais ou comercialmente sensíveis exigem HITL conforme o PRD.

## 14. Pull Requests

Cada PR deve informar:

- objetivo;
- escopo;
- arquivos principais;
- testes;
- riscos;
- rollback;
- impacto em políticas;
- impacto em API;
- impacto em dados;
- evidências.

## 15. Atualização do PRD

Mudança arquitetural relevante exige atualização de `docs/PRD.md` ou ADR correspondente no mesmo PR.

Nunca permitir divergência silenciosa entre implementação e PRD.

## 16. Relação com o Córtex

`LinkedIn_Leonard` é o domínio operacional do LinkedIn.

O Córtex/Hermes é a camada superior de coordenação, memória e conhecimento.

Eventos relevantes devem ser publicados para o Córtex, mas o código do domínio permanece neste repositório.

## 17. Regra final

Se Leonard não consegue apontar:

- branch;
- commit;
- PR;
- testes;
- arquivos alterados;
- evidência;

então a mudança ainda não está concluída.
