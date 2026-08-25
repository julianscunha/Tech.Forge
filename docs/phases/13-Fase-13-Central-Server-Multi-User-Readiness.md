# TechForge — Fase 13
## Central Server & Multi-User Readiness

> **Status:** Prompt de implementação consolidado
>
> **Objetivo:** Preparar e validar a evolução do TechForge de uma instalação Desktop local para uma implantação centralizada em servidor Linux, com múltiplos acessos, sem transformar a versão atual em um sistema corporativo pesado antes da necessidade real.

---

# 1. Contexto

O TechForge começa com este modelo:

```text
┌──────────────────────┐
│ Desktop              │
│                      │
│ TechForge            │
│ ├── Frontend         │
│ ├── Backend          │
│ ├── SQLite           │
│ └── Local Modules    │
└──────────────────────┘
```

No futuro, poderá evoluir para:

```text
                 ┌──────────────────────┐
Users ──────────►│ TechForge Server     │
Users ──────────►│                      │
Users ──────────►│ Frontend + Backend   │
                 │ Runtime              │
                 │ Module Registry      │
                 └──────────┬───────────┘
                            │
                     ┌──────▼──────┐
                     │ PostgreSQL  │
                     └─────────────┘
```

A Fase 13 não deve transformar imediatamente a instalação Desktop em um servidor corporativo obrigatório.

O objetivo é garantir que:

```text
Desktop Today
      ↓
Minimal Architectural Changes
      ↓
Central Server Tomorrow
```

seja possível.

---

# 2. Princípio central

Criar uma separação clara entre:

```text
Deployment Model
```

e:

```text
Business / Module Architecture
```

Os módulos não devem precisar saber se estão sendo executados:

```text
Desktop
```

ou:

```text
Central Server
```

O Runtime deve abstrair o ambiente.

---

# 3. Deployment profiles

Definir perfis explícitos.

Exemplo:

```text
DESKTOP
SERVER
DEVELOPMENT
```

Possíveis configurações:

```yaml
deployment:
  mode: desktop
```

ou:

```yaml
deployment:
  mode: server
```

O comportamento deve ser configurável, não duplicado em projetos diferentes.

---

# 4. Desktop profile

Características:

```text
single machine
local process
SQLite
localhost
local modules
single primary user
offline-first
```

O Desktop continua sendo:

- simples;
- leve;
- fácil de iniciar;
- sem serviços externos obrigatórios.

---

# 5. Server profile

Características futuras:

```text
Linux
network access
multiple users
PostgreSQL
central modules
central catalog
central configuration
shared runtime
```

Não implementar toda essa infraestrutura agora.

Criar e validar os pontos de extensão.

---

# 6. Stateless backend direction

Preparar o Backend para minimizar estado local de processo.

Evitar:

```text
global mutable session state
in-memory business state required for correctness
single-user assumptions
```

Permitir:

```text
request context
execution context
shared persistence
```

Isso facilita:

- reinício;
- múltiplas instâncias futuras;
- multiusuário.

---

# 7. Runtime execution ownership

Distinguir:

```text
Platform Runtime
```

de:

```text
User Request
```

Exemplo:

```text
User A
   ↓
request
   ↓
Module Runtime
   ↓
Execution Context A
```

No futuro:

```text
User B
   ↓
request
   ↓
Execution Context B
```

Os contextos não devem se misturar.

Não implementar identidade completa agora, mas não usar variáveis globais de usuário.

---

# 8. Request context

Criar abstração mínima.

Exemplo:

```text
RequestContext
├── request_id
├── source
├── execution_id
├── environment
└── metadata
```

Futuramente poderá incluir:

```text
user_id
tenant_id
roles
```

Mas estes campos não devem ser obrigatórios agora.

---

# 9. Module context

O `ModuleExecutionContext` deve continuar independente do modo de deployment.

Exemplo:

```text
ModuleExecutionContext
├── module
├── runtime
├── storage
├── services
├── logger
├── request_context
└── environment
```

