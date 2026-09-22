# LinkedIn Leonard

Sistema de Social Intelligence e operação de LinkedIn orquestrado por **Leonard — Agente Hermes**.

## Estado

- Status: bootstrap
- Owner operacional: Leonard / Hermes
- Repositório canônico: `mensuraeng/LinkedIn_Leonard`
- Branch canônica: `main`
- Governança: branch → testes → evidência → commit → PR → merge
- Ações públicas: sempre sujeitas a Policy Engine e Approval Gate conforme o PRD

## Documentos canônicos

- `docs/PRD.md` — requisitos completos do produto
- `docs/RUNBOOK.md` — implantação e rotina operacional do Leonard
- `AGENTS.md` — contrato dos agentes e regras de contribuição

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
