# PRD — LEONARD LINKEDIN CONTROL TOWER

**Versão:** 1.0  
**Status:** Especificação de produto; implementação local-only em promoção governada
**Owner:** Leonard — Agente Hermes  
**Plataforma-mãe:** Córtex  
**Domínio:** Social Intelligence / LinkedIn Operations  
**Data-base:** 22/09/2026

---

## 1. VISÃO EXECUTIVA

O **Leonard LinkedIn Control Tower** será o sistema central de inteligência, operação, monitoramento e governança das contas de LinkedIn administradas pelo usuário.

Leonard, como instância do **Agente Hermes**, será o agente orquestrador e único responsável pela coordenação do sistema.

Leonard não deverá executar diretamente todas as tarefas. Ele deverá decompor objetivos em missões e acionar subagentes especializados para:

- pesquisa;
- inteligência de mercado;
- planejamento editorial;
- produção de conteúdo;
- revisão;
- compliance;
- publicação;
- gestão de comentários;
- análise de performance;
- identificação de oportunidades;
- aprendizagem;
- manutenção operacional.

O sistema será multi-conta e multi-marca.

Escopo inicial recomendado:

- Perfil pessoal do executivo;
- MENSURA Engenharia;
- MIA Engenharia;
- PCS Engenharia;
- futuras empresas, marcas ou unidades cadastradas.

O objetivo não é criar um simples agendador de posts.

O produto será uma **Social Intelligence & Operations Layer conectada ao Córtex**.

---

## 2. PROBLEMA

A operação profissional de LinkedIn normalmente fica fragmentada entre:

- criação de conteúdo;
- revisão;
- design;
- publicação;
- monitoramento;
- resposta a comentários;
- acompanhamento de leads;
- analytics;
- calendário editorial;
- memória do que já foi publicado;
- aprendizado sobre desempenho.

Essa fragmentação produz quatro problemas principais.

### P1. Ausência de inteligência acumulada

Cada publicação tende a ser tratada como evento isolado.

Não existe necessariamente uma memória estruturada relacionando:

`tema → audiência → formato → horário → reação → perfil de quem interagiu → oportunidade comercial`

### P2. Execução dependente de pessoas

Pesquisa, conteúdo, publicação e análise dependem de tarefas manuais recorrentes.

### P3. Falta de coordenação entre marcas

Perfil pessoal e páginas empresariais possuem posicionamentos diferentes, mas frequentemente tratam assuntos relacionados.

Sem coordenação, surge:

- repetição;
- canibalização;
- conflitos de posicionamento;
- oportunidades perdidas de distribuição.

### P4. Métricas sem fechamento de ciclo

Impressões ou curtidas isoladamente não indicam geração de valor.

O sistema deve conectar:

`conteúdo → audiência alcançada → interação → conversa → oportunidade`

---

## 3. OBJETIVO DO PRODUTO

Construir uma camada autônoma de operação de LinkedIn comandada por Leonard capaz de executar continuamente o ciclo:

**OBSERVAR → ENTENDER → PLANEJAR → PRODUZIR → VALIDAR → PUBLICAR → INTERAGIR → MEDIR → APRENDER**

Leonard deverá manter visão global de todas as contas.

---

## 4. NORTH STAR

A métrica principal não será volume de posts.

Será:

> **Quantidade e qualidade de interações relevantes produzidas pela presença digital entre os públicos estratégicos definidos para cada marca.**

Exemplos:

- sócios;
- CEOs;
- diretores;
- arquitetos;
- investidores;
- incorporadores;
- gestores de engenharia;
- potenciais clientes;
- parceiros estratégicos.

---

## 5. PRINCÍPIOS OPERACIONAIS

### 5.1 Leonard é o comandante

Subagentes não comandam outros agentes sem autorização explícita de Leonard.

Fluxo:

```text
Usuário
   ↓
Leonard / Hermes
   ↓
Planner
   ↓
Subagentes
   ↓
Resultados
   ↓
Leonard
   ↓
Validação / decisão
   ↓
Execução
```

---

## 6. PRINCÍPIO DE AUTONOMIA

Aplicar a lógica:

> **Máquina age; humano atua por exceção.**

Porém, a autonomia será proporcional à reversibilidade da ação.

Quanto maior o risco reputacional ou dificuldade de reversão, menor a autonomia.

---

## 7. NÍVEIS DE AUTONOMIA

### L0 — OBSERVAÇÃO

Permitido automaticamente:

- coletar analytics;
- monitorar performance;
- identificar comentários;
- identificar tendências;
- analisar concorrentes;
- organizar dados.

Nenhuma ação pública.

### L1 — RECOMENDAÇÃO

O agente pode:

- sugerir resposta;
- sugerir post;
- sugerir pauta;
- sugerir interação.

Não executa.

### L2 — APROVAÇÃO HUMANA

Leonard prepara a ação.

Usuário aprova.

Leonard executa.

Aplicável inicialmente a:

- novos posts;
- respostas públicas;
- reposts;
- mensagens;
- mudanças editoriais relevantes.

### L3 — AUTOMAÇÃO CONTROLADA

Leonard pode executar automaticamente ações previamente autorizadas.

Exemplo:

```text
Post aprovado
↓
Agendamento autorizado
↓
Leonard publica automaticamente no horário
```

### L4 — AUTONOMIA TOTAL LIMITADA

Permitida apenas para tarefas:

