---
title: Configuration, Data & Persistence
category: core-architecture
domain: [core]
---

# Configuration, Data & Persistence

> Storage abstraction, configuração de módulo tipada, Module Storage API,
> filesystem paths oficiais, Secret Store e migrations versionadas.

## Visão Geral

Este documento formaliza como o TechForge e seus módulos guardam dados e configuração,
mantendo a instalação Desktop leve (SQLite, arquivo único) sem impedir uma
migração futura para um Server multiusuário (PostgreSQL, configuração central).

**Fora de escopo, documentado — não implementado**:
PostgreSQL obrigatório, multiusuário completo, autenticação, RBAC, replicação,
cluster, backup corporativo, data warehouse.

---

## Storage Provider & Health

`app/db/storage.py::StorageProvider` — probe real de leitura e escrita no
banco (não apenas `SELECT 1`; testa `CREATE`/`DROP TEMP TABLE` também).

```
GET /api/v1/system/storage/status
```
```json
{ "database": true, "writable": true }
```

CLI: `techforge storage status`.

---

## Migrations — Alembic

Substitui a whitelist ad-hoc que existia em `app/db/database.py::_migrate()`.
`alembic` já era dependência declarada em `requirements.txt` desde antes desta
fase, mas nunca tinha sido configurado.

- **Core migrations**: `core/backend/alembic/` (revisões `0001`, `0002`, `0003`,
  ...). `env.py` é async (`async_engine_from_config` + `connection.run_sync`) e
  usa `settings.DATABASE_URL` como padrão, mas aceita override via
  `Config.set_main_option("sqlalchemy.url", ...)` (usado nos testes contra
  bancos temporários).
- **Module migrations**: não são geridas pelo Alembic do Core — o Core não deve
  conhecer schema de negócio de módulo (ver "Config migration" abaixo, para
  migração de *configuração*, que é diferente de schema de dados próprios do
  módulo).
- `init_db()` roda `Base.metadata.create_all()` (cria tabelas novas — idempotente)
  e depois `alembic upgrade head` **numa thread separada**
  (`asyncio.to_thread`) — Alembic faz `asyncio.run()` internamente em `env.py`,
  incompatível com um event loop já em execução.

```bash
techforge migrations status   # head vs. current
techforge migrations run      # upgrade head
```

`GET /api/v1/system/migrations/status` expõe o mesmo dado por HTTP (o CLI usa
acesso direto ao Python/SQLite de propósito — precisa funcionar mesmo com a
plataforma parada; o frontend só tem HTTP).

---

## Module Configuration

Manifesto declara um bloco opcional:

```yaml
configuration:
  fields:
    - id: retention_days
      type: integer
      default: 30
```

Tipos suportados: `string`, `integer`, `float`, `boolean` — **sem tipo lista/array**
por ora (limitação conhecida, ver [`docs/limitations.md`](../../limitations.md)).

Parseado e validado em `ManifestParser.parse()` (`app/module_engine/manifest.py`
— `ConfigField`, `parse_configuration_fields()`): campo sem `id`/`type`, tipo
desconhecido, ou `id` duplicado falham no *parse*, antes de o módulo sequer
carregar.

Persistência: 1 linha por módulo em `module_configurations` (`module_id` PK,
`values_json`) — não uma tabela por módulo. Validação via schema dinâmico
(`pydantic.create_model`, `app/services/module_configuration.py`) antes de
gravar; config inválida nunca persiste.

```
GET    /api/v1/modules/{id}/config              → valores atuais (defaults se nunca salvo)
PUT    /api/v1/modules/{id}/config               body: {"values": {...}}
POST   /api/v1/modules/{id}/config/validate       body: {"values": {...}}  — não persiste
```

CLI:
```bash
techforge modules config <id>                       # mostra
techforge modules config <id> --set retention_days=7  # salva
techforge modules config-validate <id> --set k=v      # valida sem salvar
```

