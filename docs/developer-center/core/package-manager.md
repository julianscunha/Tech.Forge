---
title: Package Manager
category: arquitetura-core
domain: [arquitetura-core]
tags: [package-manager, install, update, remove, hot-reload, mod-file]
order: 4
---

# Package Manager

O Package Manager é o único componente autorizado a escrever em `modules/installed/`. Todos os outros componentes interagem com módulos exclusivamente através dele.

> Esta página é a visão geral. Para estrutura de diretórios, repository
> providers e detalhes internos de implementação, veja
> [Package Manager — Internals](package-manager-internals.md).

## Operações

### Instalar

```
PackageManager.install(mod_path)
  ↓ Valida o arquivo .mod (ZIP válido)
  ↓ Extrai e valida manifest.yaml
  ↓ Verifica compatibilidade de versão
  ↓ Verifica duplicação
  ↓ Extrai para modules/installed/<module_id>/
  ↓ Hot-reload do registry
  ↓ Registra no OperationLog
```

### Remover

```
PackageManager.remove(module_id)
  ↓ Deregistra do registry
  ↓ Deleta modules/installed/<module_id>/
  ↓ Hot-reload do registry
  ↓ Registra no OperationLog
```

### Atualizar

```
PackageManager.update(module_id, mod_path)
  ↓ Verifica que nova versão > versão instalada
  ↓ Verifica compatibilidade
  ↓ Backup em modules/cache/<id>-<old_version>.bak
  ↓ Substitui arquivos
  ↓ Hot-reload do registry
  ↓ Registra no OperationLog
```

## Formato .mod

```
meu_modulo-1.0.0.mod   (ZIP estruturado)
├── manifest.yaml
├── backend/main.py
├── frontend/index.tsx
├── assets/
├── docs/
├── tests/
└── META-INF/
    ├── TECHFORGE      ← formato e versão mínima
    └── BUILD          ← module_id, version, built_at
```

## API REST

```
GET    /api/v1/marketplace/installed
GET    /api/v1/marketplace/available
GET    /api/v1/marketplace/updates
POST   /api/v1/marketplace/install/{id}
DELETE /api/v1/marketplace/remove/{id}
POST   /api/v1/marketplace/update/{id}
POST   /api/v1/marketplace/import       ← upload manual de .mod
GET    /api/v1/marketplace/log
```

## Compatibilidade

| Resultado | Condição |
|-----------|----------|
| `COMPATIBLE` | platform_version dentro do range |
| `WARNING` | mesmo major, minor próximo ao limite |
| `INCOMPATIBLE` | fora do range — instalação bloqueada |
