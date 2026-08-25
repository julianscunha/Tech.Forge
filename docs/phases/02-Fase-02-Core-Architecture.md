# TechForge — Fase 2
## Core Architecture

> **Status:** Prompt de implementação consolidado
>
> **Objetivo:** Consolidar a arquitetura interna do Core, estabelecendo responsabilidades, contratos e componentes fundamentais sem implementar módulos de negócio.

---

## Contexto

A Fase 1 estabeleceu a fundação técnica do TechForge:

- Backend Python/FastAPI;
- Frontend React/TypeScript;
- SQLite;
- configuração centralizada;
- Health Check;
- Dashboard básico;
- navegação inicial;
- logging;
- testes;
- documentação inicial.

Nesta fase, consolidar a arquitetura do **Core**.

O objetivo é garantir que o Core permaneça:

- pequeno;
- estável;
- modular;
- desacoplado de regras de negócio;
- preparado para crescimento futuro.

Não implementar módulos de negócio.

---

# 1. Objetivo arquitetural

O TechForge deverá funcionar como uma plataforma composta por um Core e extensões.

Modelo conceitual:

```text
TechForge
│
├── Core
│   ├── App Shell
│   ├── Configuration
│   ├── Logging
│   ├── Database
│   ├── Module Infrastructure
│   ├── Runtime Foundation
│   └── Documentation Foundation
│
└── Modules
    ├── Application Modules
    └── Service Modules
```

Nesta fase, criar apenas a fundação e os contratos internos.

Não implementar ainda a instalação, ativação ou execução dinâmica completa de módulos.

---

# 2. Regra fundamental: Core mínimo

O Core não deve crescer proporcionalmente ao número de módulos.

Adicionar um novo módulo não deve exigir alterações frequentes em:

- rotas principais;
- menus fixos;
- código do Dashboard;
- banco do Core;
- componentes centrais.

Toda regra de negócio deve permanecer fora do Core.

Exemplos que **não pertencem ao Core**:

- cálculo de sizing Veeam;
- consulta à AWS;
- Health Check VMware;
- cálculo de capacidade;
- integração Salesforce.

---

# 3. Definir componentes oficiais do Core

Estabelecer interfaces e responsabilidades claras para:

```text
App Shell
Configuration
Logging
Database
Module Registry Foundation
Module Loader Foundation
Package Manager Foundation
Runtime Foundation
Documentation Foundation
Notification Foundation
```

Nesta fase, algumas dessas estruturas poderão ser apenas interfaces ou implementações mínimas.

Não criar implementações falsas ou complexidade desnecessária.

---

# 4. App Shell

Consolidar o App Shell como estrutura principal da interface.

Responsabilidades:

- layout principal;
- área de navegação;
- área de conteúdo;
- roteamento;
- identidade visual;
- futura integração com módulos.

O App Shell não deve conhecer regras de negócio dos módulos.

A interface deve permitir:

- menus retráteis;
- ocultação da navegação;
- maior uso da área de conteúdo;
- módulos ocupando a área principal.

Conceito:

```text
┌───────────────────────────────────────────────┐
│ Top Bar                                      │
├──────────────┬────────────────────────────────┤
│              │                                │
│ Navigation   │      Module / Core Content     │
│              │                                │
│              │                                │
└──────────────┴────────────────────────────────┘
```

A navegação poderá ser recolhida para aumentar a área disponível aos módulos.

---

# 5. Core API boundaries

Organizar as APIs do Backend de forma que funcionalidades do Core sejam claramente separadas de futuras APIs de módulos.

Exemplo conceitual:

```text
/api/
├── health
├── platform
├── modules
├── runtime
├── notifications
└── docs
```

Não implementar APIs de módulos de negócio.

Definir convenções para evitar conflitos futuros de rotas.

---

# 6. Module Registry Foundation

Criar a fundação do Module Registry.

Responsabilidade futura:

- conhecer módulos;
- armazenar metadados;
- informar status;
- fornecer informações para navegação;
- fornecer informações para o Marketplace;
- identificar versões e compatibilidade.

Nesta fase, definir:

- interface;
- modelo de dados;
- contratos;
- fluxo básico de registro.

O Registry não deve depender de módulos de negócio.

O Registry não deve conter lógica específica de Veeam, VMware, AWS ou Salesforce.

Preparar o Registry para futuras informações como:

```text
id
name
version
description
category
vendor
module_type
status
compatibility
dependencies
documentation
```

---

# 7. Module metadata model

Definir um modelo consistente de metadados para módulos.

Esse modelo será futuramente alimentado pelo `manifest.yaml`.

Campos conceituais:

```text
module_id
name
version
description
category
vendor
module_type
status
core_compatibility
dependencies
documentation
```

Nesta fase, não é necessário implementar todo o parser definitivo do manifesto.

Mas o modelo interno deve evitar mudanças incompatíveis futuras.

---

# 8. Package Manager Foundation

Criar uma abstração para o futuro gerenciamento de pacotes.

Responsabilidades futuras:

- instalar;
- validar;
- atualizar;
- desativar;
- remover;
- resolver dependências.

Nesta fase, definir interfaces e responsabilidades.

Não implementar ainda:

- download;
- Marketplace remoto;
- upload;
- assinaturas;
- resolução completa de dependências.

Importante:

O Package Manager será responsável pelo ciclo físico dos pacotes.

O Runtime e Registry não devem duplicar essa responsabilidade.

---

# 9. Runtime Foundation

Criar a fundação mínima do Runtime.

Responsabilidade futura:

- acompanhar o estado da plataforma;
- acompanhar módulos ativos;
- coordenar eventos de ciclo de vida;
- integrar Registry e Loader.

Nesta fase:

- definir estados;
- definir interfaces;
- preparar eventos internos simples.