Nenhum módulo deve precisar fazer:

```python
if desktop:
```

para lógica normal de negócio.

---

# 10. Shared storage preparation

A Fase 12 definiu:

```text
SQLite → Desktop
PostgreSQL → Server
```

Nesta fase, validar que:

- acesso a dados está abstraído;
- migrations funcionam com a arquitetura definida;
- módulos não dependem de caminhos locais para dados estruturados;
- transações não assumem processo único.

Não forçar PostgreSQL no Desktop.

---

# 11. Filesystem strategy

No Desktop:

```text
local filesystem
```

No Server:

```text
central filesystem
```

Futuramente pode evoluir para:

```text
object storage
```

Separar abstrações:

```text
Temporary Files
Persistent Files
Exports
Module Assets
```

Evitar que módulos assumam:

```text
C:\Users\...
```

ou caminhos específicos do host.

---

# 12. Network binding

Preparar configurações:

```text
HOST
PORT
CORS
TRUSTED_ORIGINS
```

Desktop:

```text
127.0.0.1
```

Server:

```text
configurable interface
reverse proxy friendly
```

Não abrir acesso de rede por padrão na versão Desktop.

---

# 13. Reverse proxy readiness

Preparar o Backend para execução atrás de:

```text
Nginx
Caddy
Apache
```

quando em Server mode.

Considerar:

- forwarded headers;
- HTTPS termination;
- base paths quando aplicável;
- health endpoint.

Não exigir reverse proxy no Desktop.

---

# 14. Frontend deployment

Preparar o Frontend para:

```text
Desktop local serving
```

e:

```text
static build served centrally
```

Evitar dependências rígidas de:

```text
localhost:8000
```

como endereço imutável.

Utilizar configuração de API base URL.

---

# 15. Single instance startup

A experiência Desktop deve continuar simples.

O usuário não deve precisar abrir:

```text
PowerShell 1 → Backend
PowerShell 2 → Frontend
```

A arquitetura deve suportar:

```text
TechForge Launcher
        ↓
Start Backend
        ↓ wait health
Start Frontend
        ↓
Open Application
```

Para distribuição futura, considerar:

```text
single executable
desktop launcher
installer shortcut
```

Não obrigar o usuário corporativo a conhecer comandos técnicos.

---

# 16. Server startup

No modo Server:

```text
Service Manager
      ↓
TechForge Backend
      ↓
Health Ready
      ↓
Frontend Available
```

Preparar documentação para:

```text
systemd
Docker optional
process manager
```

Não tornar Docker obrigatório.

---

# 17. Health checks

Definir endpoints:

```text
/health
/ready
/version
```

Exemplo:

```text
Health
→ processo responde

Ready
→ database + critical services ready

Version
→ platform metadata
```

Módulos críticos podem contribuir para readiness conforme política futura.

---

# 18. Graceful shutdown

No Server:

```text
Shutdown signal
      ↓
Stop new requests
      ↓
Finish/cancel active executions
      ↓
Module shutdown
      ↓
Close storage
      ↓
Exit
```

Reutilizar o Module Runtime.

Não criar um segundo lifecycle.

---

# 19. Concurrency

Preparar para múltiplas requisições.

Regras:

- não usar estado global mutável para execução;
- execution IDs únicos;
- logs contextualizados;
- transações delimitadas;
- operações longas isoladas.

Não tentar otimizar para grande escala antes de existir necessidade.

---

# 20. Background work preparation

Algumas operações podem ser longas.

Exemplos:

```text
VMware Health Check
AWS discovery
Large sizing calculations
Report generation
```

Preparar abstração:

```text
Task / Job
```

Inicialmente pode executar no mesmo processo de forma controlada.

Futuramente poderá evoluir para:

```text
worker
queue
distributed jobs
```

Não introduzir RabbitMQ, Redis ou Celery sem necessidade concreta.

---

# 21. Session readiness

Não implementar login agora.

