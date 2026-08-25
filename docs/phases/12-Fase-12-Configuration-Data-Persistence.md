---
title: TechForge — Fase 12
category: fases
domain: [fases]
---

# TechForge — Fase 12
## Configuration, Data & Persistence

> **Status:** Prompt de implementação consolidado
>
> **Objetivo:** Consolidar a estratégia de configuração, armazenamento de dados e persistência do TechForge e de seus módulos, mantendo a instalação desktop leve e preparando a arquitetura para futura migração a um servidor Linux com múltiplos usuários.

---

# 1. Contexto

O TechForge começa como uma aplicação local.

Fluxo inicial:

```text
Usuário
   ↓
Desktop
   ↓
TechForge Local
   ↓
Dados locais
```

No futuro poderá evoluir para:

```text
Múltiplos usuários
        ↓
Rede
        ↓
TechForge Server
        ↓
Database central
```

A arquitetura precisa permitir essa evolução sem obrigar a reescrita dos módulos.

---

# 2. Princípio central

Separar claramente:

```text
Configuration
```

de:

```text
Application Data
```

e de:

```text
Module Data
```

Também separar:

```text
Core-owned data
```

de:

```text
Module-owned data
```

O Core não deve conhecer o schema interno de negócio de cada módulo.

---

# 3. Storage abstraction

Criar uma abstração de persistência.

Exemplo:

```text
Storage Provider
```

Responsabilidades:

- inicialização;
- conexão;
- migrations;
- transactions;
- health;
- shutdown.

O Core deve conseguir utilizar inicialmente:

```text
SQLite
```

e futuramente:

```text
PostgreSQL
```

sem alterar a semântica dos módulos.

---

# 4. Estratégia inicial

Para Desktop:

```text
SQLite
```

Motivos:

- leve;
- sem servidor;
- arquivo único;
- simples de distribuir;
- suficiente para o Core inicial.

Para futuro Server:

```text
PostgreSQL
```

Não implementar PostgreSQL como requisito da instalação local.

Mas evitar decisões que impeçam a migração.

---

# 5. Database ownership

Definir domínios.

Exemplo:

```text
Core Database
├── modules
├── installations
├── lifecycle
├── configuration
├── notifications
├── catalog cache
├── publishers
└── platform metadata
```

Cada módulo pode possuir:

```text
Module Namespace
```

ou tabelas próprias.

Exemplo:

```text
module_veeam_m365_*
module_aws_cost_*
```

A estratégia final deve ser consistente.

---

# 6. Module data isolation

O módulo deve possuir acesso controlado ao seu espaço de dados.

Exemplo conceitual:

```text
context.storage
```

ou:

```text
context.database
```

O módulo não deve manipular diretamente tabelas internas do Core.

Da mesma forma:

```text
Core
```

não deve depender do schema interno de negócio do módulo.

---

# 7. Module storage API

Definir uma API mínima.

Exemplo conceitual:

```text
module_storage.get()
module_storage.set()
module_storage.transaction()
```

Para casos simples, pode existir:

```text
Key-Value Configuration
```

Para módulos que precisam de dados estruturados:

```text
Database access
```

Não forçar todos os módulos a usar banco relacional diretamente.

---

# 8. Configuration hierarchy

Definir níveis de configuração.

Exemplo:

```text
Platform Configuration
      ↓
Module Configuration
      ↓
Runtime Configuration
      ↓
Execution Configuration
```

Explicação:

```text
Platform
→ configuração global do TechForge

Module
→ configuração persistente do módulo

Runtime
→ parâmetros do ambiente atual

Execution
→ parâmetros de uma execução específica
```

Evitar mistura.

---

# 9. Platform configuration

Exemplos:

```text
host
port
database
module paths
catalog sources
logging
update policy
development mode
```

A configuração deve:

- ser validada;
- possuir defaults;
- não conter segredos em arquivos públicos.

---

# 10. Module configuration

Cada módulo deve declarar sua configuração.

Exemplo:

```yaml
configuration:
  fields:
    - id: retention_days
      type: integer
      default: 30
```

O formato exato pode evoluir.

Requisitos:

- tipado;
- validável;
- documentável;
- versionável.

O módulo deve conseguir gerar ou utilizar uma página de configuração integrada quando necessário.

---

# 11. Secrets

Mesmo sem autenticação complexa, alguns módulos poderão usar:

```text
API keys
tokens
credentials
connection strings
```

Não armazenar segredos em:

- manifest;
- documentação;
- repositório;
- logs;
- exportações comuns.

Criar uma abstração:

```text
Secret Store
```

Para Desktop, pode inicialmente utilizar o mecanismo mais seguro disponível no sistema operacional ou solução local apropriada.

Para Server, preparar integração futura com:

