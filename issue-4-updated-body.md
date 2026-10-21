## Objetivo
Executar o LinkedIn Leonard por waves, mantendo `main` como estado canônico e sem writes reais antes de Policy, Approval, Audit/Trace, Gateway MOCK, verificação, credential gate e capability discovery.

## Waves
- [x] 00–03 Fundação local/mock-only (PR #2)
- [x] 04 Simulator e contratos locais (PR #5; head `ebbda69649bf2ac82d8406c10225ed7e03377339`; merge `cbcd18e44a6e9f3b0c4121a28301c1a41baf38b4`; CI final `36043751192` verde)
- [ ] 05 Credential/OAuth Gate
- [ ] 06 Capability Discovery
- [ ] 07 Member Connector
- [ ] 08 Organization Connector
- [ ] 09 Agentes operacionais
- [ ] 10 Approval/HITL real
- [ ] 11 Publisher
- [ ] 12 Analytics
- [ ] 13 Learning Loop
- [ ] 14 Eventos → Córtex
- [ ] 15 Writes reais, somente após autorização específica

## Estado de borda

```text
REAL_LINKEDIN_WRITE = DISABLED
OAUTH = NOT_CONFIGURED
WAVE_05 = AUTHORIZED_TO_START
```

`WAVE_05 = AUTHORIZED_TO_START` permite somente branch, implementação local/sintética, testes e revisão. Não autoriza app registration, segredo real, consentimento, token exchange, capability real ou ação no LinkedIn.

## Ordem obrigatória antes de qualquer permissão de escrita

```text
Secret reference
  ↓
Credential Broker
  ↓
OAuth state/PKCE
  ↓
Token lifecycle
  ↓
Scope allowlist
  ↓
Capability discovery
  ↓
READ-ONLY TEST
```

`w_member_social` e `w_organization_social` permanecem bloqueados até a cadeia read-only estar implementada e comprovada.

## Regra
Cada wave requer branch, testes, evidência, commit, PR, revisão independente e merge. OAuth real, tokens reais, scopes, app registration, qualquer gasto ou write LinkedIn ficam bloqueados até gate humano explícito.
