---
title: Referência do Manifesto
category: sdk-desenvolvimento
domain: [sdk-desenvolvimento]
tags: [manifest, yaml, reference, icon, order, color, required-fields]
order: 1
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

# Navegação e apresentação (obrigatórios)
icon: shield-check
order: 10
color: blue

entry_backend: backend/main.py
entry_frontend: frontend/index.js

module_type: application
channel: stable

homepage: https://example.com
documentation: https://docs.example.com

# checksum é preenchido automaticamente ao empacotar/publicar.
# signature ainda não é gerada automaticamente — ver seção "Campos opcionais".
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
| `entry_frontend` | path | Caminho para o JS compilado (ESM), ex. `frontend/index.js`. **Não** um `.tsx`/`.ts` cru — o Core só serve/importa `.js`/`.mjs` (`ModuleHost` rejeita silenciosamente qualquer outra extensão). |
| `icon` | string | Nome do ícone lucide-react em **kebab-case**. Ex: `shield-check`. |
| `order` | int | Posição na Sidebar dentro do grupo category/vendor. Menor = primeiro. |

## Campos opcionais

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `color` | string | Cor de destaque. Valores: `blue`, `green`, `red`, `yellow`, `orange`, `purple`, `pink`, `cyan`, `teal`, `indigo`, `gray`. |
| `platform_min_version` | string | Versão mínima da plataforma. Default: `0.0.0`. |
| `platform_max_version` | string | Versão máxima da plataforma. Default: `999.999.999`. |
| `module_type` | string | `application` (padrão) ou `service`. Módulos `service` exigem contrato completo e os 3 tiers de exemplo — ver [Documentation First Principle](/developer-center/governance/documentation-first-principle). |
| `channel` | string | Canal de pre-release: `stable` (padrão), `beta` ou `development`. |
| `homepage` | URL | Site do módulo. |
| `documentation` | URL | Documentação externa. |
| `documentation.version` | string | Versão semver da documentação do módulo (bloco `documentation: {version, applies_to}` em vez de URL simples). |
| `documentation.applies_to` | mapping | Faixa de compatibilidade da documentação, ex. `techforge: ">=1.0.0,<2.0.0"`. |
| `dependencies` | list | Dependências de outros módulos instalados — ver Dependency Governance. |
| `configuration.fields` | list | Campos de configuração expostos na UI do módulo (`id`, `type`: `string`\|`integer`\|`float`\|`boolean`, `default`). |
| `source_type` | string | Origem do módulo: `local` (padrão), `catalog` ou `development`. Preenchido pelo Core, normalmente não editado à mão. |
| `source_location` | string | Localização de origem quando `source_type` não é `local`. Preenchido pelo Core. |
| `signature` | string | Assinatura digital do publisher. **Ainda não implementada** — nenhum caminho de produção (`package-module`, install, publish) a preenche hoje; ver [Package Manager — Internals](../core/package-manager-internals.md#3-formato-do-arquivo-mod). |
| `checksum` | string | Checksum SHA-256 do `.mod`, preenchido automaticamente por `techforge package-module`. |

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