Frontend: aparece dentro de **Module Details → Configuração** (painel lateral,
`ModuleDetailPanel.tsx` → `ModuleConfigSection.tsx`), não como página separada —
só renderiza se o manifesto declarar `configuration.fields`.

**No código do módulo**, os valores persistidos chegam via
`context.configuration` (dict já validado, defaults aplicados se nunca salvo):

```python
retention = context.configuration.get("retention_days", 30)
```

`ModuleExecutionContext.build()` ficou async justamente
para poder buscar essa config persistida antes de montar o contexto — antes
disso, `configuration` era sempre `{}` (stub nunca conectado).

---

## Config migration no update de módulo

Um módulo pode declarar um hook opcional no objeto `module` do seu
`entry_backend` (mesmo padrão de `enable`/`disable`/`health_check`):

```python
class MyModule:
    def migrate_config(self, old_version: str, old_config: dict) -> dict:
        # ex.: renomear campo entre versões
        return {"new_field": old_config.get("old_field")}

module = MyModule()
```

`PackageManager.update()` chama isso **depois** de extrair a versão nova,
**antes** de ativar (regenerar integrity manifest, hot-reload). Diferente dos
hooks de lifecycle (best-effort, nunca bloqueiam a transição), uma falha aqui
**é** um erro de update — reaproveita o mesmo rollback-por-exceção que já
existia para falha de extração: se `migrate_config()` levantar, retornar algo
que não seja `dict`, ou produzir uma config que não valide contra os novos
`configuration.fields`, o update inteiro é revertido (arquivos **e** config
voltam pra versão anterior — a config nova só é persistida depois que o hook
retorna com sucesso, então nunca fica meio-gravada).

Carrega a versão nova do `entry_backend` (já extraída) via `load_module_file()`
direto — nunca reusa o cache de instância do `module_runtime.lifecycle`, que
serve a versão *ativa* em runtime, não a versão que acabou de ser extraída.

---

## Module Storage API (key-value)

Para módulos que só precisam guardar dados simples, sem schema relacional
próprio — `context.storage` (`ModuleKVStorage`, `app/services/module_storage.py`):

```python
await context.storage.set("last_sync", {"at": "2026-01-01T00:00:00Z"})
value = await context.storage.get("last_sync", default=None)

async with context.storage.transaction() as tx:
    count = await tx.get("counter", default=0)
    await tx.set("counter", count + 1)
    # rollback automático se algo levantar dentro do bloco
```

**Isolamento estrutural, não por convenção**: `module_id` é fixado na
construção — nunca é parâmetro de `get`/`set`/`transaction`. Um módulo não tem
como ler ou escrever chave de outro módulo, mesmo por engano de programação
(desenho validado com a skill `api-and-interface-design` antes de implementar).

`set()` valida que o valor é serializável em JSON e nunca deixa vazar exceção
do SQLAlchemy/`json` pro código do módulo — levanta `ModuleStorageError` com
mensagem clara.

Tabela: `module_kv_store(module_id, key, value_json)`, chave primária composta.

Um módulo que precise de schema relacional próprio continua livre de usar
SQLAlchemy diretamente — o Core não impede, mas também não oferece uma API de
provisionamento assistida (ver [`docs/limitations.md`](../../limitations.md)).

---

## Filesystem Paths oficiais

`ModulePaths` (`app/module_runtime/paths.py`) substitui o `Path` solto que
`ModuleExecutionContext.paths` expunha antes:

```python
context.paths.root      # modules/installed/<id>/ — código + manifest
context.paths.data      # dados persistentes (nunca apagados em update)
context.paths.cache     # dados descartáveis, sem TTL garantido
context.paths.exports   # relatórios/CSV/XLSX/PDF gerados pelo módulo
context.paths.temp      # arquivos de vida curta de uma execução
```