```text
environment secrets
external secret providers
```

Não implementar criptografia caseira.

---

# 12. Configuration validation

Toda configuração deve ser validada antes do uso.

Exemplo:

```text
Module Config
    ↓
Schema Validation
    ↓
Valid?
    ├── No → Error
    └── Yes → Persist
```

Não deixar o módulo descobrir erros de configuração apenas durante execução quando puder validar antes.

---

# 13. Configuration migrations

Configurações também evoluem.

Exemplo:

```text
Module 1.0
config:
  region
```

Depois:

```text
Module 2.0
config:
  regions
```

Preparar:

```text
Configuration Migration
```

Associada à versão do módulo.

Não depender de alterações manuais do usuário.

---

# 14. Database migrations

Cada mudança estrutural deve ser versionada.

Definir:

```text
Core migrations
```

e:

```text
Module migrations
```

Separar ownership.

Exemplo:

```text
core migrations
module migrations
```

O Package Manager e Runtime devem saber quando uma migration é necessária.

---

# 15. Module migration lifecycle

Fluxo:

```text
Module Update
      ↓
Validate Package
      ↓
Backup/Transaction
      ↓
Run Module Migration
      ↓
Validate
      ↓
Activate
```

Se falhar:

```text
Rollback when possible
```

Não atualizar código e deixar dados incompatíveis silenciosamente.

---

# 16. Data portability

Preparar exportação futura.

Exemplos:

```text
Module configuration export
Module data export
Platform configuration export
```

Não implementar backup corporativo completo agora.

Mas evitar formatos proprietários desnecessários.

Preferir:

```text
JSON
CSV
documented relational schema
```

quando adequado.

---

# 17. Backup

Como o TechForge pode armazenar informações importantes, prever:

```text
Local backup strategy
```

Inicialmente pode ser:

- backup do arquivo SQLite;
- exportação controlada;
- snapshot antes de migrations críticas.

Não criar um sistema completo de backup de infraestrutura.

---

# 18. Data retention

Cada módulo deve poder declarar necessidades de retenção.

Exemplo:

```text
execution history: 90 days
cache: 7 days
reports: manual
```

Não implementar limpeza automática destrutiva sem política explícita.

---

# 19. Cache

Separar:

```text
Persistent Data
```

de:

```text
Cache
```

O cache deve:

- possuir TTL quando aplicável;
- poder ser limpo;
- não ser fonte única de verdade.

Exemplo:

```text
AWS API data cache
```

não deve ser tratado como dado permanente sem necessidade.

---

# 20. Filesystem storage

Alguns módulos precisarão gerar:

- relatórios;
- CSV;
- XLSX;
- PDF;
- arquivos temporários.

Criar caminhos oficiais.

Exemplo:

```text
data/
cache/
exports/
temp/
modules/
```

Cada módulo deve receber paths via Runtime Context.

Não usar caminhos arbitrários hardcoded.

---

# 21. User data paths

A instalação deve distinguir:

```text
Application Files
```

de:

```text
User Data
```

Isso facilita:

- atualização;
- reinstalação;
- backup;
- migração.

Não misturar banco e configuração dentro da pasta de código se isso dificultar updates.

---

# 22. Multi-user preparation

Não implementar multiusuário agora.

Mas evitar:

```text
global mutable state
local hardcoded user assumptions
file locking sem abstração
```

Preparar conceitos:

```text
tenant/context
user context
request context
```

Somente como abstrações futuras quando necessário.

Não adicionar autenticação prematuramente.

---

# 23. Desktop to Server migration

A arquitetura deve permitir:

```text
SQLite
    ↓ migration
PostgreSQL
```

e:

```text
Local configuration
    ↓
Central configuration
```

O Module API deve depender de abstrações estáveis, não de detalhes específicos do SQLite.

---

# 24. Persistence health

Criar health checks simples:

```text
Database available
Migrations current
Storage writable
Disk space warning optional
```

O Dashboard pode mostrar apenas:

```text
Data Store: Healthy
```

---

# 25. Transaction boundaries

Operações críticas devem usar transações.

Exemplos:

```text
Install module
Update module
Run migration
Save configuration
```

Definir claramente:

```text
transaction start
commit
rollback
```

Não manter transações abertas durante tarefas longas.

---

# 26. Concurrency preparation

No Desktop:

```text
single-user local
```

No futuro:

```text
multi-user
```

Evitar código que dependa de acesso exclusivo permanente ao banco.

Usar padrões adequados da ORM/stack existente.

Não otimizar prematuramente para centenas de usuários.

---

# 27. Data schema governance

Cada módulo que possuir persistência estruturada deve:

- declarar migrations;
- documentar ownership;
- evitar modificar tabelas do Core;
- não acessar tabelas de outros módulos diretamente.