Mas garantir que o sistema não dependa de:

```text
single global user state
```

Preparar Request Context para futura sessão.

Não criar tabelas de usuários sem necessidade.

---

# 22. Authorization readiness

O modelo futuro pode ter:

```text
User
Role
Module Access
```

Mas nesta fase:

```text
all users can access all modules
```

A arquitetura deve permitir adicionar autorização depois sem alterar contratos fundamentais.

Não implementar RBAC.

---

# 23. Multi-user data collisions

Preparar módulos para não sobrescrever dados arbitrariamente.

Exemplo ruim:

```text
last_report.csv
```

global para todos.

Preferir:

```text
execution_id/
timestamp/
unique output
```

Quando dados forem compartilhados, usar persistência controlada.

---

# 24. Central module registry

No Server mode, preparar:

```text
Central Installed Modules
```

Todos os usuários enxergam o mesmo conjunto.

No Desktop:

```text
Local Installed Modules
```

A interface de módulos deve depender do Registry, não do filesystem diretamente.

---

# 25. Central catalog

O Catálogo pode futuramente existir no servidor.

Fluxo:

```text
Client
   ↓
TechForge Server
   ↓
Central Catalog
```

A Fase 11 já possui abstração de Catalog Provider.

Validar que a arquitetura suporta:

```text
Local Catalog
```

e:

```text
Server Catalog
```

sem reescrever a UI.

---

# 26. Configuration scope

Preparar escopos:

```text
Platform
Module
Environment
Future User
```

No Desktop:

```text
Platform + Module
```

No Server:

```text
Platform + Module + Environment
```

Futuro:

```text
User preferences
```

Não implementar personalização individual agora.

---

# 27. Environment configuration

Utilizar configuração por ambiente.

Exemplo:

```text
development
desktop
server
test
```

Evitar múltiplos arquivos com lógica divergente difícil de manter.

Definir defaults e overrides claros.

---

# 28. Observability readiness

No Server, preparar:

- structured logs;
- request IDs;
- execution IDs;
- health;
- metrics extensíveis.

Não exigir uma plataforma externa de observabilidade.

O Desktop deve continuar com logging local simples.

---

# 29. Metrics abstraction

Preparar uma interface opcional.

Exemplo:

```text
MetricEmitter
```

Métricas possíveis:

```text
requests
module executions
duration
errors
active modules
```

No Desktop pode ser:

```text
no-op / local
```

No Server futuramente:

```text
Prometheus-compatible
```

Não implementar stack completa de métricas.

---

# 30. Server security baseline

Quando Server mode existir, preparar:

- HTTPS via reverse proxy;
- network binding controlado;
- trusted origins;
- secrets externos;
- secure headers quando aplicável.

Não assumir que a segurança da instalação local é suficiente para uma rede.

---

# 31. Deployment documentation

Documentar:

## Desktop

```text
Install
Start
Stop
Data location
Module location
Backup
Update
```

## Server

```text
Linux requirements
Database
Environment
Reverse proxy
Startup
Health checks
Backup
Update
```

A documentação Server pode inicialmente ser de preparação arquitetural e referência.

---

# 32. Developer Center

Documentar:

- deployment modes;
- Request Context;
- Module Context;
- storage portability;
- filesystem portability;
- long-running tasks;
- concurrency;
- central execution;
- anti-patterns.

Adicionar uma seção:

```text
Writing Server-Ready Modules
```

O AI Context deve incluir essas regras.

---

# 33. API versioning

Preparar versionamento explícito:

```text
/api/v1/
```

Já existente quando aplicável.

Garantir que novos endpoints:

- mantenham compatibilidade;
- tenham contratos claros;
- possam evoluir.

Não implementar v2 sem necessidade.

---

# 34. Compatibility validation

Adicionar validações de deployment quando necessárias.

Exemplo:

```text
Module requires:
network access

Desktop:
warning

Server:
supported
```

Ou:

