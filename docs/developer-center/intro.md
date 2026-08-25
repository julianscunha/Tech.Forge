---
title: Introdução ao TechForge
category: sdk-desenvolvimento
domain: [sdk-desenvolvimento]
tags: [intro, overview, getting-started]
order: 1
---

# Introdução ao TechForge

TechForge é uma plataforma corporativa modular para execução de ferramentas técnicas e comerciais via plugins. Ela permite que novas funcionalidades sejam adicionadas através de módulos independentes, sem necessidade de alterar o Core da aplicação.

## Filosofia da Plataforma

> **O módulo é o protagonista.** A plataforma ocupa o mínimo possível da interface — 95% da área útil é destinada aos módulos.

O Core é deliberadamente minimalista. Ele fornece:

- Navegação e App Shell
- Registry de módulos
- Package Manager
- SDK oficial
- Developer Center

O Core **não contém** regras de negócio de nenhum módulo.

## Como funciona

```
manifest.yaml         ← módulo declara seus metadados
       ↓
ModuleLoader          ← Core valida e registra ao iniciar
       ↓
ModuleRegistry        ← estado runtime de todos os módulos
       ↓
NavigationBuilder     ← Sidebar construída automaticamente
       ↓
Plugin Loader         ← frontend do módulo montado no App Shell
```

## Começando

Para criar seu primeiro módulo:

```bash
# 1. Instalar a CLI
cd cli && pip install -e .

# 2. Criar o scaffold
techforge create-module

# 3. Validar
techforge validate-module .

# 4. Empacotar
techforge package-module .

# 5. Instalar
cp -r meu_modulo/ modules/installed/
# Reiniciar o backend
```

## Estrutura do projeto

```
techforge/
├── core/         ← Core da plataforma (não modifique)
├── sdk/          ← SDK oficial para módulos
├── cli/          ← Ferramentas de desenvolvimento
├── modules/
│   ├── installed/    ← módulos ativos
│   └── repository/   ← pacotes .mod disponíveis
└── docs/         ← documentação
```
