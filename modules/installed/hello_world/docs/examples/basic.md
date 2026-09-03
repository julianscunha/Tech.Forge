---
title: Hello World — Exemplo Básico
order: 1
tags: [hello-world, basic, example]
---

## Objetivo

Demonstrar o uso mínimo do módulo `hello_world`: verificar que ele está instalado e respondendo.

## Entradas

Nenhuma. O endpoint `ping` não recebe parâmetros.

## Saídas

```json
{
  "module": "hello_world",
  "status": "ok",
  "version": "1.0.0"
}
```

## Exemplo

```bash
curl http://127.0.0.1:8000/api/v1/modules/hello_world/ping
```

```python
import httpx

async def check_hello_world():
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://127.0.0.1:8000/api/v1/modules/hello_world/ping")
        return resp.json()

result = await check_hello_world()
print(result)
# {"module": "hello_world", "status": "ok", "version": "1.0.0"}
```

## Observações

- Este é o caso de uso mais simples do SDK — apenas health check.
- Não requer autenticação nem configuração prévia.
- Use este padrão como ponto de partida para o `health_check()` do seu próprio módulo.
