---
title: Module Registry
category: arquitetura-core
domain: [arquitetura-core]
tags: [core, registry, module-engine, runtime]
order: 2
---

# Module Registry

O Module Registry é o armazenamento in-memory central de todos os módulos descobertos e carregados pelo Module Loader.

## Responsabilidades

- Armazenar estado runtime de cada módulo
- Ser a fonte de verdade para a navegação
- Ser acessível por qualquer parte da aplicação
- Suportar hot-reload após operações do Package Manager

## Estados possíveis

| Status | Descrição |
|--------|-----------|
| `INSTALLED` | Válido, compatível e ativo |
| `DISABLED` | Instalado mas desabilitado manualmente |
| `INVALID` | Manifest quebrado ou estrutura inválida |
| `INCOMPATIBLE` | Versão da plataforma fora do range declarado |

Apenas módulos com status `INSTALLED` aparecem na navegação.

## API Python

```python
from app.module_engine.registry import registry

# Leitura
registry.all()                            # list[ModuleEntry]
registry.get("my_module")                 # ModuleEntry | None
registry.by_status(ModuleStatus.INSTALLED)
registry.by_category("Backup")
registry.count_installed                  # int
registry.categories                       # list[str]

# Escrita (somente pelo ModuleLoader e PackageManager)
registry.register(entry)
registry.deregister("my_module")
registry.set_status("my_module", ModuleStatus.DISABLED)
```

## API REST

```
GET /api/v1/registry/modules              → lista todos os módulos
GET /api/v1/registry/modules/{id}         → detalhe de um módulo
GET /api/v1/registry/summary              → contadores agregados
GET /api/v1/registry/navigation           → árvore de navegação
GET /api/v1/registry/loader/journal       → log do último scan
```

## Hot Reload

Após qualquer operação do Package Manager, o ModuleLoader é chamado novamente:

```python
loader = ModuleLoader()
result = await loader.scan_installed()
loader_journal.store(result)
```

O registry é reconstruído sem reiniciar o processo.
