---
title: Hello World — Exemplo de Integração
order: 3
tags: [hello-world, integration, example, cross-module]
---

## Objetivo

Demonstrar como **outro módulo** pode consumir o serviço `hello_world` como dependência, validando o padrão de integração entre módulos.

## Entradas

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `base_url` | str | sim | URL base da API do Core |

## Saídas

`dict` com a resposta do endpoint consumido, ou `None` se o serviço estiver indisponível.

## Exemplo

```python
"""
my_consumer_module/backend/main.py
====================================
Módulo que depende de hello_world como referência de integração.
"""
import httpx
from techforge_sdk import create_sdk

sdk = create_sdk("my_consumer_module")


async def check_dependency_health(base_url: str = "http://127.0.0.1:8000") -> dict | None:
    """
    Verifica se o serviço hello_world está saudável antes de prosseguir.
    Padrão de integração: sempre validar dependências antes de executar lógica própria.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{base_url}/api/v1/modules/hello_world/ping")
            resp.raise_for_status()
            data = resp.json()
            sdk.logger.info("Dependency hello_world is healthy: %s", data)
            return data
    except httpx.HTTPError as exc:
        sdk.logger.error("Dependency hello_world unreachable: %s", exc)
        return None


async def my_module_main_logic():
    dependency_status = await check_dependency_health()
    if dependency_status is None:
        sdk.logger.warning("Proceeding without hello_world — degraded mode.")
        return {"status": "degraded"}

    return {"status": "ok", "dependency": dependency_status}
```

## Declarando a dependência no manifesto

```yaml
# my_consumer_module/manifest.yaml
id: my_consumer_module
name: My Consumer Module
# ...
```

```yaml
# my_consumer_module/docs/contracts/api.yaml
service_id: my_consumer_module
dependencies:
  - hello_world
exports: []
```

## Observações

- Em produção, prefira chamadas internas (in-process) em vez de HTTP quando ambos os módulos rodam no mesmo processo — esta é uma simplificação didática.
- Declare sempre a dependência em `dependencies` no `api.yaml` para que o Documentation Engine e futuras versões do Package Manager possam resolver a ordem de carregamento.
- Trate timeouts e indisponibilidade graciosamente — nunca assuma que outro módulo estará sempre disponível.
