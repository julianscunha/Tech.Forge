---
title: Hello World — Overview
order: 1
tags: [hello-world, reference, examples, architecture-validation]
---

# Hello World

**Category:** Examples  
**Vendor:** TechForge  
**Version:** 1.0.0

## Descrição

Módulo de referência oficial da plataforma TechForge. Valida a arquitetura de plugins sem implementar nenhuma lógica de negócio.

## O que valida

- Manifest completo com campos `icon` e `order` obrigatórios
- Estrutura de diretórios conforme especificação
- Implementação de `ModuleContract` com todos os hooks de ciclo de vida
- Router FastAPI exportado para o Plugin Loader
- Frontend com `moduleConfig` e export padrão React
- Uso correto do SDK: `create_sdk()`, `sdk.logger`, `sdk.settings`
- Aparência no registry com status `INSTALLED`
- Renderização na Sidebar com ícone `blocks` e cor `blue`

## Endpoints

```
GET /api/v1/modules/hello_world/ping
GET /api/v1/modules/hello_world/info
```

## Como usar como template

```bash
# Copie e renomeie
cp -r modules/installed/hello_world/ modules/installed/meu_modulo/

# Edite o manifest
vim meu_modulo/manifest.yaml

# Valide
techforge validate-module meu_modulo/
```
