---
title: Ciclo de Vida dos Módulos
category: arquitetura-core
domain: [arquitetura-core]
tags: [lifecycle, install, enable, disable, upgrade, uninstall, contract]
order: 3
---

# Ciclo de Vida dos Módulos

Todo módulo TechForge deve implementar o contrato `ModuleContract` que define os hooks de ciclo de vida chamados pelo Core.

## Fluxo completo

```
install()   ← chamado uma vez na primeira instalação
    ↓
enable()    ← chamado ao habilitar (após install ou após disable)
    ↓
[em uso]    ← módulo está ativo e disponível
    ↓
disable()   ← chamado ao desabilitar (dados preservados)
    ↓
upgrade(v)  ← chamado ao atualizar (from_version como parâmetro)
    ↓
uninstall() ← chamado ao remover permanentemente
```

## Implementação

```python
from techforge_sdk import create_sdk
from techforge_sdk.contracts import ModuleContract, ModuleMetadata, HealthResult

sdk = create_sdk("my_module")

class MyModule(ModuleContract):

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="my_module",
            name="My Module",
            version="1.0.0",
            category="Backup",
            vendor="Acme",
            author="Dev Team",
            description="Does useful things.",
        )

    async def install(self) -> None:
        sdk.logger.info("Installing my_module...")
        sdk.settings.set("configured", False)

    async def enable(self) -> None:
        sdk.logger.info("my_module enabled.")

    async def disable(self) -> None:
        sdk.logger.info("my_module disabled.")

    async def upgrade(self, from_version: str) -> None:
        sdk.logger.info("Upgrading from %s", from_version)

    async def health_check(self) -> HealthResult:
        return HealthResult.ok("All systems nominal.")

    async def uninstall(self) -> None:
        sdk.settings.reset()
        sdk.logger.info("my_module uninstalled.")

module = MyModule()
```

## health_check()

O método `health_check()` é chamado periodicamente pelo Core. Retorne `HealthResult.ok()` ou `HealthResult.fail()`:

```python
# Sucesso
return HealthResult.ok("Service running.", connections=3)

# Falha
return HealthResult.fail("Database unreachable.", code=503)
```
