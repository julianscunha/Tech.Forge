---
title: Exemplos — Hello World
order: 1
tags: [examples, hello-world, reference-module, walkthrough]
---

# Módulo de Referência: Hello World

O módulo `hello_world` é o exemplo oficial que valida toda a arquitetura da plataforma. Ele não implementa lógica real — serve exclusivamente como referência.

## O que ele demonstra

- Manifest completo com todos os campos obrigatórios (incluindo `icon` e `order`)
- Implementação completa de `ModuleContract` com todos os hooks
- Router FastAPI exportado para o Plugin Loader
- Frontend com `moduleConfig` e componente padrão
- Uso correto do SDK: `create_sdk()`, `sdk.logger`, `sdk.settings`
- Estrutura de diretórios conforme a especificação

## Manifest

```yaml
id: hello_world
name: Hello World
version: 1.0.0
platform_min_version: 1.0.0
platform_max_version: 2.0.0

category: Examples
vendor: TechForge
author: TechForge Team
description: Módulo de referência para validação da arquitetura.

icon: blocks
order: 99
color: blue

entry_backend: backend/main.py
entry_frontend: frontend/index.tsx
```

## Backend

```python
from techforge_sdk import create_sdk
from techforge_sdk.contracts import ModuleContract, ModuleMetadata, HealthResult

sdk = create_sdk("hello_world")
router = APIRouter(prefix="/modules/hello_world", tags=["hello_world"])

@router.get("/ping")
async def ping():
    return {"module": "hello_world", "status": "ok"}

class HelloWorldModule(ModuleContract):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(id="hello_world", name="Hello World", ...)

    async def install(self) -> None:
        sdk.settings.set("installed", True)

    async def health_check(self) -> HealthResult:
        return HealthResult.ok("hello_world is healthy.")

module = HelloWorldModule()
```

## Frontend

```tsx
export const moduleConfig: ModulePageConfig = {
  moduleId: "hello_world",
  title:    "Hello World",
  icon:     "blocks",
  category: "Examples",
  vendor:   "TechForge",
  route:    "/modules/hello_world",
}

export default function HelloWorldPage() {
  return (
    <div className="p-8">
      <h2>Hello World</h2>
      <p>Módulo de referência — arquitetura validada.</p>
    </div>
  )
}
```

## Validar com a CLI

```bash
cd modules/installed/hello_world
techforge validate-module .
# → 20/20 checks passed ✓
```

## Usar como template

```bash
cp -r modules/installed/hello_world/ modules/installed/meu_modulo/
# Edite manifest.yaml, backend/main.py e frontend/index.tsx
techforge validate-module meu_modulo/
```