- reversíveis;
- previsíveis;
- de risco baixo;
- claramente definidas por política.

Exemplo:

- coleta de analytics;
- geração de relatórios;
- atualização do calendário;
- classificação de comentários;
- identificação de leads.

---

## 8. AÇÕES QUE NUNCA DEVEM SER TOTALMENTE AUTÔNOMAS

Inicialmente:

- envio de mensagem comercial fria;
- convite de conexão;
- publicação sobre crise;
- posicionamento político;
- resposta jurídica;
- resposta agressiva;
- exclusão de conteúdo;
- bloqueio de usuário;
- mudanças de credenciais;
- alteração de administradores;
- publicação relacionada a informação confidencial.

---

## 9. FATOS TÉCNICOS VERIFICADOS

O LinkedIn diferencia permissões para pessoas e organizações.

A Posts API usa, entre outras:

- `w_member_social`: criar posts, comentários e likes em nome do usuário autenticado;
- `w_organization_social`: executar essas ações em nome de uma organização;
- `r_organization_social`: leitura de posts, comentários e likes de organizações;
- `r_member_social`: leitura de conteúdo de membro, mas atualmente é uma permissão restrita.

Fonte:  
https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2025-07

O LinkedIn informa que `r_member_social` está fechado para novas solicitações atualmente.

Fonte:  
https://learn.microsoft.com/en-us/linkedin/marketing/community-management/community-management-overview?view=li-lms-2026-06

Portanto:

> O sistema não poderá assumir que terá a mesma capacidade de leitura no perfil pessoal que possui nas páginas corporativas.

Essa diferença deverá fazer parte do desenho arquitetural.

---

## 10. COMMUNITY MANAGEMENT API

Para páginas empresariais, utilizar prioritariamente a **Community Management API oficial**.

Ela permite gerenciar páginas, atividades sociais e analytics, de acordo com as permissões concedidas.

Fonte:  
https://learn.microsoft.com/en-us/linkedin/marketing/community-management/community-management-overview?view=li-lms-2026-06

Existem dois níveis:

### Development Tier

Para desenvolvimento e testes.

A documentação atual informa limites padrão de:

- 500 requests/app;
- 100 requests/member.

Esses valores são específicos do Development Tier descrito pela documentação atual e podem ser alterados pelo LinkedIn.

### Standard Tier

Destinado a produção.

O upgrade exige solicitação específica e demonstração da aplicação, incluindo screen recording dos casos de uso.

---

## 11. ALERTA DE VERSIONAMENTO P0

A documentação atual alerta que a Marketing API `202510` será descontinuada em:

**15 de outubro de 2026.**

Portanto é proibido:

```text
LINKEDIN_VERSION=202510
```

hard-coded na aplicação.

Criar:

```text
LINKEDIN_API_VERSION
```

como configuração externa.

Além disso:

```text
API Version Monitor
        ↓
Detecta nova versão
        ↓
Executa compatibility tests
        ↓
Abre migration task
        ↓
Leonard recebe alerta
```

---

## 12. ARQUITETURA GERAL

```text
                         USUÁRIO
                            │
                            ▼
                    ┌───────────────┐
                    │    LEONARD    │
                    │ Hermes Agent  │
                    └───────┬───────┘
                            │
              ORCHESTRATION / GOVERNANCE
                            │
        ┌───────────────────┼──────────────────┐
        │                   │                  │
        ▼                   ▼                  ▼
   STRATEGY             OPERATIONS         INTELLIGENCE
        │                   │                  │
        ▼                   ▼                  ▼
 Subagentes           Subagentes          Subagentes
        │                   │                  │
        └───────────────────┬──────────────────┘
                            │
                         POLICY
                          ENGINE
                            │
                     APPROVAL GATE
                            │
                            ▼
                    LINKEDIN GATEWAY
                   ┌────────┴────────┐
                   │                 │
             Member API       Organization API
                   │                 │
                   ▼                 ▼
             Perfil pessoal      Company Pages
                            │
                            ▼
                         EVENTS
                            │
                            ▼
                       PostgreSQL
                         pgvector
                            │
                ┌───────────┴──────────┐
                ▼                      ▼
             CÓRTEX                  BI
```

---

## 13. AGENTE PRINCIPAL — LEONARD

**Código:** `AGENT-LNK-000`  
**Tipo:** Orquestrador.

### Responsabilidade

Leonard deverá:

1. receber objetivos;
2. interpretar contexto;
3. identificar conta/marca;
4. decompor tarefa;
5. definir subagentes;
6. controlar sequência;
7. controlar custos;
8. controlar API quota;
9. controlar risco;
10. consolidar outputs;
11. decidir necessidade de HITL;
12. solicitar aprovação;
13. executar ações aprovadas;
14. verificar resultado;
15. registrar auditoria;
16. atualizar memória;
17. gerar aprendizado.

---

## 14. SUBAGENTES

### AGENT-LNK-101 — RADAR

**Função:** Social Listening / Research.

Analisa:

- tendências;
- notícias;
- concorrentes;
- temas emergentes;
- conteúdo relevante;
- oportunidades editoriais.

Output:

```json
{
  "topic": "",
  "reason": "",
  "audience": "",
  "timing": "",
  "evidence": [],
  "recommended_action": ""
}
```

### AGENT-LNK-102 — STRATEGIST

Responsável pela estratégia editorial.

