# Plano — Fase 12: Configuration, Data & Persistence

> Spec: docs/phases/12-Fase-12-Configuration-Data-Persistence.md
> Pré-requisito: Fase 11 (Marketplace Distribution) ✅ fechada.

## Premissas validadas (investigação de código real)

1. `app/db/database.py::_migrate()` é uma whitelist manual
   (`additions = {"modules": [...]}`) — não escala, não separa Core de
   módulo. Spec §14 pede exatamente essa separação.
2. `ModuleExecutionContext.configuration` (Fase 9,
   `app/module_runtime/context.py:48`) é sempre `{}` — nunca foi
   preenchido. É o ponto de entrada natural pro Module Storage API
   (spec §6/§7).
3. `ModuleExecutionContext.paths` é um único `Path` (a pasta de
   instalação) — spec §20 pede `data/cache/exports/temp` oficiais.
4. `alembic==1.13.1` está em `requirements.txt` desde sempre e nunca
   foi usado — sem `alembic.ini`, sem pasta de migrations, zero
   referência no código. Dependência parada.
5. Não existe `keyring` nem qualquer lib de secrets — Secret Store
   (spec §11) é 100% novo nesta fase.
6. `CatalogAggregator` (Fase 11) já implementa cache TTL por fonte —
   vira a base do `TTLCache` genérico (§19), sem duplicar lógica.

## Decisões arquiteturais (confirmadas com o usuário antes do plano)

1. **Migrations → Alembic**, não um runner caseiro. É dependência já
   instalada, feita exatamente pra isso. `core migrations` em
   `core/backend/alembic/` (versiona `modules`, `module_configurations`,
   `module_kv_store`, etc — tudo que o Core possui). `module migrations`
   ficam dentro do próprio `.mod` do módulo (descobertas via manifest),
   rodadas pelo `PackageManager.update()` — o Alembic do Core nunca
   toca schema de negócio de módulo, mantendo o ownership separado
   (spec §27).
2. **Module config**: manifest ganha bloco `configuration.fields`
   (`id`/`type`/`default`, formato do exemplo do spec §10). Persistido
   em uma única tabela `module_configurations(module_id PK, values_json)`
   — não uma tabela por módulo. Validação via schema dinâmico
   (`pydantic.create_model`) antes de persistir (§12) — configuração
   inválida nunca chega a gravar.
3. **Module Storage API**: key-value simples
   (`context.storage.get/set/transaction`) sobre uma tabela única
   `module_kv_store(module_id, key, value_json)` para o caso "simples"
   do §7. Um módulo que precise de tabelas relacionais próprias
   continua livre de criá-las (nada no Core impede), mas esta fase
   **não** constrói um framework de provisionamento de schema por
   módulo — fica documentado como extensão futura, não implementado.
4. **Secrets**: lib `keyring` (usa o cofre nativo do SO — Windows
   Credential Manager, macOS Keychain, Secret Service no Linux) por
   trás de uma abstração `SecretStore`, trocável no Server futuramente.
   Sem criptografia própria — a spec exige isso explicitamente (§11).
5. **Filesystem paths**: `ModulePaths(data, cache, exports, temp)`
   substitui o `Path` solto em `ModuleExecutionContext.paths`, criados
   na instalação (`PackageManager.install`).
6. **Fora de escopo — só documentação, zero implementação** (spec §34,
   explícito): PostgreSQL, multiusuário completo, autenticação, RBAC,
   replicação, cluster, backup corporativo, data warehouse. Esses
   itens entram no Developer Center (Slice 12) só como "não
   implementado nesta fase / caminho de evolução futura" — nenhum
   código, nenhuma tabela, nenhum endpoint para eles agora.

## Novo pacote / arquivos

```
core/backend/alembic/                       # Alembic — core migrations
core/backend/alembic.ini
core/backend/app/db/storage.py              # StorageProvider (health check)
core/backend/app/models/module_configuration.py   # module_configurations
core/backend/app/models/module_kv_store.py        # module_kv_store
core/backend/app/services/module_configuration.py # CRUD + validação tipada
core/backend/app/services/module_storage.py       # context.storage get/set/transaction
core/backend/app/security/secret_store.py         # SecretStore (keyring)
core/backend/app/storage/cache.py                 # TTLCache genérico (extraído do CatalogAggregator)
core/backend/app/api/routes/system.py             # GET /system/storage/status
core/backend/app/api/routes/module_config.py      # GET/PUT config, POST validate
cli/techforge_cli/commands/storage.py             # techforge storage status
cli/techforge_cli/commands/migrations.py          # techforge migrations status|run
core/backend/app/module_engine/manifest.py        # + configuration.fields no ParsedManifest
core/backend/app/module_runtime/context.py        # configuration real + ModulePaths
```

## Slices

### Slice 1 — StorageProvider + health (TDD) — §3/§24
- `StorageProvider.health_check(db)` → `database: bool`, `writable: bool`.
- `GET /api/v1/system/storage/status`.
- `techforge storage status`.

