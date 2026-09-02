---
title: Ciclo de Vida dos Módulos
category: arquitetura-core
domain: [arquitetura-core]
tags: [lifecycle, install, enable, disable, upgrade, uninstall, contract]
order: 3
---

# Ciclo de Vida dos Módulos

Todo módulo TechForge deve implementar o contrato `ModuleContract`, que define
os hooks de ciclo de vida. **Nem todos são chamados pelo Core hoje** — ver
tabela abaixo antes do fluxo conceitual.

## Fluxo completo (conceitual)

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

## O que o Core realmente chama hoje

| Hook | Chamado pelo Core? | Quando |
|---|---|---|
| `enable()` | ✅ Sim | `POST /api/v1/marketplace/activate/{id}` |
| `disable()` | ✅ Sim | `POST /api/v1/marketplace/deactivate/{id}` |
| `health_check()` | ✅ Sim | `GET /api/v1/health`, sob demanda |
| `uninstall()` | ✅ Sim | `PackageManager.remove()` |
| `install()` | ❌ Não | Declarado no contrato, mas nenhum caminho de código do Core o invoca — `PackageManager.install()` extrai o pacote e atualiza o registry, sem chamar o hook do módulo |
| `upgrade(from_version)` | ❌ Não | Mesma situação — `PackageManager.update()` não invoca o hook |

Implemente `install()`/`upgrade()` se quiser, mas não dependa deles rodando
automaticamente: hoje eles só existem no contrato do SDK.

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

O método `health_check()` é chamado sob demanda pelo Core, a cada requisição a `GET /api/v1/health` (não em background/periodicamente). Retorne `HealthResult.ok()` ou `HealthResult.fail()`:

```python
# Sucesso
return HealthResult.ok("Service running.", connections=3)

# Falha
return HealthResult.fail("Database unreachable.", code=503)
```

## Testar o lifecycle em dev sem empacotar um `.mod`

`ModuleLoader.scan_installed()` (rodado no boot) só monta o router do módulo — não chama `install()`/`enable()`/`health_check()`. O caminho oficial para exercitar os hooks reais durante o desenvolvimento é:

```bash
POST /api/v1/marketplace/activate/{module_id}     # chama enable()
POST /api/v1/marketplace/deactivate/{module_id}   # chama disable()
```

Isso evita empacotar um `.mod` só para validar que `enable()`/`disable()` fazem o que deveriam.