Comunicação entre módulos deve ocorrer preferencialmente por:

```text
Service Registry
```

e não por acesso direto ao banco de outro módulo.

---

# 28. Observability

Registrar:

```text
migration completed
migration failed
storage unavailable
backup created
configuration validation failed
```

Não registrar:

```text
secrets
tokens
credentials
```

---

# 29. APIs

Criar APIs coerentes.

Exemplos:

```text
GET /api/v1/system/storage/status
GET /api/v1/config
GET /api/v1/modules/{id}/config
PUT /api/v1/modules/{id}/config
POST /api/v1/modules/{id}/config/validate
```

Não criar endpoint genérico que permita acesso arbitrário ao banco.

---

# 30. CLI

Adicionar:

```bash
techforge storage status
techforge config validate
techforge modules config <module>
techforge modules config validate <module>
techforge migrations status
techforge migrations run
```

Comandos devem respeitar ownership e lifecycle.

---

# 31. Frontend

Criar interfaces leves para:

```text
Platform Settings
Module Settings
Storage Status
Migration Status
```

Não criar um painel administrativo enorme.

A configuração de um módulo deve aparecer preferencialmente:

```text
Module Details
→ Settings
```

---

# 32. Developer Center

Documentar:

- Storage API;
- Configuration API;
- Secrets;
- Module Data Ownership;
- Migrations;
- Cache;
- Filesystem paths;
- Data portability;
- Desktop → Server migration.

Adicionar exemplos de:

```text
simple config
database module
migration
secret usage
```

O AI Context deve incluir essas regras.

---

# 33. Testes

Criar testes para:

- SQLite initialization;
- Storage abstraction;
- Core data ownership;
- Module namespace;
- Module config;
- Config validation;
- Invalid config;
- Config migration;
- Database migration;
- Transaction commit;
- Transaction rollback;
- Secret abstraction;
- Secret redaction in logs;
- Cache TTL;
- Filesystem paths;
- Export/import;
- Backup before migration;
- Storage health;
- Module isolation;
- Server portability assumptions;
- API;
- CLI;
- frontend.

Teste integrado:

```text
Install Module
      ↓
Create Config
      ↓
Validate
      ↓
Persist
      ↓
Execute
      ↓
Update Module
      ↓
Run Migration
      ↓
Preserve Data
```

Também:

```text
Migration fails
      ↓
Rollback
      ↓
Previous state preserved
```

---

# 34. O que não implementar

Não implementar nesta fase:

- PostgreSQL obrigatório;
- multiusuário completo;
- autenticação;
- RBAC;
- replicação;
- cluster;
- backup corporativo;
- data warehouse.

A fase deve preparar a arquitetura, não antecipar toda a infraestrutura futura.

---

# 35. Critérios de aceitação

A fase estará concluída quando:

1. Storage abstraction existir.
2. SQLite funcionar para Desktop.
3. PostgreSQL futuro não exigir redesign dos módulos.
4. Core e Module Data tiverem ownership separado.
5. Module Storage API existir.
6. Configuration hierarchy estiver definida.
7. Configuração de módulo for tipada e validável.
8. Secrets não forem armazenados em locais inadequados.
9. Secret Store abstraction existir.
10. Config migrations forem previstas.
11. Database migrations forem separadas entre Core e módulos.
12. Updates puderem executar migrations.
13. Falhas de migration forem tratadas.
14. Cache for separado de dados persistentes.
15. Filesystem paths forem oficiais.
16. Application files e user data forem separados.
17. Storage Health existir.
18. APIs funcionarem.
19. CLI funcionar.
20. Frontend de configuração for integrado.
21. Developer Center documentar persistência.
22. AI Context incluir regras.
23. Todos os testes passarem.
24. Core continuar leve.

---

# Regra final

Antes de finalizar:

- iniciar instalação limpa;
- validar SQLite;
- instalar módulo;
- salvar configuração;
- testar configuração inválida;
- executar módulo;
- criar dados;
- atualizar módulo;
- executar migration;
- confirmar preservação;
- simular falha;
- confirmar rollback;
- verificar paths;
- verificar que segredos não aparecem em logs;
- testar exportação;
- testar storage health;
- executar todos os testes;
- executar build do Frontend.

Apresentar:

```text
Storage Architecture:
SQLite Desktop:
Future PostgreSQL:
Data Ownership:
Module Storage API:
Configuration:
Configuration Validation:
Secrets:
Migrations:
Transactions:
Cache:
Filesystem:
User Data:
Backup:
Health:
Desktop-to-Server Readiness:
Frontend:
API:
CLI:
Developer Center:
AI Context:
Tests:
Build:
Known Issues:
```