Entrada:

- dados do Radar;
- objetivos comerciais;
- histórico;
- performance;
- posicionamento da marca.

Produz:

- tese editorial;
- campanha;
- pauta;
- target audience;
- CTA;
- canal;
- formato.

### AGENT-LNK-103 — COPYWRITER

Produz:

- posts;
- artigos;
- respostas;
- títulos;
- comentários;
- hooks;
- CTAs.

Não publica.

### AGENT-LNK-104 — CREATIVE DIRECTOR

Transforma conteúdo em briefing visual.

Responsável por:

- direção de arte;
- formato;
- imagem;
- carrossel;
- vídeo;
- document post;
- consistência visual.

Poderá acionar ferramentas de geração de imagem quando disponíveis.

### AGENT-LNK-105 — EDITOR

Revisa:

- clareza;
- estrutura;
- redundância;
- tom;
- força do argumento;
- adequação ao público;
- potencial de interpretação equivocada.

Deve executar até três ciclos internos de revisão quando configurado.

### AGENT-LNK-106 — BRAND GUARDIAN

Verifica aderência ao Brand System.

Cada marca possuirá:

```text
BrandProfile
Tone
Audience
ForbiddenClaims
PreferredClaims
VisualGuidelines
CTAStyle
RiskRules
```

Não deverá permitir que o posicionamento de uma marca contamine outra.

### AGENT-LNK-107 — FACT CHECKER

Classifica cada afirmação relevante:

```text
VERIFIED
SUPPORTED
UNCERTAIN
OPINION
HYPOTHESIS
PROHIBITED
```

Para dados quantitativos:

```text
claim
source
source_date
confidence
expiry_date
```

### AGENT-LNK-108 — PUBLISHER

Único subagente autorizado a solicitar publicação.

Fluxo obrigatório:

```text
Content
↓
Editor
↓
Brand Guardian
↓
Fact Checker
↓
Policy Engine
↓
Approval
↓
Publisher
```

Publisher jamais poderá pular gates.

### AGENT-LNK-109 — COMMUNITY MANAGER

Responsável por:

- comentários;
- menções;
- dúvidas;
- classificação das interações;
- identificação de oportunidade;
- preparação de respostas.

Classificações:

```text
POSITIVE
NEUTRAL
QUESTION
LEAD
CUSTOMER
PARTNER
CRITICISM
COMPLAINT
SPAM
RISK
```

### AGENT-LNK-110 — LEAD DETECTOR

Analisa interações comerciais.

Exemplo:

```text
Diretor de Engenharia
↓
comentou em post sobre atraso
↓
empresa compatível com ICP
↓
score comercial elevado
```

Output:

```json
{
  "person": "",
  "company": "",
  "signal": "",
  "source": "",
  "intent_score": 0,
  "recommended_action": ""
}
```

Não deverá enviar mensagem automaticamente no MVP.

### AGENT-LNK-111 — ANALYST

Responsável por analytics.

Analisa:

- alcance;
- impressões;
- engagement;
- follower growth;
- comentários;
- perfil das interações;
- conteúdo;
- formato;
- horário;
- tema;
- CTA.

Não utilizar apenas métricas de vaidade.

### AGENT-LNK-112 — EXPERIMENT MANAGER

Opera experimentos editoriais.

Exemplo:

```text
Hipótese:
posts baseados em erros reais de obra
geram mais compartilhamentos entre decisores.

Teste:
A vs B

Janela:
30 dias

KPI:
qualified engagement rate
```

### AGENT-LNK-113 — ARCHIVIST

Mantém memória editorial.

Responsável por evitar:

- temas duplicados;
- exemplos repetidos;
- estatísticas antigas;
- afirmações conflitantes.

### AGENT-LNK-114 — API GUARDIAN

Responsável por:

- quotas;
- tokens;
- erros;
- expiração;
- retry;
- backoff;
- versão da API;
- disponibilidade.

O LinkedIn utiliza limites por aplicação e por membro, que são contabilizados em janelas diárias e retornam HTTP `429` quando excedidos. Os limites específicos variam por endpoint.

Fonte:  
https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/rate-limits

---

## 28. ACCOUNT REGISTRY

Criar entidade:

`LinkedInEntity`

Tipos:

```text
PERSON
ORGANIZATION
```

Campos:

```text
id
brand_id
linkedin_urn
entity_type
display_name
status
permissions
oauth_connection
autonomy_level
posting_policy
engagement_policy
risk_profile
```

---

## 29. BRAND REGISTRY

```text
Brand
├─ positioning
├─ audience
├─ voice
├─ claims
├─ forbidden_claims
├─ CTA
├─ content_pillars
├─ visual_identity
└─ commercial_objectives
```

---

## 30. ARQUITETURA TÉCNICA RECOMENDADA

### Orquestração

- Leonard/Hermes;
- n8n para workflows determinísticos;
- agentes IA para raciocínio.

### Backend

- Node.js/TypeScript ou Python;
- API Gateway interno.

### Banco

PostgreSQL.

### Memória semântica

pgvector.

### Fila

Redis/BullMQ, RabbitMQ ou equivalente.

### Dashboard

Next.js/React.

### BI

Power BI ou dashboard Córtex.

### Storage

Object Storage / SharePoint quando adequado.

---

## 31. PRINCÍPIO ARQUITETURAL

Agente não deve acessar LinkedIn diretamente.

