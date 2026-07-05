---
title: SDK Backend
order: 1
tags: [sdk, python, database, storage, logger, settings, notifications]
---

# SDK Backend (Python)

O SDK Backend oferece serviços isolados para os backends dos módulos. Importe sempre via `create_sdk()` para obter uma instância com escopo correto.

```python
from techforge_sdk import create_sdk

sdk = create_sdk("my_module")
```

## sdk.logger

Logger estruturado prefixado com o `module_id`.

```python
sdk.logger.debug("Detalhe técnico")
sdk.logger.info("Processamento iniciado", job_id=42)
sdk.logger.warning("Rate limit próximo", remaining=10)
sdk.logger.error("Falha na API externa", url="https://api.example.com")
sdk.logger.exception("Erro não esperado")
```

## sdk.settings

Configurações persistidas por módulo em `modules/installed/<id>/data/settings.json`.

```python
# Escrita
sdk.settings.set("api_url", "https://api.example.com")
sdk.settings.set("max_retries", 3)

# Leitura
url = sdk.settings.get("api_url", default="https://default.com")

# Listar / limpar
all_cfg = sdk.settings.all()
sdk.settings.delete("deprecated_key")
sdk.settings.reset()   # limpa tudo (use em uninstall())
```

## sdk.storage

Armazenamento de arquivos isolado em `modules/installed/<id>/data/`.

```python
# Escrita
sdk.storage.write("config.json", b'{"key": "value"}')
sdk.storage.write_text("output.csv", csv_content)

# Leitura
data  = sdk.storage.read("config.json")
text  = sdk.storage.read_text("output.csv")

# Listagem e existência
files = sdk.storage.list("exports/")
if sdk.storage.exists("config.json"):
    sdk.storage.delete("config.json")
```

> **Segurança:** Tentativas de path traversal (`../../etc/passwd`) são bloqueadas com `PermissionError`.

## sdk.database

Acesso SQL isolado por módulo.

```python
# SELECT
rows = await sdk.database.fetch_all(
    "SELECT * FROM jobs WHERE active = ?", [True]
)
row = await sdk.database.fetch_one(
    "SELECT * FROM jobs WHERE id = ?", [job_id]
)

# INSERT / UPDATE / DELETE
await sdk.database.execute(
    "INSERT INTO jobs (name, status) VALUES (?, ?)",
    ["nightly", "pending"]
)
await sdk.database.execute_many(
    "INSERT INTO items (name) VALUES (?)",
    [["item_a"], ["item_b"]]
)
```

## sdk.notifications

Enfileira notificações para exibir na interface.

```python
sdk.notifications.push(
    title="Backup Concluído",
    message="3 VMs processadas em 4m 12s.",
    level="success",    # info | success | warning | error
)

# Verificar pendentes
pending = sdk.notifications.pending()
sdk.notifications.mark_read(notification_id)
```
