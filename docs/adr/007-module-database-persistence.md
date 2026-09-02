---
title: "ADR-007: Persistência de banco por módulo (sdk.database)"
category: governanca-setup
domain: [governanca-setup]
tags: [architecture, adr, sdk, database]
---

# ADR-007: Persistência de banco por módulo (sdk.database)

**Status**: Accepted

## Context

`sdk.database` (SDK Python) sempre foi um mock em memória — `fetch_all`/
`execute` não sobrevivem a um restart do backend, mas a assinatura dos
métodos parece uma sessão real, sem nenhum aviso na superfície da API. Um
autor de módulo real (feedback do desenvolvimento do Lead.Tracker)
descobriu isso só lendo o código-fonte do SDK, e acabou implementando sua
própria camada de persistência em vez de confiar no que existia
(rastreado como TD-021). Nenhum dos 4 módulos hoje instalados usa
`sdk.database`.

`sdk.storage` (arquivos) já resolve isolamento por módulo de forma real e
comprovada: cada módulo grava sob `modules/installed/<module_id>/data/`,
com guarda de path traversal. `sdk.database` precisa do mesmo nível de
isolamento, mas para dados tabulares/consultáveis via SQL em vez de
arquivos soltos.

## Decision

`sdk.database` passa a persistir de verdade em **SQLite por módulo**,
via `aiosqlite` (já é dependência do Core, mesmo padrão usado em
`app/db/database.py`):

- **Isolamento**: um arquivo `modules/installed/<module_id>/data/<module_id>.db`
  por módulo — mesmo diretório base que `sdk.storage` já usa, então
  qualquer backup/limpeza que já cubra a pasta `data/` do módulo cobre o
  banco automaticamente. Nenhum módulo acessa o banco de outro.
- **API**: mantém a assinatura já documentada (`fetch_all`, `fetch_one`,
  `execute`, `execute_many`, `begin_transaction`/`commit`/`rollback`) —
  não é uma sessão ORM, é SQL parametrizado cru (`?` como placeholder,
  padrão stdlib `sqlite3`/`aiosqlite`). Módulos que já escreveram contra
  essa assinatura não precisam mudar nada além de passar a confiar nela.
- **Migrações**: são responsabilidade do próprio módulo — o padrão é
  `CREATE TABLE IF NOT EXISTS` idempotente dentro de `install()`/
  `enable()`, o mesmo padrão já sugerido no exemplo de
  `module-lifecycle.md`. Não introduzimos Alembic por módulo: o Core não
  conhece o schema de um módulo de terceiro, e cada módulo é livre para
  gerenciar sua própria evolução de schema.
- **Concorrência**: uma única conexão `aiosqlite` por instância de
  `DatabaseSDK`, serializada por um `asyncio.Lock` — SQLite é
  single-writer de qualquer forma, então uma conexão por módulo já é o
  suficiente; não há pool nem múltiplos workers (o Core é single-process
  por design, ver TD-008).
- **Backup**: nenhum mecanismo novo — o arquivo `.db` vive dentro do
  `data/` do módulo, já coberto pelo mesmo raciocínio de preservação de
  dados que `sdk.storage` (reinstalar preserva `data/`, separado do
  diretório de instalação).
- **Compatibilidade**: módulos que hoje ignoram `sdk.database` (todos os
  4 instalados) não são afetados. Não há dado real em produção rodando
  contra o mock hoje, então não existe migração de dados a fazer.

Fica fora de escopo desta decisão (YAGNI até haver caso real): pool de
conexões, múltiplos workers, e um sistema de migração formal por módulo.

## Consequences

- Dados gravados via `sdk.database` sobrevivem a restart — elimina o
  risco de perda silenciosa de dado que o mock representava.
- `sdk.python/setup.py` ganha `aiosqlite` como dependência declarada
  (antes só usava o que já estava instalado no venv do Core por
  coincidência de processo compartilhado).
- Autores de módulo que hoje implementam a própria camada de
  persistência (como o Lead.Tracker fez) podem migrar para `sdk.database`
  quando quiserem, sem mudar a forma como chamam os métodos.
- **Gap conhecido**: sem migração automática de schema — se um módulo
  mudar sua própria tabela entre versões, `upgrade(from_version)` precisa
  tratar isso manualmente (`ALTER TABLE`/recriação), o SDK não oferece
  ferramenta para isso ainda.