Sempre:

```text
Agent
↓
Leonard
↓
Policy Engine
↓
LinkedIn Gateway
↓
API
```

---

## 32. LINKEDIN GATEWAY

Interface única:

```text
linkedin.publish()
linkedin.comment()
linkedin.reply()
linkedin.react()
linkedin.getPosts()
linkedin.getComments()
linkedin.getAnalytics()
linkedin.getOrganizations()
linkedin.uploadImage()
linkedin.uploadVideo()
linkedin.uploadDocument()
```

Cada chamada gera `ToolCallEvent`.

---

## 33. MCP LAYER

As MCPs estudadas deverão ser tratadas como:

> **reference implementations / adapters**

e não como núcleo de governança.

Estrutura:

```text
linkedin-mcp-member
linkedin-mcp-pages
        ↓
Connector Adapter
        ↓
LinkedIn Gateway
```

Isso evita acoplamento irreversível a uma repo externa.

---

## 34. CONTEÚDO SUPORTADO

A Posts API atual documenta suporte orgânico para:

- texto;
- imagem;
- vídeo;
- documentos;
- artigo;
- múltiplas imagens;
- polls;
- celebration.

O carousel orgânico não está disponível pela Posts API atual; carousel aparece como formato patrocinado.

Fonte:  
https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2025-07

Portanto não definir “carousel” e “document post” como sinônimos na camada técnica.

---

## 35. CONTENT OBJECT

```json
{
  "content_id": "",
  "brand_id": "",
  "author_entity": "",
  "campaign_id": "",
  "content_type": "",
  "topic": "",
  "audience": [],
  "objective": "",
  "hook": "",
  "body": "",
  "cta": "",
  "assets": [],
  "sources": [],
  "status": "",
  "risk_score": 0,
  "approval_status": "",
  "scheduled_at": null
}
```

---

## 36. ESTADOS DO CONTEÚDO

```text
IDEA
↓
RESEARCH
↓
DRAFT
↓
EDITORIAL_REVIEW
↓
FACT_CHECK
↓
BRAND_REVIEW
↓
READY
↓
APPROVAL_REQUIRED
↓
APPROVED
↓
SCHEDULED
↓
PUBLISHED
↓
MONITORING
↓
ANALYZED
↓
ARCHIVED
```

---

## 37. APPROVAL ENGINE

Cada ação possui:

```text
risk_score
reversibility_score
brand_sensitivity
public_visibility
financial_impact
reputation_impact
```

Resultado:

```text
AUTO
AUTO_WITH_LOG
HUMAN_APPROVAL
BLOCK
```

---

## 38. EXEMPLO

Post institucional normal:

```text
risk = 22
→ HUMAN_APPROVAL
```

Analytics:

```text
risk = 2
→ AUTO
```

Responder:

> Obrigado pelo comentário.

```text
risk = 8
→ AUTO futuramente
```

Responder crítica de cliente:

```text
risk = 80
→ HUMAN_APPROVAL
```

---

## 39. KILL SWITCH

Leonard deverá possuir:

```text
GLOBAL_WRITE_ENABLED=false
```

Esse comando bloqueia imediatamente:

- publicação;
- comentário;
- reaction;
- resposta;
- mensagens.

Leitura permanece ativa.

---

## 40. CIRCUIT BREAKER

Desativar automaticamente writes caso ocorram:

- múltiplos 401;
- múltiplos 403;
- excesso de 429;
- comportamento inesperado;
- falhas de validação;
- publicação divergente do conteúdo aprovado.

---

## 41. RATE LIMIT MANAGER

O LinkedIn informa que existem limites:

- por aplicação;
- por membro.

Os limites padrão por endpoint não são publicados de maneira universal; devem ser consultados no Developer Portal para o app específico.

Fonte:  
https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/rate-limits

Criar:

`QuotaBudget`

Campos:

```text
endpoint
daily_limit
used
reserved
remaining
reset_at
```

Política:

```text
< 60% → NORMAL
60–75% → WATCH
75–90% → CONSERVE
>90% → CRITICAL
```

---

## 42. WORKFLOW — CRIAÇÃO DE CONTEÚDO

```text
Leonard
   ↓
Radar
   ↓
Strategist
   ↓
Copywriter
   ↓
Creative Director
   ↓
Editor
   ↓
Fact Checker
   ↓
Brand Guardian
   ↓
Policy Engine
   ↓
Usuário
   ↓
Publisher
```

---

## 43. WORKFLOW — COMENTÁRIOS

```text
Novo comentário
↓
Community Manager
↓
Classificação
↓
Lead Detector
↓
Risk Score
↓
Resposta sugerida
↓
Policy
↓
Auto / Approval
```

---

## 44. WORKFLOW — LEAD SIGNAL

```text
Interaction
↓
Identity enrichment
↓
ICP comparison
↓
Intent scoring
↓
Lead Signal
↓
Leonard
↓
CRM / alerta
```

---

## 45. WORKFLOW — APRENDIZADO

Após determinado período:

```text
Post
↓
Metrics Snapshot
↓
Audience Quality
↓
Business Signals
↓
Analyst
↓
Experiment Manager
↓
Learning
↓
Strategy Memory
```

---

## 46. CONTENT KNOWLEDGE GRAPH

Criar relações:

