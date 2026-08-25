---
title: TechForge — Fase 11
category: fases
domain: [fases]
---

# TechForge — Fase 11
## Module Marketplace & Distribution

> **Status:** Prompt de implementação consolidado
>
> **Objetivo:** Implementar o catálogo e a distribuição de módulos do TechForge, inicialmente com suporte a fontes locais/internas e arquitetura preparada para catálogos centralizados futuros, sem criar uma plataforma comercial de marketplace.

---

# 1. Contexto

O TechForge é uma plataforma corporativa interna e modular.

O objetivo desta fase não é criar um marketplace comercial.

O objetivo é permitir:

```text
Discover
↓
Inspect
↓
Validate
↓
Install
↓
Activate
↓
Use
```

Para módulos disponíveis à organização.

Exemplo:

```text
Available Modules

Backup
├── Veeam M365 Sizing
├── Salesforce Sizing
└── AWS Backup Sizing

Virtualization
└── VMware Health Check

Cloud
└── AWS Cost Service
```

---

# 2. Conceito de catálogo

Separar:

```text
Module Catalog
```

de:

```text
Installed Modules
```

Um módulo pode estar:

```text
AVAILABLE
INSTALLED
ACTIVE
DISABLED
UPDATE_AVAILABLE
BLOCKED
```

O catálogo mostra o que pode ser obtido.

A área de módulos mostra o que está instalado.

Não misturar os dois conceitos.

---

# 3. Fontes de distribuição

Definir uma abstração:

```text
ModuleSource
```

Fontes iniciais:

```text
LOCAL_DIRECTORY
LOCAL_PACKAGE
INTERNAL_CATALOG
```

Preparar para:

```text
REMOTE_CATALOG
GIT_SOURCE
ENTERPRISE_REPOSITORY
```

Não implementar todas as fontes agora.

---

# 4. Local package

Permitir instalação a partir de:

```text
.zip
```

ou formato oficial de pacote.

Fluxo:

```text
Select Package
      ↓
Inspect Package
      ↓
Validate
      ↓
Show Results
      ↓
Confirm
      ↓
Install
```

Nunca instalar diretamente sem inspeção.

---

# 5. Local directory development

Permitir ambiente de desenvolvimento.

Fluxo:

```text
Developer Module Folder
        ↓
Register Local Source
        ↓
Discover
        ↓
Validate
        ↓
Install/Link
```

Quando apropriado, suportar:

```text
development mode
```

O objetivo é facilitar a criação de módulos sem exigir empacotamento a cada alteração.

Separar claramente:

```text
Development Module
```

de:

```text
Distributed Package
```

---

# 6. Internal catalog

Criar arquitetura para um catálogo interno.

Inicialmente pode ser:

```text
local JSON/YAML
```

ou API local.

Cada item deve possuir:

- module id;
- nome;
- descrição;
- categoria;
- versão;
- publisher;
- compatibilidade;
- source;
- trust metadata;
- tamanho quando disponível.

Exemplo conceitual:

```json
{
  "id": "veeam_m365_sizing",
  "version": "1.0.0",
  "category": "Backup/Veeam",
  "publisher": "techforge.internal"
}
```

---

# 7. Catalog provider

Criar interface:

```text
CatalogProvider
```

Responsabilidades:

```text
list_modules()
get_module()
get_versions()
get_updates()
download_package()
```

Cada fonte implementa a interface.

Não acoplar a UI a uma fonte específica.

---

# 8. Marketplace page

Criar página integrada:

```text
Modules Catalog
```

Não chamar necessariamente de marketplace na interface se isso sugerir comércio.

Sugestão de nome:

```text
Catálogo de Módulos
```

A página deve permitir:

- buscar;
- filtrar;
- navegar por categoria;
- visualizar detalhes;
- verificar compatibilidade;
- verificar trust;
- instalar.

Visual:

- clean;
- corporativo;
- leve;
- cards simples;
- sem excesso de banners.

---

# 9. Categories

Reutilizar taxonomia oficial.

Exemplo:

```text
Backup
└── Veeam

Virtualization
└── VMware

Cloud
└── AWS

Commercial
└── Lead Generation
```

Formato:

```text
Domain > Vendor > Module
```

Categorias devem ser metadados do módulo.

Não codificar menus manualmente.

---

# 10. Module details

Ao abrir um item do catálogo, mostrar:

```text
Name
Description
Version
Publisher
Compatibility
Dependencies
Trust
Documentation
Capabilities
Install Source
```

Para Service Modules:

```text
Public Capabilities
Contract
Examples
```

Para Application Modules:

```text
Features
Dependencies
Screenshots optional
```

Não exigir imagens para todos os módulos.

---

# 11. Installation flow

Fluxo completo:

```text
Select Module
      ↓
Download/Acquire
      ↓
Inspect
      ↓
Structure Validation
      ↓
Compatibility Validation
      ↓
Dependency Validation
      ↓
Documentation Compliance
      ↓
Integrity
      ↓
Trust
      ↓
Install Preview
      ↓
Confirm
      ↓
Install
      ↓
Available
      ↓
Activate
```

A instalação não deve automaticamente significar ativação.

Respeitar o fluxo:

```text
Install
↓
Available / Installed
↓
Activate
↓
Active
```

---

# 12. Download management

Para fontes remotas futuras, criar abstração.

Responsabilidades:

- download;
- progresso;
- checksum;
- cancelamento;
- retry quando aplicável;
- cleanup.

Não implementar download paralelo complexo sem necessidade.

---

# 13. Update discovery

O catálogo deve permitir identificar:

```text
Installed: 1.0.0
Available: 1.1.0
```

Resultado:

```text
UPDATE_AVAILABLE
```

Não atualizar automaticamente nesta fase.

O usuário deve:

```text
Review
↓
Validate
↓
Confirm
↓
Update
```

---

# 14. Update compatibility

Antes de atualizar:

```text
New Version
      ↓
Core Compatibility
      ↓
Dependency Governance
      ↓
Trust Verification
      ↓
Documentation Validation
      ↓
Update
```

Também verificar dependentes quando necessário.

Não quebrar consumidores silenciosamente.

---

# 15. Version history

Preparar estrutura para:

```text
Module
├── 1.0.0
├── 1.1.0
└── 2.0.0
```

O catálogo pode mostrar:

- versões disponíveis;
- versão instalada;
- release notes;
- compatibilidade.

Não implementar rollback complexo ainda, mas manter arquitetura preparada.

---

# 16. Distribution metadata

Definir um descriptor de catálogo.

Exemplo conceitual:

```text
CatalogModule
├── module_id
├── name
├── description
├── category
├── versions
├── publisher
├── compatibility
├── source
├── trust
└── metadata
```

Separar:

```text
Catalog metadata
```

de:

```text
Installed module metadata
```

---

# 17. Offline-first

Como o TechForge inicialmente roda localmente:

- catálogo local deve funcionar offline;
- módulos instalados devem continuar funcionando sem catálogo;
- falha de conexão não deve impedir o uso do sistema.

Para fontes remotas:

```text
Unavailable Source
```

deve ser tratado como informação, não como falha do Core.

---

# 18. Cache

Para catálogos remotos futuros:

- cache controlado;
- metadata cache;
- expiração;
- atualização manual.

Não cachear indefinidamente versões sem controle.

---

# 19. Source priority

Se houver múltiplas fontes:

```text
Internal Catalog
Local Development
Local Package
Remote Catalog
```

A prioridade deve ser explícita.

Não escolher arbitrariamente.

O mesmo módulo encontrado em fontes diferentes deve ser identificado como possível conflito.

---

# 20. Conflict handling

Exemplo:

```text
veeam_m365_sizing
```

disponível em:

```text
Internal Catalog → 1.2.0
Local Package → 1.3.0-dev
```

Mostrar claramente:

- fonte;
- versão;
- publisher;
- trust.

Não substituir silenciosamente.

---

# 21. Installation transaction

Instalação deve ser transacional quando possível.

Fluxo:

```text
Acquire
↓
Validate
↓
Prepare staging
↓
Install files
↓
Register module
↓
Rebuild registries
↓
Complete
```

Se falhar:

```text
Rollback
```

Não deixar módulos parcialmente instalados.

---

# 22. Update transaction

Fluxo:

```text
Validate New Version
↓
Prepare Staging
↓
Stop Runtime
↓
Backup Previous State
↓
Apply Update
↓
Validate
↓
Activate
↓
Success
```

Se falhar:

```text
Restore Previous Version
```

A implementação inicial pode ter rollback limitado, mas o comportamento deve ser explícito.

---

# 23. Notifications

Notificar:

```text
New module available
Update available
Installation completed
Installation failed
Validation blocked
Source unavailable
```