**Aceite:** endpoint e CLI reportam `Healthy` num banco saudável;
teste simula falha de escrita e reporta `writable=False` sem derrubar
a API.

### Slice 2 — Migrations via Alembic (TDD) — §14
- `alembic init` configurado pra usar `settings.DATABASE_URL` e
  `Base.metadata` (autogenerate).
- Migration inicial = baseline do schema atual (substitui o
  `_migrate()` ad-hoc; remove a whitelist depois que a baseline
  cobrir as colunas que ela adicionava).
- `techforge migrations status|run` chamando Alembic programaticamente
  (`alembic.command`), não subprocess solto.

**Aceite:** banco novo → `alembic upgrade head` cria o schema completo;
banco de uma instalação antiga (só com as colunas do `_migrate()` velho)
→ upgrade aplica sem erro e sem duplicar coluna.

### Slice 3 — Module configuration: schema + validação + persistência (TDD) — §10/§12
- `ParsedManifest.configuration_fields` (novo campo opcional).
- `module_configurations` (Alembic revision).
- Validação tipada antes de persistir; config inválida nunca grava.

**Aceite:** config válida persiste; inválida retorna erro sem
persistir; campo ausente usa `default` do manifest.

### Slice 4 — Module configuration: API + CLI (TDD) — §29/§30
- `GET/PUT /api/v1/modules/{id}/config`, `POST .../config/validate`.
- `techforge modules config <id>` / `config validate <id>`.

**Checkpoint 1:** suíte completa + fluxo manual (instalar módulo de
teste com config, salvar, validar erro).

### Slice 5 — Module Storage API — key-value (TDD) — §6/§7
- `module_kv_store` (Alembic revision).
- `context.storage.get/set/transaction` no `ModuleExecutionContext`.

**Aceite:** isolamento entre módulos (module A não lê chave de module B);
transaction com exceção faz rollback.

### Slice 6 — Filesystem paths oficiais (TDD) — §20/§21
- `ModulePaths(data, cache, exports, temp)` substitui `paths: Path`.
- Criação dos diretórios em `PackageManager.install`.

**Aceite:** paths existem após install, isolados por módulo; update
preserva `data/` (já garantido desde a Fase 11, só passa a expor via
`ModulePaths`).

### Slice 7 — Secret Store (TDD) — §11/§28
- `SecretStore` (abstração) + implementação `keyring`.
- Filtro de log redigindo valores conhecidos como secret.

**Checkpoint 2:** suíte completa; nenhum segredo aparece em `logs/`
após teste manual.

### Slice 8 — Cache TTL genérico (TDD) — §19
- Extrair `TTLCache` de `CatalogAggregator` pra `app/storage/cache.py`.
- `CatalogAggregator` passa a usar o `TTLCache` genérico.

**Aceite:** testes da Fase 11 continuam verdes, sem regressão.

### Slice 9 — Config migration no update de módulo (TDD) — §13/§15
- Hook opcional `migrate_config(old_version, old_config) -> new_config`
  declarado pelo módulo, chamado por `PackageManager.update()` antes
  de ativar a nova versão. Reaproveita o backup/rollback de `data/`
  já existente (Fase 11).

**Aceite:** migration ok → config nova persistida; migration falha →
config e versão anterior preservadas (rollback).

### Slice 10 — Data portability (TDD) — §16
- Export JSON de config de módulo e de configuração de plataforma.

**Aceite:** export de um módulo com config salva reproduz os valores
exatos via JSON.

### Slice 11 — Frontend — §31
- Platform Settings (página leve).
- Module Settings dentro de Module Details → Settings.
- Storage Status + Migration Status.

**Checkpoint 3:** `npm run build`/`npm run lint` limpos; fluxo manual
no navegador (abrir settings de um módulo, salvar config, ver erro de
validação).

### Slice 12 — Developer Center + AI Context + fechamento — §32/§33
- `docs/developer-center/core/persistence.md`: Storage API, Config,
  Secrets, Migrations, Cache, filesystem paths, Desktop→Server.
- Seção explícita "Fora de escopo nesta fase" cobrindo a decisão 6
  (PostgreSQL, multiusuário, auth, RBAC, replicação, cluster, backup
  corporativo, data warehouse) — só texto, nenhum código associado.
- AI Context atualizado.
- `tasks/phase-audit.md` + `tasks/phase-12-report.md`.
- Auditoria de ponta a ponta contra os 24 critérios do spec §35.

**Checkpoint final:** suíte completa + build de frontend + todos os
critérios de aceitação do spec conferidos individualmente.

## Known Issues esperados (documentar no report, não bloquear a fase)

- Module Storage API cobre só key-value (§7 "não forçar banco
  relacional") — módulo com necessidade de schema relacional próprio
  continua livre de usar SQLAlchemy diretamente, mas sem uma API de
  provisionamento assistida pelo Core nesta fase.
- Secret Store depende do backend nativo do SO via `keyring` — SO sem
  backend compatível (ex.: Linux headless sem D-Bus/Secret Service)
  fica sem opção de fallback nesta fase; documentado, não resolvido.