```text
POST
 ├─ ABOUT → TOPIC
 ├─ TARGETS → AUDIENCE
 ├─ BELONGS_TO → BRAND
 ├─ GENERATED → COMMENT
 ├─ GENERATED → LEAD
 ├─ USED → FORMAT
 ├─ USED → CTA
 └─ ACHIEVED → METRIC
```

Posteriormente isso poderá ser visualizado dentro do Córtex.

---

## 47. MODELO DE DADOS

Tabelas principais:

```text
brands
linkedin_entities
linkedin_credentials_refs
linkedin_permissions

content_items
content_versions
content_assets
content_sources
content_campaigns

publications
comments
reactions
interactions

profiles
companies
lead_signals

metric_snapshots
experiments
learnings

approvals
policies
policy_decisions

agent_runs
agent_tasks
tool_calls

api_quota
api_errors
alerts

audit_events
```

---

## 48. AUDIT LOG

Toda ação deve registrar:

```json
{
  "timestamp": "",
  "actor": "",
  "agent": "",
  "account": "",
  "action": "",
  "reason": "",
  "input": "",
  "output": "",
  "approval_id": "",
  "tool": "",
  "api_response": "",
  "trace_id": ""
}
```

---

## 49. TRACE ID

Toda missão iniciada por Leonard deverá receber:

```text
TRACE-LNK-YYYYMMDD-XXXX
```

Permitindo seguir:

```text
pedido
→ agentes
→ ferramentas
→ aprovação
→ publicação
→ resultado
```

---

## 50. OBSERVABILIDADE

Dashboard operacional:

### Agent Health

- success rate;
- failure rate;
- tempo;
- custo;
- retries.

### LinkedIn Health

- token;
- API status;
- quota;
- erros.

### Content Operations

- draft;
- approval;
- scheduled;
- published;
- failed.

### Community

- comentários pendentes;
- leads;
- riscos.

---

## 51. DASHBOARD EXECUTIVO

Tela principal:

```text
LINKEDIN CONTROL TOWER
────────────────────────

Accounts Online       4/4

Posts this week       7

Pending approvals     3

Qualified comments    12

Potential leads       4

Risk alerts           0

API health            OK
```

---

## 52. KPIs OPERACIONAIS

- % de publicação bem-sucedida;
- erro API;
- latência média;
- conteúdo pendente;
- tempo de aprovação;
- comentários sem classificação;
- comentários sem resposta;
- disponibilidade do conector.

---

## 53. KPIs EDITORIAIS

- impressions;
- reach;
- engagement;
- comments;
- shares;
- saves quando disponível;
- follower growth;
- profile/page visits quando disponível.

---

## 54. KPIs DE QUALIDADE

Criar:

### Qualified Engagement Rate

```text
interações ICP
──────────────
total de interações
```

---

## 55. KPI COMERCIAL

### Social Influence Pipeline

Quantidade de oportunidades comerciais que tiveram pelo menos um sinal identificável originado ou influenciado pelo LinkedIn.

Não atribuir causalidade automática.

Classificar:

```text
SOURCE
ASSIST
INFLUENCE
UNKNOWN
```

---

## 56. CONTENT PERFORMANCE SCORE

Não usar score absoluto para tomada de decisão sem contexto.

Modelo interno possível:

```text
30% audience quality
25% comments quality
15% sharing
10% engagement
10% profile activity
10% commercial signals
```

Pesos deverão ser calibrados empiricamente.

---

## 57. BRAND-SPECIFIC STRATEGY

Cada conta possuirá estratégia independente.

Exemplo estrutural:

```text
Perfil pessoal
→ autoridade do executivo

MENSURA
→ gestão, governança e engenharia

MIA
→ construção premium e pré-construção

PCS
→ retrofit, patrimônio e engenharia especializada
```

Leonard deverá coordenar sem homogeneizar as marcas.

---

## 58. CROSS-BRAND INTELLIGENCE

Leonard poderá detectar:

```text
tema performou bem no perfil pessoal
        ↓
é relevante institucionalmente?
        ↓
SIM
        ↓
criar abordagem diferente para empresa
```

Jamais duplicar texto literalmente como regra padrão.

---

## 59. CALENDÁRIO EDITORIAL

Entidade:

`EditorialCalendar`

Campos:

```text
date
brand
platform
content
campaign
status
owner
approval
publication
```

Leonard deverá detectar:

- conflitos;
- excesso de publicação;
- lacunas;
- repetição.

---

## 60. COMANDOS DO LEONARD

Exemplos:

```text
/leonard status
```

```text
/leonard linkedin today
```

```text
/leonard prepare-week
```

```text
/leonard approvals
```

```text
/leonard leads
```

```text
/leonard performance 30d
```

```text
/leonard company mensura
```

```text
/leonard investigate topic
```

```text
/leonard pause
```

---

## 61. PROMPT CENTRAL DE LEONARD

Conceito:

> Você é Leonard, agente Hermes responsável pela operação do ecossistema LinkedIn. Seu trabalho não é produzir conteúdo diretamente quando um subagente especializado puder realizá-lo melhor. Você deve decompor objetivos, selecionar agentes, fornecer contexto mínimo necessário, validar resultados, aplicar políticas, solicitar aprovação quando exigido, executar ações autorizadas, monitorar resultado e registrar aprendizado no Córtex.

Regra central:

> Nenhuma ação pública ocorre sem passar pelo Policy Engine.

---

## 62. MEMÓRIA

