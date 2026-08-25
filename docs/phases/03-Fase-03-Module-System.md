---
title: TechForge — Fase 3
category: fases
domain: [fases]
---

# TechForge — Fase 3
## Module System

> **Status:** Prompt de implementação consolidado
>
> **Objetivo:** Implementar o sistema oficial de módulos do TechForge, permitindo descoberta, validação, carregamento e integração estrutural de módulos sem ainda implementar Marketplace remoto, dependências avançadas ou Service Registry.

---

# 1. Contexto

As fases anteriores estabeleceram:

- Foundation;
- Core mínimo;
- App Shell;
- Module Registry Foundation;
- Module Loader Foundation;
- Package Manager Foundation;
- Runtime Foundation;
- limites entre Core e módulos;
- convenções de versionamento e compatibilidade.

Nesta fase, transformar essas fundações em um sistema real de módulos.

O TechForge deve ser projetado para crescer por módulos.

Exemplos futuros:

```text
Backup
└── Veeam
    ├── M365 Sizing
    └── Salesforce Sizing

Virtualização
└── VMware
    └── Health Check

Cloud
└── AWS
    ├── Cost Service
    └── Sizing
```

Não desenvolver funcionalidades específicas desses módulos nesta fase.

O objetivo é construir o mecanismo que permitirá que eles existam.

---

# 2. Princípio principal

Um módulo deve conseguir ser desenvolvido, adicionado e integrado ao TechForge sem exigir alteração manual do Core.

O fluxo desejado é:

```text
Módulo
   ↓
Manifest
   ↓
Discovery
   ↓
Validation
   ↓
Registration
   ↓
Load
   ↓
Navigation / Runtime
```

O Core deve descobrir módulos por metadados.

Não criar listas hardcoded de módulos.

---

# 3. Tipos oficiais de módulo

Definir dois tipos iniciais:

## Application Module

Módulo com interface e funcionalidade diretamente utilizada pelo usuário.

Exemplos futuros:

- Veeam M365 Sizing;
- VMware Health Check;
- Lead Analyzer.

Características:

- pode possuir interface;
- pode contribuir para navegação;
- pode consumir serviços;
- não deve ser utilizado como dependência direta por outros módulos através de acesso interno.

## Service Module

Módulo que fornece capacidades reutilizáveis para outros módulos.

Exemplos futuros:

- AWS API Connector;
- VMware API Connector;
- Inventory Service;
- Cost Service.

Características:

- pode não possuir interface funcional tradicional;
- publica contratos;
- fornece capacidades reutilizáveis;
- poderá ser consumido através do SDK e Service Registry;
- não deve depender de Application Modules.

Nesta fase, preparar o tipo `service`, mas não implementar ainda o Service Registry completo.

---

# 4. Estrutura oficial do módulo

Definir uma estrutura padrão.

Exemplo:

```text
module/
├── manifest.yaml
├── README.md
│
├── backend/
│   └── ...
│
├── frontend/
│   └── ...
│
├── docs/
│   └── ...
│
├── tests/
│   └── ...
│
└── assets/
    └── ...
```

A estrutura pode variar internamente, desde que o contrato externo seja preservado.

Campos obrigatórios devem ser encontrados de forma previsível.

---

# 5. Manifest

O `manifest.yaml` é a fonte oficial de metadados do módulo.

Definir formato inicial contendo pelo menos:

```yaml
id: example_module
name: Example Module
version: 1.0.0
description: Example description
category: Example
vendor: TechForge
module_type: application

compatibility:
  techforge: ">=1.0.0,<2.0.0"
```

Preparar suporte para futura expansão com:

- dependencies;
- optional_dependencies;
- navigation;
- exports;
- documentation;
- signature;
- permissions.

Não exigir todos esses campos nesta fase se ainda não forem utilizados.

---

# 6. Identidade do módulo

O `id` do módulo deve ser:

- único;
- estável;
- utilizado internamente;
- independente do nome visual.

Exemplo:

```text
veeam_m365_sizing
```

O nome visual poderá ser:

```text
Veeam M365 Sizing
```

Não utilizar o nome visual como chave interna.

---

# 7. Module Discovery

Implementar descoberta automática de módulos.

