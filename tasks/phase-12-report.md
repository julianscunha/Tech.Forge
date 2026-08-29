# Relatório da Fase 12 — Configuration, Data & Persistence

> Spec: `docs/phases/12-Fase-12-Configuration-Data-Persistence.md`
> Plano: `tasks/phase12-plan.md`
> **Status: EM ANDAMENTO** — atualizado a cada slice concluída, não só no fechamento.

## Visão Geral

Formaliza a camada de configuração e persistência do TechForge: migrations versionadas
(Alembic, substituindo uma whitelist ad-hoc), configuração de módulo tipada e validada,
Module Storage API (key-value), filesystem paths oficiais, Secret Store via `keyring`,
cache TTL genérico. Fora de escopo (documentação apenas, spec §34): PostgreSQL,
multiusuário, autenticação, RBAC, replicação, cluster, backup corporativo, data warehouse.

---

## Slices & Conclusão

### Slice 1 — StorageProvider + health ✅ (commit `2dc8098`)
- **Arquivos:** `app/db/storage.py`, `app/api/routes/system.py`, `cli/techforge_cli/commands/storage.py`
- **O quê:** `StorageProvider.health_check()` — probe real de leitura+escrita no SQLite.
- **Aceite:** `GET /api/v1/system/storage/status` e `techforge storage status` reportam
  `database`/`writable`; testado via TestClient e servidor real.
- **Teste:** `test_phase12_storage.py`

### Slice 2 — Migrations via Alembic ✅ (commit `7a5a74e`)
- **Arquivos:** `core/backend/alembic/` (env.py async, revisão `0001`), `app/db/migrations.py`
- **O quê:** Substitui a whitelist ad-hoc `_migrate()` pelo Alembic — dependência já
  instalada em `requirements.txt` desde sempre, nunca usada antes desta fase.
- **Decisão-chave:** `upgrade_head()` roda em thread separada
  (`asyncio.to_thread`) — Alembic faz `asyncio.run()` internamente em `env.py`,
  incompatível com um event loop já rodando (o de `init_db()`).
- **Aceite:** banco novo (via `create_all`) e banco legado (schema pré-Fase-11) upgradam
  sem erro nem duplicar coluna; idempotente.
- **Teste:** `test_phase12_migrations.py`

### Slice 3 — Module configuration: schema + validação + persistência ✅ (commit `54f6d1d`)
- **Arquivos:** `app/module_engine/manifest.py` (+`configuration_fields`),
  `app/models/module_configuration.py`, `app/services/module_configuration.py`,
  Alembic `0002`
- **O quê:** Manifest ganha bloco opcional `configuration.fields` (id/type/default),
  validado no parse. Persistência em 1 linha por módulo (`module_configurations`,
  JSON), validada via schema dinâmico (`pydantic.create_model`) antes de gravar.
- **Aceite:** tipo desconhecido/id duplicado/campo sem type falham no parse; config
  inválida nunca persiste; valores ausentes usam o default do manifest.
- **Teste:** `test_phase12_manifest_config.py`, `test_phase12_module_configuration.py`

### Slice 4 — Module configuration: API + CLI ✅ (commit `09c007b`) — **Checkpoint 1**
- **Arquivos:** `app/api/routes/module_config.py`, `cli/techforge_cli/commands/modules.py`
- **O quê:** `GET/PUT /api/v1/modules/{id}/config`, `POST .../config/validate`, lendo os
  campos do registry in-memory (`manifest_raw`) — fonte única de verdade, nunca
  reparseia manifest.yaml do disco. CLI: `techforge modules config <id> [--set k=v]`,
  `techforge modules config-validate <id> --set k=v`.
- **Checkpoint 1:** suíte completa (624 testes) + fluxo manual de ponta a ponta contra
  backend real (get defaults → set → get reflete → validate rejeita tipo errado).
- **Teste:** `test_phase12_module_config_api.py`

### Slice 5 — Module Storage API (key-value) ✅ (commit `ea62bc0`)
- **Arquivos:** `app/models/module_kv_store.py`, `app/services/module_storage.py`,
  Alembic `0003`
- **O quê:** `context.storage.get/set/transaction` sobre `module_kv_store`. Desenho
  validado com a skill `api-and-interface-design` antes de implementar.
- **Decisão-chave:** isolamento **estrutural**, não por convenção — `module_id` é
  fixado na construção de `ModuleKVStorage`, nunca é parâmetro de `get`/`set`, então
  um módulo não tem como ler/escrever chave de outro módulo mesmo por engano.
  `set()` valida serializabilidade JSON e nunca deixa vazar exceção do
  SQLAlchemy/json pro código do módulo (`ModuleStorageError`).
- **Aceite:** isolamento entre módulos confirmado por teste; `transaction()` faz
  rollback automático em exceção.
- **Teste:** `test_phase12_module_storage.py`

### Slice 6 — Filesystem paths oficiais ✅ (commit `8edb920`)
- **Arquivos:** `app/module_runtime/paths.py` (`ModulePaths`), `app/package_manager/manager.py`,
  `app/module_trust/integrity.py`
- **O quê:** `ModulePaths(root, data, cache, exports, temp)` substitui o `Path` solto em
  `ModuleExecutionContext.paths`. `PackageManager.install()` cria os quatro
  diretórios logo após extrair o módulo.