Três níveis.

### Working Memory

Missão atual.

### Operational Memory

Últimos dias/semanas.

### Strategic Memory

Aprendizados permanentes.

---

## 63. MEMÓRIA EVIDENCIAL

Separar:

```text
FACT
ANALYSIS
HYPOTHESIS
EXPERIMENT
LEARNING
```

Não transformar automaticamente hipótese em aprendizado.

---

## 64. LEARNING OBJECT

```json
{
  "observation": "",
  "hypothesis": "",
  "evidence": [],
  "confidence": 0,
  "brand": "",
  "valid_until": "",
  "recommended_change": ""
}
```

---

## 65. SEGURANÇA — CREDENCIAIS

Proibido armazenar tokens em:

- prompts;
- logs;
- pgvector;
- Git;
- banco em texto puro.

Utilizar Secret Manager.

Agentes recebem apenas:

```text
credential_reference
```

---

## 66. RBAC

Papéis internos:

```text
OWNER
APPROVER
EDITOR
ANALYST
VIEWER
AGENT
```

---

## 67. PERMISSÕES DO LINKEDIN

Para organizações, as permissões dependem também do papel do usuário na página.

A documentação atual registra, por exemplo:

- `ADMINISTRATOR`;
- `DIRECT_SPONSORED_CONTENT_POSTER`;
- `ANALYST`;
- `CURATOR`;
- `CONTENT_ADMINISTRATOR`.

Certas operações administrativas exigem papel apropriado, e `rw_organization_admin` é usado para administração e reporting conforme a documentação aplicável.

Fonte:  
https://learn.microsoft.com/en-us/linkedin/marketing/community-management/organizations/organization-access-control-by-role?view=li-lms-2025-07

---

## 68. PRIVACIDADE

Minimizar armazenamento de dados pessoais.

Armazenar apenas o necessário para:

- operação;
- analytics;
- relacionamento legítimo;
- auditoria.

Definir políticas de retenção.

---

## 69. AÇÕES NÃO OFICIAIS

Automação via cookie/browser ou APIs não oficiais deverá ser isolada.

Nunca integrar essas ações diretamente ao core.

Arquitetura:

```text
Official API Gateway
        │
        ├── PRIMARY
        │
Unofficial Adapter
        │
        └── DISABLED BY DEFAULT
```

---

## 70. FEATURE FLAGS

Exemplos:

```text
ENABLE_PERSONAL_POSTING
ENABLE_COMPANY_POSTING

ENABLE_AUTO_REPLY
ENABLE_CONNECTION_REQUESTS
ENABLE_DIRECT_MESSAGES

ENABLE_UNOFFICIAL_API=false
```

---

## 71. FAILSAFE

Em dúvida:

```text
DO NOT ACT
↓
create approval request
↓
notify Leonard
```

---

## 72. SLOS

### API Gateway

Disponibilidade alvo:

`≥ 99,5%`

### Publication

Posts aprovados enviados:

`≥ 99%`

excluindo indisponibilidade externa do LinkedIn.

### Auditability

Ações públicas com trace:

`100%`

### Human Approval

Ações classificadas como críticas publicadas sem aprovação:

`0`

---

## 73. ALERTAS

### P0

- publicação não autorizada;
- vazamento de credencial;
- conta comprometida.

### P1

- token expirado;
- múltiplos 401/403;
- publicação divergente.

### P2

- quota >75%;
- fila atrasada;
- analytics sem atualização.

### P3

- queda de performance;
- calendário vazio.

---

## 74. RELATÓRIO DIÁRIO DE LEONARD

Leonard deverá produzir resumo:

```text
LinkedIn Daily

Publicados: 2
Agendados: 3
Aprovação: 2

Comentários: 21
Qualificados: 5

Lead signals: 2

Alertas: 0

API: Healthy
```

---

## 75. RELATÓRIO SEMANAL

```text
1. Conteúdo publicado
2. Performance
3. Audiência
4. Interações qualificadas
5. Leads
6. Hipóteses
7. Experimentos
8. Alertas
9. Próxima semana
```

---

## 76. RELATÓRIO MENSAL

Leonard deverá consolidar:

### O que funcionou

### O que não funcionou

### O que aprendemos

### O que ainda não sabemos

### O que devemos testar

---

## 77. IMPLEMENTAÇÃO — FASE 0

### Governança

Criar:

- repo;
- arquitetura;
- secrets;
- banco;
- RBAC;
- audit schema;
- brand registry.

Saída:

**Core operacional sem LinkedIn.**

---

## 78. FASE 1 — LINKEDIN APP

Criar Developer App.

Configurar OAuth.

Solicitar produtos necessários.

Validar:

- identidade;
- páginas;
- permissões;
- organization ACL.

O LinkedIn recomenda validar as páginas às quais o membro autenticado possui acesso por meio de `/organizationAcls`.

Fonte:  
https://learn.microsoft.com/en-us/linkedin/marketing/quick-start?view=li-lms-2026-07

---

## 79. FASE 2 — MEMBER CONNECTOR

Implementar:

```text
authenticate
create post
upload assets
publish
```

Priorizar API oficial.

---

## 80. FASE 3 — ORGANIZATION CONNECTOR

Implementar:

- organizations;
- posts;
- comments;
- reactions;
- analytics.

---

## 81. FASE 4 — LEONARD CORE

Implementar:

