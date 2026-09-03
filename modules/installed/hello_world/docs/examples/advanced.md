---
title: Hello World — Exemplo Avançado
order: 2
tags: [hello-world, advanced, example, lifecycle, settings]
---

## Objetivo

Demonstrar o uso completo do módulo `hello_world`: ciclo de vida completo, persistência de settings e o endpoint `info`.

## Entradas

| Operação | Entrada |
|---|---|
| `install()` | nenhuma |
| `info` | nenhuma |

## Saídas

```json
{
  "module_id": "hello_world",
  "name": "Hello World",
  "category": "Examples",
  "vendor": "TechForge",
  "sdk_version": "1.0.0",
  "description": "Reference module — architecture validation only."
}
```

## Exemplo

```python
from techforge_sdk import create_sdk
from backend.main import module  # HelloWorldModule instance

sdk = create_sdk("hello_world")

# 1. Instalar — idempotente, pode ser chamado múltiplas vezes
await module.install()
print(sdk.settings.get("install_count"))  # → 1 (incrementa a cada install)

# 2. Habilitar
await module.enable()

# 3. Verificar saúde
health = await module.health_check()
print(health.is_healthy, health.message)
# True "hello_world is healthy"
print(health.details)
# {"install_count": 1}

# 4. Consultar metadados via endpoint info
import httpx
async with httpx.AsyncClient() as client:
    resp = await client.get("http://127.0.0.1:8000/api/v1/modules/hello_world/info")
    print(resp.json())

# 5. Desabilitar (dados preservados)
await module.disable()

# 6. Atualizar (simulação)
await module.upgrade(from_version="0.9.0")
```

## Observações

- `sdk.settings.set()` persiste em `modules/installed/hello_world/data/settings.json`.
- O contador `install_count` demonstra que `install()` pode acumular estado entre chamadas.
- `disable()` **não** apaga settings — apenas `uninstall()` faz isso via `sdk.settings.reset()`.
- Use este padrão para módulos que precisam rastrear estado de configuração ao longo do tempo.