- **Bug real encontrado e corrigido:** `cache/`, `exports/`, `temp/` não estavam na
  lista de exclusão do hash de integridade (Fase 10) — escrever neles depois da
  instalação marcava o módulo como `UNEXPECTED_FILE` incorretamente (são dados de
  runtime, não código do módulo). Corrigido em `_EXCLUDED_DIR_PREFIXES`.
- **Teste:** `test_phase12_module_paths.py`

### Slice 7 — Secret Store ✅ (commit `f0edbbf`) — **Checkpoint 2**
- **Arquivos:** `app/security/secret_store.py`, `app/security/redaction.py`,
  `requirements.txt` (+`keyring==25.7.0`)
- **O quê:** `context.secrets` (`ModuleSecretStore`) usa o cofre nativo do SO via
  `keyring`, mesmo desenho de isolamento estrutural por `module_id` do Storage API
  (Slice 5). `SecretRedactionFilter` redige qualquer valor já gravado que apareça
  em mensagem de log.
- **Decisão-chave (achado técnico):** o filtro precisa ser instalado no **Handler**
  do logger raiz, não no **Logger** — um `Filter` anexado a um `Logger` só roda
  quando aquele logger específico é o originador do registro; registros
  propagados de loggers filhos (`techforge.module.*`) vão direto pros Handlers
  dos ancestrais, sem passar pelo `Logger.filter()` do ancestral. Testado com um
  logger isolado (não o root real, que o pytest mexe entre testes).
- **Validado contra o Windows Credential Manager real** (set/get/delete), não só
  mockado — testes automatizados usam um backend fake pra não depender de
  D-Bus/Secret Service/Credential Manager disponíveis em CI.
- **Checkpoint 2:** confirmado manualmente que um segredo logado aparece como
  `***REDACTED***`, nunca em texto puro.
- **Teste:** `test_phase12_secret_store.py`

### Slice 8 — Cache TTL genérico ✅ (commit `c5206c8`)
- **Arquivos:** `app/storage/cache.py` (`TTLCache[T]`), `app/package_manager/catalog_cache.py`
- **O quê:** Extrai a lógica de `CatalogCache` (Fase 11) pra um `TTLCache` genérico,
  reutilizável por qualquer módulo/serviço. `CatalogCache` vira um alias fino
  (herda de `TTLCache[list[PackageInfo]]`) — mesmo construtor e métodos, zero
  mudança de comportamento; `CatalogAggregator` não precisou ser tocado.
- **Aceite:** testes da Fase 11 (`test_phase11_sources.py`) continuam verdes sem
  alteração — prova de que a extração não mudou comportamento.
- **Teste:** `test_phase12_ttl_cache.py`

### Slice 9 — Config migration no update de módulo ✅ (pendente commit)
- **Arquivos:** `app/package_manager/config_migration.py`, `app/package_manager/manager.py`
- **O quê:** Hook opcional `migrate_config(old_version, old_config) -> new_config`,
  declarado pelo módulo (mesmo padrão de `enable`/`disable`/`health_check` da Fase 9:
  objeto `module` no `entry_backend`). Chamado por `PackageManager.update()` depois de
  extrair a versão nova, antes de ativar (regenerar integrity + hot-reload).
- **Decisão-chave:** ao contrário dos hooks de lifecycle (best-effort), uma falha aqui
  **é** um erro de update — reaproveita o mesmo bloco de rollback-por-exceção que
  `update()` já usa para falha de extração, sem lógica de rollback nova. Nunca reusa o
  cache de instância do `module_runtime.lifecycle` (aquele serve a versão ativa em
  runtime; a migration precisa da versão NOVA recém-extraída) — carrega via
  `load_module_file()` direto, com `import_name` próprio.
- **Desvio encontrado (registrado, não implementado):** o exemplo do próprio spec §13
  (`region` string → `regions` lista) não é representável no schema de configuração
  hoje — `_VALID_CONFIG_TYPES` (Slice 3) só cobre `string/integer/float/boolean`, sem
  tipo lista/array. Testado com um rename string→string equivalente em vez disso.
  **Decisão para o usuário considerar em fase futura:** adicionar tipo `list`/`array`
  ao schema de configuração de módulo, se algum módulo real precisar.
- **Aceite:** migration bem-sucedida persiste a nova config; migration que levanta
  exceção ou retorna algo não-dict/inválido faz rollback completo (arquivos E config
  voltam pra versão anterior, nunca commitados parcialmente — o `save_config()` só
  roda depois que `migrate()` retorna com sucesso, então uma falha no meio nunca
  deixa a config nova meio-gravada).
- **Teste:** `test_phase12_config_migration.py`

---

## Ainda pendente

- **Slice 10** — Data portability (export JSON).
- **Slice 11** — Frontend (Platform Settings, Module Settings, Storage/Migration Status).
- **Slice 12** — Developer Center + AI Context + fechamento (auditoria dos 24 critérios
  do spec §35, `tasks/phase-audit.md`, contagem final de testes).

## Limitações conhecidas registradas até aqui

- Config de módulo não suporta tipo lista/array (só string/integer/float/boolean) —
  ver Slice 9 acima.
- Module Storage API cobre só key-value — módulo com necessidade de schema relacional
  próprio continua livre de usar SQLAlchemy diretamente, sem API de provisionamento
  assistida pelo Core (decisão original do plano, não uma lacuna nova).
- Secret Store depende do backend nativo do SO via `keyring` — sem fallback definido
  pra SO sem backend compatível (Linux headless sem D-Bus/Secret Service).

## Contagem de testes (snapshot após Slice 9)

659 testes de backend passando, 3 skipped (pré-existentes, sem relação com a Fase 12).