Não gerar notificações para cada atualização de catálogo.

---

# 24. Dashboard

O Dashboard simples pode mostrar:

```text
Installed Modules
Active Modules
Available Updates
Catalog Sources Status
```

Manter o Dashboard enxuto.

---

# 25. Developer Center

Documentar:

- como criar pacote;
- como publicar internamente;
- catalog descriptor;
- versões;
- categorias;
- release notes;
- desenvolvimento local;
- distribuição;
- trust requirements.

O AI Context deve incluir o formato oficial de distribuição.

---

# 26. CLI

Adicionar:

```bash
techforge catalog list
techforge catalog search <term>
techforge catalog show <module>
techforge catalog sources
techforge modules install <source>
techforge modules update <module>
techforge modules updates
```

A CLI deve reutilizar o Package Manager, Validators e Catalog Providers.

---

# 27. APIs

Criar APIs:

```text
GET /api/v1/catalog/modules
GET /api/v1/catalog/modules/{id}
GET /api/v1/catalog/modules/{id}/versions
GET /api/v1/catalog/sources
GET /api/v1/catalog/updates
```

A instalação deve reutilizar o fluxo oficial existente.

Não criar uma segunda implementação de Package Manager via API.

---

# 28. Frontend architecture

Criar componentes reutilizáveis:

```text
CatalogPage
CatalogCard
CatalogDetails
CategoryFilter
SourceStatus
InstallDialog
UpdateDialog
```

O estado deve refletir o backend.

Não duplicar regras de:

- compatibilidade;
- dependência;
- trust.

---

# 29. Testes

Criar testes para:

- CatalogProvider;
- Local Directory;
- Local Package;
- Internal Catalog;
- list;
- search;
- categories;
- details;
- compatibility;
- install flow;
- validation failure;
- dependency missing;
- trust failure;
- transaction rollback;
- update detection;
- source conflict;
- offline behavior;
- API;
- CLI;
- frontend states.

Teste integrado:

```text
Catalog discovers module
        ↓
User selects
        ↓
Validation
        ↓
Install
        ↓
Installed
        ↓
Activate
        ↓
Visible in Modules
        ↓
Open in Runtime
```

Também testar:

```text
Update Available
        ↓
Validate
        ↓
Update
        ↓
Version changes
```

---

# 30. O que não implementar

Não implementar nesta fase:

- pagamentos;
- venda de módulos;
- marketplace público;
- contas externas;
- avaliação pública;
- comentários;
- ranking;
- sincronização obrigatória em nuvem.

O foco é distribuição corporativa e modular.

---

# 31. Critérios de aceitação

A fase estará concluída quando:

1. Catálogo de módulos existir.
2. Catálogo e módulos instalados forem separados.
3. Fontes forem abstraídas.
4. Local Package funcionar.
5. Local Development funcionar.
6. Internal Catalog funcionar.
7. Categorias forem dinâmicas.
8. Detalhes de módulos forem exibidos.
9. Instalação usar validação consolidada.
10. Instalação não ativar automaticamente sem política explícita.
11. Updates forem detectados.
12. Compatibilidade for validada.
13. Dependências forem respeitadas.
14. Trust for exibido.
15. Conflitos de fonte forem detectados.
16. Instalação tiver staging/rollback quando aplicável.
17. Offline-first for preservado.
18. APIs funcionarem.
19. CLI funcionar.
20. Frontend integrado funcionar.
21. Developer Center documentar distribuição.
22. AI Context incluir formato de catálogo.
23. Todos os testes passarem.
24. Build do Frontend passar.

---

# Regra final

Antes de finalizar:

- criar catálogo local;
- adicionar módulos de teste;
- listar;
- pesquisar;
- filtrar categoria;
- abrir detalhes;
- instalar;
- validar;
- ativar;
- executar no Runtime;
- testar fonte indisponível;
- testar conflito;
- testar update disponível;
- testar update;
- testar rollback de falha;
- executar testes;
- executar build.

Apresentar:

```text
Catalog Architecture:
Catalog Providers:
Sources:
Local Development:
Local Package:
Internal Catalog:
Categories:
Module Details:
Installation:
Transactions:
Updates:
Offline Behavior:
Conflicts:
Notifications:
Dashboard:
Frontend:
API:
CLI:
Developer Center:
AI Context:
Tests:
Build:
Known Issues:
```