Inicialmente, o sistema deve procurar módulos em um diretório configurável.

Exemplo:

```text
modules/
```

Cada diretório encontrado deverá ser avaliado.

Fluxo:

```text
Directory
   ↓
manifest.yaml found?
   ↓
Parse
   ↓
Validate
   ↓
Compatible?
   ↓
Register
```

Módulos inválidos não devem derrubar o TechForge.

Registrar erro e continuar carregando os demais módulos.

---

# 8. Module Validation

Implementar validação estrutural básica.

Validar pelo menos:

- manifest presente;
- YAML válido;
- id presente;
- nome presente;
- versão válida;
- module_type válido;
- compatibilidade presente;
- id único.

Se um módulo falhar:

```text
INVALID
```

Ele não deve ser carregado.

O erro deve ficar disponível para diagnóstico.

---

# 9. Module Registry

Transformar a fundação anterior em um Registry funcional.

Responsabilidades:

- armazenar módulos descobertos;
- fornecer metadados;
- informar status;
- impedir duplicação;
- informar erros de validação.

Estados iniciais:

```text
DISCOVERED
VALIDATED
INVALID
REGISTERED
FAILED
```

Não implementar ainda:

- ENABLED;
- DISABLED;
- DEPRECATED;
- dependency resolution completo.

Esses estados serão expandidos posteriormente pelo Module Lifecycle Manager.

---

# 10. Module Loader

Implementar o Module Loader responsável por carregar módulos válidos.

O Loader deve:

- receber módulo validado;
- preparar o módulo para uso;
- integrar contribuições permitidas;
- registrar falhas.

Não permitir que um módulo altere diretamente o Core.

Toda integração deve ocorrer através de contratos definidos.

---

# 11. Frontend module integration

Preparar módulos Application para renderizar dentro do TechForge.

Requisito crítico:

> Um módulo deve abrir dentro da área principal do TechForge, e não em uma nova aba ou aplicação externa.

Modelo:

```text
TechForge App Shell
│
├── Navigation
│
└── Content Area
       │
       └── Module UI
```

A navegação deve poder ser recolhida/ocultada para maximizar a área do módulo.

O módulo não deve recriar:

- App Shell;
- Top Bar;
- navegação global.

O módulo deve fornecer seu conteúdo para a área do Core.

---

# 12. Navegação declarativa

Preparar o manifesto para futura contribuição de navegação.

Exemplo conceitual:

```yaml
navigation:
  category:
    - Backup
    - Veeam
  label: M365 Sizing
  icon: calculator
```

A estrutura exata pode ser refinada.

O ponto obrigatório é:

> O módulo declara sua posição; o Core constrói a navegação.

Não exigir edição manual de menus centrais.

---

# 13. Categorias

Permitir organização hierárquica.

Exemplo:

```text
Backup
└── Veeam
    └── M365 Sizing

Virtualização
└── VMware
    └── Health Check
```

Categorias devem ser metadados.

Não criar uma enumeração fixa que obrigue alteração do Core para novas áreas.

---

# 14. Backend module boundaries

Preparar a integração Backend dos módulos.

Cada módulo pode possuir lógica Backend própria.

O módulo não deve:

- alterar diretamente tabelas internas do Core sem contrato;
- sobrescrever rotas do Core;
- acessar internamente outro módulo;
- importar diretamente código privado de outro módulo.

Definir convenções para namespaces.

Exemplo conceitual:

```text
/api/v1/modules/{module_id}/...
```

Ou outra solução consistente com a arquitetura existente.

---

# 15. Isolamento

Implementar isolamento lógico.

Nesta fase não é necessário:

- sandbox de containers;
- processos separados;
- isolamento de segurança pesado.

Mas um módulo deve ser tratado como unidade independente.

Falha em um módulo não deve impedir a plataforma inteira de iniciar.

Exemplo:

```text
Module A → READY
Module B → FAILED
Module C → READY
```

O TechForge continua operacional.

---

# 16. Módulo de exemplo

Criar um módulo de exemplo mínimo.

Objetivo:

- validar Discovery;
- validar Manifest;
- validar Registry;
- validar Loader;
- validar integração visual.

O módulo não deve conter lógica de negócio complexa.