`PackageManager.install()` cria os quatro diretórios (`ensure_exist()`) logo
após extrair o módulo. `cache/`, `exports/` e `temp/` entram na lista de
exclusão do hash de integridade (`app/module_trust/integrity.py`) —
são dados de runtime, não código do módulo; escrever neles depois da
instalação não marca o módulo como modificado.

---

## Secret Store

`context.secrets` (`ModuleSecretStore`, `app/security/secret_store.py`) usa o
cofre nativo do SO via a lib `keyring` (Windows Credential Manager, macOS
Keychain, Secret Service no Linux) por trás de uma abstração trocável
(`SecretStoreBackend`) — sem criptografia própria.

```python
context.secrets.set("api_key", "sk-...")           # cria (1a vez) ou sobrescreve
value = context.secrets.get("api_key")              # None se ausente
context.secrets.rotate("api_key", "sk-new-...")     # troca EXPLICITA de um valor existente
context.secrets.delete("api_key")
```

Mesmo isolamento estrutural do Module Storage API — `module_id` fixado na
construção. `rotate()` levanta `SecretStoreError` se a key nunca
foi criada. `set()`/`rotate()`/`delete()` publicam `security.secret_created`/
`security.secret_rotated`/`security.secret_deleted` no EventBus — nunca com
o valor do segredo no payload (ver `module-trust.md`).

**Redação em log** (`app/security/redaction.py::SecretRedactionFilter`): todo
valor já gravado via `SecretStore` que aparecer em qualquer mensagem de log,
mais qualquer campo de nome sensível (`password`, `token`, `api_key`,
`secret`, `private_key`, `credentials`, `authorization` — incluindo o header
`Authorization: Bearer xxx` inteiro) é substituído por `***REDACTED***`.
Instalado no **Handler** do logger raiz, não no **Logger** — um `Filter`
anexado a um `Logger` só roda quando aquele logger é o originador do
registro; registros propagados de loggers filhos (`techforge.module.*`) vão
direto pros Handlers dos ancestrais.

---

## Cache TTL genérico

`app/storage/cache.py::TTLCache[T]` — extraído do cache por-fonte que o
Catálogo já usava. Não é fonte única de verdade — expira e some.

```python
cache: TTLCache[list[Something]] = TTLCache(ttl_seconds=900)
cache.set("key", value)
cache.get("key")          # None se ausente ou TTL expirado
cache.invalidate("key")   # remove imediatamente, ignora TTL
```

---

## Data Portability

`GET /api/v1/config` — configuração de plataforma efetiva
(`settings.model_dump(mode="json")`). Como `settings.py` nunca guarda segredo
, ler e exportar são a mesma operação, sem endpoint `/export`
separado. `techforge config export` no CLI.

Export de configuração de módulo já é o próprio `GET /modules/{id}/config`
(reproduz os valores exatos salvos) — mesma lógica, sem endpoint duplicado.

---

## Limitações Conhecidas

1. **Configuração de módulo não suporta tipo lista/array.**
   `_VALID_CONFIG_TYPES` cobre só `string/integer/float/boolean`. O próprio
   exemplo típico (`region` string → `regions` lista) não é representável
   hoje. Decisão explícita do usuário: deixar para quando um módulo real
   precisar, em vez de desenhar uma API especulativa agora.
2. **Module Storage API cobre só key-value.** Um módulo com necessidade de
   schema relacional próprio continua livre de usar SQLAlchemy diretamente,
   sem uma API de provisionamento assistida pelo Core.
3. **Secret Store depende do backend nativo do SO.** Sem fallback definido
   para SO sem backend `keyring` compatível (ex.: Linux headless sem
   D-Bus/Secret Service).
4. **Frontend não foi verificado visualmente em navegador real** —
   sem ferramenta de browser automation disponível durante a implementação;
   `npm run build` (tsc + vite) e a integração de API foram confirmados.

---

Veja também:
- [Module Lifecycle](module-lifecycle.md)
- [Module Runtime](module-runtime.md)
- [Module Trust](module-trust.md)
- [Package Manager](package-manager.md)