```text
Mission Router
Agent Registry
Task Planner
Policy Engine
Approval Engine
Audit
Memory
```

---

## 82. FASE 5 — CONTENT AGENTS

Implementar:

- Radar;
- Strategist;
- Copywriter;
- Editor;
- Fact Checker;
- Brand Guardian.

---

## 83. FASE 6 — PUBLICATION PIPELINE

Implementar:

```text
Draft
→ Review
→ Approval
→ Schedule
→ Publish
→ Verify
```

---

## 84. FASE 7 — COMMUNITY

Implementar:

- ingestão de comentários;
- classificação;
- respostas;
- lead signals.

---

## 85. FASE 8 — ANALYTICS

Implementar:

- snapshots;
- dashboard;
- comparisons;
- trends.

---

## 86. FASE 9 — LEARNING LOOP

Implementar:

```text
Experiment
→ Measurement
→ Analysis
→ Learning
→ Strategy update
```

---

## 87. FASE 10 — CÓRTEX

Eventos enviados ao Córtex:

```text
ContentCreated
ContentApproved
ContentPublished

CommentReceived
LeadSignalDetected

ExperimentCompleted
LearningCreated

RiskDetected
ApiFailure
```

---

## 88. EVENT ENVELOPE

```json
{
  "event_id": "",
  "event_type": "",
  "timestamp": "",
  "source": "linkedin-control-tower",
  "brand": "",
  "entity": "",
  "trace_id": "",
  "payload": {}
}
```

---

## 89. MVP

O MVP estará pronto quando Leonard conseguir:

1. identificar a conta;
2. criar missão;
3. acionar subagentes;
4. produzir conteúdo;
5. revisar;
6. validar;
7. solicitar aprovação;
8. publicar;
9. confirmar publicação;
10. registrar auditoria;
11. coletar métricas;
12. gerar relatório.

---

## 90. FORA DO MVP

Inicialmente fora:

- envio autônomo de DMs;
- conexão automática;
- scraping em escala;
- browser automation agressiva;
- campanhas pagas;
- recrutamento;
- Sales Navigator automation.

---

## 91. TESTES

### Unit

Cada adapter.

### Integration

LinkedIn Sandbox/Test environment quando disponível.

### Contract

Schemas da API.

### Agent Tests

Prompt/evals.

### Policy Tests

Ações proibidas.

### Security

Secrets / authorization.

### Chaos Tests

- 401;
- 403;
- 429;
- timeout;
- LinkedIn down;
- token expirado.

---

## 92. EVALS DOS AGENTES

Criar datasets gold-standard.

Avaliar:

```text
relevance
brand alignment
factuality
risk detection
tool selection
approval decision
```

---

## 93. ACCEPTANCE CRITERIA — LEONARD

Leonard passa quando:

- identifica corretamente marca >99%;
- roteia corretamente agente >95%;
- não publica sem gate;
- registra 100% das ações externas;
- detecta falha de agente;
- consegue repetir ação idempotente sem duplicação.

---

## 94. IDEMPOTÊNCIA

Toda publicação:

```text
idempotency_key
```

Antes de executar:

```text
já publicado?
YES → abort
NO → execute
```

Evita posts duplicados.

---

## 95. RECONCILIAÇÃO

A cada ciclo:

```text
DB
vs
LinkedIn
```

Detectar:

- post faltando;
- post duplicado;
- status divergente;
- analytics atrasado.

---

## 96. CONTROL PLANE

Separar:

### Data Plane

Executa operações.

### Control Plane

Leonard controla:

- autonomia;
- políticas;
- agentes;
- contas;
- quota;
- feature flags.

---

## 97. INTERFACE DE CONTROLE

Página:

### Leonard Control

```text
SYSTEM           ONLINE

Autonomy         L2

Public posting   ENABLED
Auto replies     DISABLED
DM               DISABLED
Connections      DISABLED

API              HEALTHY

Emergency Stop   [ STOP ALL WRITES ]
```

---

## 98. AGENT REGISTRY

```text
Agent
Capabilities
AllowedTools
AllowedAccounts
MaxAutonomy
Model
Budget
Timeout
Status
```

Leonard não poderá enviar tarefa a agente sem capability cadastrada.

---

## 99. COST GOVERNANCE

Registrar por missão:

```text
tokens
API calls
image generations
external tools
compute
```

Criar custo por:

- post;
- campanha;
- marca;
- agente.

---

## 100. DEFINITION OF DONE

O sistema será considerado implantado quando:

### Tecnologia

- API oficial conectada;
- OAuth funcionando;
- banco funcionando;
- filas funcionando;
- observabilidade funcionando.

### Agentes

- Leonard operacional;
- subagentes registrados;
- políticas aplicadas.

### Governança

- approval engine;
- kill switch;
- audit log;
- RBAC.

### Operação

- conteúdo publicado;
- comentários monitorados;
- analytics coletados;
- relatório gerado.

### Aprendizado

- métricas relacionadas aos conteúdos;
- experimentos armazenados;
- learnings persistidos.

---

## 101. ROADMAP DE AUTONOMIA

### Etapa A

```text
L1
AI recomenda.
Humano executa.
```

### Etapa B

```text
L2
AI prepara.
Humano aprova.
AI executa.
```

### Etapa C

```text
L3
AI executa ações previamente autorizadas.
```

### Etapa D

```text
L4
AI opera tarefas de baixo risco por exceção.
```

