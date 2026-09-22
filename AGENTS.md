# AGENTS.md — LinkedIn Leonard

## Orquestrador

**Leonard / Agente Hermes** é o único orquestrador responsável pelo domínio.

## Subagentes previstos

- Radar
- Strategist
- Copywriter
- Creative Director
- Editor
- Brand Guardian
- Fact Checker
- Publisher
- Community Manager
- Lead Detector
- Analyst
- Experiment Manager
- Archivist
- API Guardian

## Contrato de execução

Subagentes:

1. recebem missão e contexto de Leonard;
2. executam apenas capabilities autorizadas;
3. retornam resultado estruturado;
4. não publicam diretamente;
5. não acessam segredos em texto puro;
6. não alteram `main` diretamente;
7. não redefinem políticas canônicas;
8. não consideram hipótese como aprendizado sem evidência.

## Tool boundary

Toda ação externa deve seguir:

```text
Subagente
→ Leonard
→ Policy Engine
→ Approval Gate
→ LinkedIn Gateway
→ Verification
→ Audit
```

## Regra de segurança

Nenhum agente recebe token bruto em prompt ou memória vetorial.

Use referências a credenciais gerenciadas externamente.

## Desenvolvimento

Toda alteração persistente deve:

- ocorrer em branch;
- ser testada;
- ser revisada;
- ser commitada;
- terminar em PR;
- atualizar documentação quando necessário.

## Fonte de verdade

- Produto: `docs/PRD.md`
- Operação: `docs/RUNBOOK.md`
- Código aprovado: `main`