```text
Module requires:
local device

Server:
incompatible
```

Preparar metadata de requisitos de ambiente.

Não criar matriz complexa sem necessidade.

---

# 35. Migration validation

Criar um teste ou modo de validação:

```text
Desktop Architecture Check
```

que detecte dependências indevidas:

- paths locais hardcoded;
- SQLite-specific code fora da abstração;
- estado global inadequado;
- localhost hardcoded.

O objetivo é evitar que o sistema Desktop se torne impossível de migrar.

---

# 36. Testes

Criar testes para:

- deployment profiles;
- Desktop configuration;
- Server configuration;
- Request Context isolation;
- Module Execution Context portability;
- API base URL;
- network binding defaults;
- health;
- readiness;
- graceful shutdown;
- concurrent requests;
- unique execution IDs;
- filesystem paths;
- storage abstraction;
- no global user state;
- startup launcher integration;
- module registry portability;
- environment configuration;
- long-running task abstraction;
- migration readiness checks;
- API;
- frontend.

Teste conceitual:

```text
DESKTOP
  ↓
Start
  ↓
Local Module
  ↓
Execute
  ↓
Stop
```

E:

```text
SERVER PROFILE
  ↓
Configured Storage Provider
  ↓
Network Binding
  ↓
Multiple Request Contexts
  ↓
Concurrent Module Executions
```

Sem necessariamente exigir infraestrutura Linux real durante todos os testes.

---

# 37. O que não implementar

Não implementar nesta fase:

- login;
- RBAC;
- SSO;
- MFA;
- cluster;
- Kubernetes;
- load balancer obrigatório;
- Redis obrigatório;
- RabbitMQ obrigatório;
- worker farm;
- tenancy completa.

O objetivo é readiness, não hyperscale.

---

# 38. Critérios de aceitação

A fase estará concluída quando:

1. Deployment profiles existirem.
2. Desktop continuar simples.
3. Server mode estiver arquiteturalmente previsto.
4. Módulos não dependerem do modo de deployment.
5. Request Context existir.
6. Execution Context suportar múltiplas requisições.
7. Storage permanecer portável.
8. Paths não forem hardcoded.
9. API URL não for rigidamente localhost.
10. Health e readiness existirem.
11. Graceful shutdown reutilizar o Runtime.
12. Concurrency básica for suportada.
13. Long-running task abstraction existir.
14. Launcher Desktop continuar simples.
15. Server startup estiver documentado.
16. Registry puder ser centralizado.
17. Catalog puder ser centralizado.
18. Configuração por ambiente existir.
19. Métricas estiverem preparadas por abstração.
20. Server security baseline estiver documentado.
21. Developer Center possuir Server-Ready Modules.
22. AI Context incluir essas regras.
23. Migration readiness checks existirem.
24. Todos os testes passarem.
25. Build do Frontend passar.
26. Core permanecer leve.

---

# Regra final

Antes de finalizar:

- testar perfil Desktop;
- iniciar via Launcher único;
- validar health;
- validar ready;
- executar módulo;
- validar shutdown;
- testar Request Contexts simultâneos;
- testar Execution IDs únicos;
- verificar ausência de localhost hardcoded;
- verificar paths portáveis;
- validar perfil Server por configuração;
- validar Storage abstraction;
- validar API base URL configurável;
- executar migration readiness checks;
- revisar documentação;
- executar todos os testes;
- executar build do Frontend.

Apresentar:

```text
Deployment Profiles:
Desktop:
Server Readiness:
Request Context:
Execution Context:
Storage Portability:
Filesystem Portability:
Network:
Reverse Proxy:
Frontend Deployment:
Launcher:
Server Startup:
Health:
Readiness:
Graceful Shutdown:
Concurrency:
Background Tasks:
Registry:
Catalog:
Configuration Scope:
Observability:
Metrics:
Server Security Baseline:
Developer Center:
AI Context:
Migration Readiness:
Tests:
Build:
Known Issues:
```
