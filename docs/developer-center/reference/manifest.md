---
title: Referência do Manifesto
order: 1
tags: [manifest, yaml, reference, icon, order, color, required-fields]
---

# Referência do Manifesto (manifest.yaml)

O `manifest.yaml` é o contrato declarativo de um módulo TechForge. Ele define identidade, compatibilidade, metadados de navegação e pontos de entrada.

## Exemplo completo

```yaml
id: my_module
name: My Module
version: 1.0.0

platform_min_version: 1.0.0
platform_max_version: 2.0.0

category: Backup
vendor: Acme Corp
author: Dev Team
description: Descrição clara do que o módulo faz.

# Navegação e apresentação (obrigatórios — §7.1)
icon: shield-check
order: 10
color: blue

entry_backend: backend/main.py
entry_frontend: frontend/index.tsx

homepage: https://example.com
documentation: https://docs.example.com

# Segurança — Fase 5
signature:
checksum:
```

## Campos obrigatórios

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | string | Identificador único. `snake_case`, 2–64 chars. |
| `name` | string | Nome de exibição. |
| `version` | string | Versão semver `X.Y.Z`. |
| `category` | string | Categoria para agrupamento na Sidebar. |
| `vendor` | string | Empresa ou autor do módulo. |
| `author` | string | Nome do desenvolvedor. |
| `description` | string | Descrição de uma linha. |
| `entry_backend` | path | Caminho para `backend/main.py`. |
| `entry_frontend` | path | Caminho para `frontend/index.tsx`. |
| `icon` | string | Nome do ícone lucide-react em **kebab-case**. Ex: `shield-check`. |
| `order` | int | Posição na Sidebar dentro do grupo category/vendor. Menor = primeiro. |

## Campos opcionais

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `color` | string | Cor de destaque. Valores: `blue`, `green`, `red`, `yellow`, `orange`, `purple`, `pink`, `cyan`, `teal`, `indigo`, `gray`. |
| `platform_min_version` | string | Versão mínima da plataforma. Default: `0.0.0`. |
| `platform_max_version` | string | Versão máxima da plataforma. Default: `999.999.999`. |
| `module_type` | string | `application` (padrão) ou `service`. Módulos `service` exigem contrato completo e os 3 tiers de exemplo — ver [§16 Documentation First Principle](/developer-center/governance/documentation-first-principle). |
| `homepage` | URL | Site do módulo. |
| `documentation` | URL | Documentação externa. |
| `signature` | string | Assinatura digital (Fase 5). |
| `checksum` | string | Checksum SHA-256 (Fase 5). |

## Ícones disponíveis

O campo `icon` deve ser um nome de ícone do [Lucide React](https://lucide.dev/icons) em **kebab-case**:

```
shield-check  database    cloud        server
hard-drive    activity    bar-chart    box
cpu           globe        layers      lock
monitor       network     package      zap
file-text     folder      search       terminal
wrench        alert-circle archive     blocks
```

## Validação

```bash
techforge validate-module .
```

O validador verifica todos os campos obrigatórios, formatos e compatibilidade.