Subir nível apenas após dados de confiabilidade.

---

## 102. MÉTRICA DE CONFIABILIDADE

Criar:

### Agent Reliability Score

Baseado em:

```text
task success
human correction
policy violation
tool error
rollback
```

Exemplo conceitual:

```text
>98% → candidato a autonomia maior

95–98% → manter

<95% → reduzir autonomia
```

Os thresholds deverão ser validados empiricamente.

---

## 103. REGRA DE DEGRADAÇÃO

Erro reduz autonomia.

```text
L3
↓ erro crítico
L2
↓ novo erro
L1
```

Nunca aumentar autonomia automaticamente apenas pelo tempo.

---

## 104. PRINCÍPIO FINAL DE GOVERNANÇA

Nenhum subagente é responsável pelo sistema.

**Leonard é responsável.**

Nenhum subagente publica por autoridade própria.

**Leonard autoriza.**

Nenhuma execução desaparece.

**Tudo gera evento.**

Nenhuma aprendizagem existe sem evidência.

**Toda aprendizagem possui rastreabilidade.**

---

## 105. ESTADO-ALVO

```text
                    CÓRTEX
                       │
                       ▼
                    LEONARD
                  Hermes Agent
                       │
         ┌─────────────┼─────────────┐
         │             │             │
     Intelligence   Content       Community
         │             │             │
     Research       Creation       Engagement
         │             │             │
         └─────────────┼─────────────┘
                       │
                    POLICY
                       │
                   APPROVAL
                       │
                 LINKEDIN API
                       │
           ┌───────────┴───────────┐
           │                       │
        PERSONAL                COMPANIES
           │                       │
           └───────────┬───────────┘
                       │
                     DATA
                       │
                  ANALYTICS
                       │
                   LEARNING
                       │
                     CÓRTEX
```

O ciclo final é:

> **Observar → Interpretar → Decidir → Agir → Verificar → Aprender.**

Essa é a função de Leonard.

---

## 106. DECISÃO DE ARQUITETURA

**ADR-LNK-001**

Leonard/Hermes será o único agente orquestrador do domínio LinkedIn.

Subagentes serão stateless sempre que possível e especializados por capability.

Toda ação externa deverá passar por:

```text
Leonard
→ Policy
→ Approval
→ Gateway
→ LinkedIn
→ Verification
→ Audit
```

Esta decisão deve ser considerada **arquitetural e canônica** para o projeto.

---

## 107. PRIORIDADES DE IMPLEMENTAÇÃO

### P0

- Leonard;
- OAuth;
- Organization API;
- Member posting;
- Policy Engine;
- Approval;
- Audit;
- Kill Switch;
- quota manager;
- API version manager.

### P1

- conteúdo;
- calendário;
- comentários;
- analytics;
- Brand Guardian;
- Fact Checker.

### P2

- leads;
- experiments;
- knowledge graph;
- advanced learning.

### P3

- autonomia elevada;
- ações sociais adicionais;
- extensões multi-plataforma.

---

## 108. PRIMEIRO MARCO DE PRODUÇÃO

O primeiro marco não deve ser:

> “Leonard publicou um post.”

Deve ser:

> **“Leonard recebeu uma missão, coordenou múltiplos agentes, aplicou políticas, solicitou aprovação, publicou via API, verificou a execução, registrou o trace completo e posteriormente mediu o resultado.”**

Somente neste ponto existe um sistema de agentes.

Antes disso existe apenas automação.

---

## 109. RISCO PRINCIPAL

O maior risco técnico não é o LLM.

É construir a arquitetura presumindo capacidades que as permissões do LinkedIn não fornecem.

A Community Management API exige acesso aprovado e possui Development e Standard Tiers. A leitura ampla de conteúdo pessoal continua restrita.

Portanto a arquitetura deverá usar:

```text
Capability Discovery
```

ao autenticar cada conta.

Exemplo:

```json
{
  "member_write": true,
  "member_read": false,
  "organization_write": true,
  "organization_read": true,
  "organization_analytics": true
}
```

Leonard raciocinará com base nas capabilities reais e nunca presumidas.

---

## 110. VISÃO FUTURA

A mesma arquitetura poderá posteriormente operar:

```text
LinkedIn
Instagram
Facebook
YouTube
X
TikTok
Newsletter
Site
CRM
```

Leonard continuaria como orquestrador.

O LinkedIn seria apenas o primeiro **Channel Domain**.

A arquitetura deverá portanto separar:

```text
Social Intelligence
        │
    Leonard
        │
Channel Adapters
        │
LinkedIn / Meta / X / ...
```

Isso evita reconstruir o sistema quando novos canais forem adicionados.

---

## 111. CONCLUSÃO ARQUITETURAL

A arquitetura canônica deverá obedecer à seguinte cadeia de controle:

```text
Leonard
→ Policy
→ Approval
→ Gateway
→ LinkedIn
→ Verification
→ Audit
→ Analytics
→ Learning
→ Córtex
```

O sistema deve ser orientado por eventos, rastreável, com capacidade real de degradação de autonomia, isolamento de credenciais, gestão de quotas e reconciliação entre estado interno e estado efetivo no LinkedIn.

O objetivo final é transformar Leonard em um **operador social corporativo governado**, capaz de coordenar múltiplos especialistas e múltiplas marcas sem perder controle, identidade ou rastreabilidade.