Não implementar:

- Service Registry;
- execução dinâmica completa;
- dependências entre módulos;
- Hot Reload completo.

---

# 10. Notification Foundation

Criar uma estrutura simples de notificações do Core.

Futuramente poderá ser usada para:

- incompatibilidade;
- atualização;
- erro de módulo;
- validação;
- integridade;
- eventos da plataforma.

Nesta fase, evitar sistemas complexos.

A interface deve permitir:

```text
info
warning
error
success
```

A implementação deve ser reutilizável por fases futuras.

---

# 11. Configuration boundaries

Consolidar a configuração em uma única fonte lógica.

Evitar:

- valores duplicados;
- configurações no Frontend e Backend sem sincronização;
- portas espalhadas;
- caminhos de módulos hardcoded.

Preparar categorias como:

```text
Platform
Database
Runtime
Modules
Marketplace
Logging
```

Não criar configurações que ainda não possuem necessidade real.

---

# 12. Error boundaries

Estabelecer convenções de erro entre:

- Core;
- infraestrutura;
- APIs;
- futuras extensões.

Definir:

- classes ou categorias de erro;
- formato consistente de resposta;
- logging interno;
- mensagens seguras.

Não criar uma hierarquia excessivamente profunda.

---

# 13. Database ownership

Definir claramente a propriedade dos dados.

Regra arquitetural:

> O Core não deve possuir dados de negócio dos módulos.

O banco do Core deverá futuramente armazenar apenas dados necessários à plataforma, como:

- estado;
- metadados;
- Registry;
- notificações;
- configuração;
- histórico técnico.

Dados específicos de módulos deverão permanecer sob responsabilidade dos próprios módulos ou de serviços explicitamente definidos.

Não permitir que o Core se transforme em um banco central de regras de negócio.

---

# 14. Frontend architecture

Organizar o Frontend por responsabilidades.

Exemplo conceitual:

```text
src/
├── app/
├── core/
├── components/
├── pages/
├── services/
├── hooks/
├── types/
└── styles/
```

Não criar estruturas excessivas.

O objetivo é permitir que futuras áreas de módulos sejam integradas sem modificar indiscriminadamente componentes do Core.

---

# 15. Navigation architecture

Preparar a arquitetura para navegação dinâmica.

Regra:

> A interface não deverá depender permanentemente de uma lista fixa de módulos.

O Core poderá possuir itens fixos essenciais, como:

- Dashboard;
- Modules;
- Developer Center;
- Settings.

Módulos futuros deverão contribuir com navegação através de metadados, e não por alterações manuais em componentes centrais.

Nesta fase, apenas preparar os contratos necessários.

---

# 16. Versioning

Definir convenção oficial de versionamento.

Utilizar Semantic Versioning:

```text
MAJOR.MINOR.PATCH
```

Exemplo:

```text
1.0.0
```

Preparar o modelo para:

- versão do Core;
- versão de módulos;
- compatibilidade futura;
- evolução de contratos.

Não implementar ainda o resolvedor completo de versões.

---

# 17. Compatibility foundation

Preparar contratos para futura validação de compatibilidade.

Exemplo conceitual:

```text
requires:
  techforge: ">=1.0.0,<2.0.0"
```

Nesta fase:

- definir modelo;
- validar sintaxe básica, se apropriado;
- documentar convenção.

Não implementar ainda todo o mecanismo de dependências.

---

# 18. Documentation

Atualizar a documentação da arquitetura.

Criar ou consolidar:

```text
docs/architecture/
├── core.md
├── app-shell.md
├── module-boundaries.md
├── data-ownership.md
├── versioning.md
└── compatibility.md
```

Documentar claramente:

- responsabilidades;
- limites do Core;
- limites dos módulos;
- propriedade de dados;
- contratos arquiteturais.

Aplicar o princípio Documentation First.

---

# 19. Testes

Criar testes para as estruturas implementadas nesta fase.

Cobrir pelo menos:

- modelos do Core;
- contratos;
- configuração;
- Registry Foundation;
- Runtime Foundation;
- Notification Foundation;
- versionamento básico;
- limites de dados quando aplicável.

Não criar testes artificiais apenas para atingir números de cobertura.

---

# 20. O que não implementar

Não implementar nesta fase:

- módulos de negócio;
- Marketplace completo;
- instalação de módulos;
- upload de módulos;
- Service Registry completo;
- Dependency Governance;
- Launcher;
- assinaturas digitais;
- autenticação avançada;
- IA;
- geração automática de módulos.

---

# 21. Critérios de aceitação

A fase será concluída quando:

1. As responsabilidades do Core estiverem claramente definidas.
2. O App Shell estiver consolidado.
3. A arquitetura de navegação estiver preparada para crescimento.
4. A fundação do Module Registry existir.
5. A fundação do Package Manager existir.
6. A fundação do Runtime existir.
7. Os limites entre Core e módulos estiverem documentados.
8. O modelo de metadados estiver definido.
9. A convenção de versionamento estiver definida.
10. A base de compatibilidade futura estiver preparada.
11. O Core não possuir lógica de negócio.
12. A documentação arquitetural estiver atualizada.
13. Testes relevantes estiverem funcionando.
14. Nenhuma funcionalidade da Fase 1 for quebrada.

---

# Regra final

Antes de finalizar:

- revisar a arquitetura existente;
- remover duplicações desnecessárias;
- executar todos os testes;
- executar o Backend;
- executar o Frontend;
- validar o App Shell;
- validar os contratos internos;
- validar a documentação.

Apresentar ao final:

```text
Architecture:
Core Boundaries:
App Shell:
Registry Foundation:
Runtime Foundation:
Tests:
Build:
Known Issues:
```

Não avançar para a implementação completa do sistema de módulos nesta fase.