Pode ser:

```text
Hello World
```

Mas deve utilizar o mesmo padrão que módulos reais utilizarão.

Não criar um caminho especial para o módulo de exemplo.

---

# 17. API do Core

Adicionar APIs básicas para módulos.

Exemplo:

```text
GET /api/v1/modules
GET /api/v1/modules/{module_id}
GET /api/v1/modules/{module_id}/status
```

Retornar:

- id;
- name;
- version;
- description;
- category;
- module_type;
- status;
- compatibility.

Não implementar ainda APIs de instalação/removal completas.

---

# 18. Frontend Modules Page

Criar uma página simples de módulos instalados/encontrados.

Exibir:

- nome;
- versão;
- categoria;
- tipo;
- status;
- erro, quando aplicável.

Não criar Marketplace completo nesta fase.

---

# 19. CLI

Preparar comandos básicos.

Exemplo:

```bash
techforge modules list
techforge modules show <module_id>
techforge modules validate
```

Os comandos devem reutilizar a mesma lógica do Core.

Não duplicar validações exclusivamente para CLI.

---

# 20. Configuração

Centralizar:

- diretório de módulos;
- módulos habilitados para discovery;
- opções de desenvolvimento.

Exemplo conceitual:

```text
MODULES_DIR=./modules
```

Não espalhar caminhos pelo código.

---

# 21. Documentação

Criar documentação oficial para o sistema de módulos.

Estrutura sugerida:

```text
docs/developer-center/modules/
├── overview.md
├── module-types.md
├── manifest.md
├── structure.md
├── navigation.md
└── lifecycle.md
```

Documentar:

- como criar módulo;
- estrutura;
- manifest;
- tipos;
- discovery;
- validação;
- integração visual;
- limites arquiteturais.

A documentação deve ser clara o suficiente para futuramente ser consumida também por IA.

---

# 22. Testes

Criar testes para:

- discovery;
- manifest parsing;
- YAML inválido;
- campos obrigatórios;
- versão inválida;
- módulo incompatível;
- IDs duplicados;
- Registry;
- Loader;
- falha isolada;
- API;
- CLI;
- integração visual básica.

Criar teste de integração:

```text
Module Directory
      ↓
Discovery
      ↓
Validation
      ↓
Registry
      ↓
Loader
      ↓
API
      ↓
UI
```

---

# 23. O que não implementar

Não implementar nesta fase:

- Marketplace remoto;
- download de módulos;
- upload de módulos;
- instalação por ZIP;
- atualização automática;
- remoção física;
- Service Registry;
- Dependency Governance;
- assinatura digital;
- Security Sandbox;
- Launcher;
- Runtime completo;
- documentação compliance automática.

---

# 24. Critérios de aceitação

A fase estará concluída quando:

1. O TechForge descobrir módulos automaticamente.
2. Todo módulo possuir `manifest.yaml`.
3. Manifestos inválidos não derrubarem a plataforma.
4. Módulos válidos forem registrados.
5. IDs duplicados forem rejeitados.
6. Módulos incompatíveis forem identificados.
7. Módulos puderem declarar tipo `application` ou `service`.
8. Application Modules puderem abrir dentro do App Shell.
9. Módulos não abrirem em novas abas.
10. Navegação futura puder ser declarada por metadados.
11. Falha em um módulo não derrubar outros.
12. APIs básicas funcionarem.
13. CLI básica funcionar.
14. O módulo de exemplo validar o fluxo completo.
15. Documentação estiver disponível.
16. O Core não receber lógica de negócio dos módulos.

---

# Regra final

Antes de finalizar:

- executar todos os testes existentes;
- executar novos testes;
- validar Discovery com múltiplos módulos;
- validar módulo inválido;
- validar módulo com erro;
- validar módulo incompatível;
- validar IDs duplicados;
- validar API;
- validar CLI;
- validar renderização interna do módulo;
- executar build do Frontend.

Apresentar ao final:

```text
Modules Discovered:
Modules Valid:
Modules Invalid:
Registry:
Loader:
API:
Frontend Integration:
CLI:
Tests:
Build:
Known Issues:
```

Não avançar para Marketplace, Package Manager, Service Registry ou Dependency Governance nesta fase.
