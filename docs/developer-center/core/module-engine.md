---
title: Module Engine
category: arquitetura-core
domain: [arquitetura-core]
---

> Nota: este documento foi movido da raiz de docs/ e é complementar à visão
> canônica no Developer Center. Conteúdo histórico preservado.

# TechForge — Module Engine

## Documentação Técnica

---

## 1. Visão Geral

O Module Engine implementa toda a infraestrutura de plugins sem nenhum módulo funcional de negócio.
O objetivo é que novos módulos possam ser adicionados colocando um diretório em
`modules/installed/` e reiniciando o backend — sem alterar uma linha do Core.

---

## 2. Ciclo de Vida dos Módulos

```
startup
  │
  ▼
ModuleLoader.scan_installed()
  │
  ├─► para cada diretório em modules/installed/
  │     │
  │     ▼
  │   ManifestParser.parse(path)
  │     │ erro → status = INVALID → registrar no registry
  │     │
  │     ▼
  │   ModuleValidator.validate(path, platform_version)
  │     │
  │     ├─ estrutura inválida → status = INVALID
  │     ├─ versão incompatível → status = INCOMPATIBLE
  │     └─ OK → status = INSTALLED
  │
  ▼
ModuleRegistry.register(entry)
  │
  ▼
LoaderJournal.store(result)   ← disponível para Developer Mode
  │
  ▼
API disponível em /api/v1/registry/modules
```

---

## 3. ManifestParser

**Localização:** `core/backend/app/module_engine/manifest.py`

**Responsabilidade:** ler e validar o `manifest.yaml` de um módulo.

**Campos obrigatórios validados:**

| Campo            | Tipo   | Validação                              |
|------------------|--------|----------------------------------------|
| `id`             | string | snake_case, 2–64 chars, começa com letra |
| `name`           | string | não vazio                              |
| `version`        | string | semver (X.Y.Z)                         |
| `category`       | string | não vazio                              |
| `vendor`         | string | não vazio                              |
| `author`         | string | não vazio                              |
| `description`    | string | não vazio                              |
| `entry_backend`  | string | não vazio                              |
| `entry_frontend` | string | não vazio                              |

**Campos opcionais:**

| Campo                  | Default         |
|------------------------|-----------------|
| `platform_min_version` | `"0.0.0"`       |
| `platform_max_version` | `"999.999.999"` |
| `homepage`             | null            |
| `documentation`        | null            |
| `signature`            | null (não implementado)   |
| `checksum`             | null (não implementado)   |

**Erros emitidos:**
- `ManifestError: manifest.yaml not found in module directory: <path>`
- `ManifestError: manifest.yaml is not valid YAML: <detail>`
- `ManifestError: Missing required fields: id, version, …`
- `ManifestError: Field 'version' must follow semver format (X.Y.Z)`
- `ManifestError: Module id must be lowercase snake_case`

---

## 4. ModuleValidator

**Localização:** `core/backend/app/module_engine/validator.py`

**Responsabilidade:** validar a estrutura do diretório e compatibilidade de versão.

**Verificações (em ordem):**

1. **Manifest** — delega ao ManifestParser; qualquer ManifestError → `INVALID`
2. **Subdirectórios obrigatórios** — `backend/` e `frontend/` devem existir → `INVALID` se ausentes
3. **Entry points** — os caminhos declarados em `entry_backend` e `entry_frontend` devem existir no disco
4. **Compatibilidade de versão** — `platform_min_version ≤ platform_version ≤ platform_max_version` → `INCOMPATIBLE` se fora do intervalo

**Avisos (não bloqueantes):**
- `assets/` ausente
- `docs/` ausente
- `tests/` ausente

---

## 5. ModuleRegistry

**Localização:** `core/backend/app/module_engine/registry.py`

**Responsabilidade:** armazenar e servir o estado runtime de todos os módulos.

**Singleton de processo:** `from app.module_engine.registry import registry`

**API:**

```python
# Leitura
registry.all()                          # → list[ModuleEntry]
registry.get("hello_world")             # → ModuleEntry | None
registry.by_status(ModuleStatus.INSTALLED)
registry.by_category("Backup")
registry.count_total
registry.count_installed
registry.categories                     # → list[str] ordenada

# Escrita (apenas durante startup)
registry.register(entry)
registry.set_status("hello_world", ModuleStatus.DISABLED)
registry.deregister("hello_world")
registry.clear()
```

**Extensão via Marketplace:**
```python
# Instalar em runtime sem reiniciar
await marketplace.install(module_id)
registry.register(new_entry)
router.include_router(module_backend.router)  # plugin loader dinâmico
```

---

## 6. ModuleLoader

**Localização:** `core/backend/app/module_engine/loader.py`

**Responsabilidade:** orquestrar o scan completo na inicialização.

**Fluxo interno:**

```python
loader = ModuleLoader()
result = await loader.scan_installed()
# result.installed, result.invalid, result.incompatible
# result.journal → list[LoadEvent] para Developer Mode
```

**Integração com FastAPI lifespan (`app/main.py`):**
```python
@asynccontextmanager
async def lifespan(app):
    await init_db()
    loader = ModuleLoader()
    result = await loader.scan_installed()
    loader_journal.store(result)
    yield
```

---

## 7. LoaderJournal

**Localização:** `core/backend/app/module_engine/journal.py`

**Responsabilidade:** preservar o resultado do último scan para o Developer Mode.

**API REST:** `GET /api/v1/registry/loader/journal`

Cada evento no journal tem:

| Campo      | Tipo     | Descrição                              |
|------------|----------|----------------------------------------|
| `timestamp`| datetime | Momento do evento (UTC)                |
| `module_id`| str?     | ID do módulo afetado, ou null para global |
| `level`    | string   | `"info"` \| `"warning"` \| `"error"`   |
| `message`  | string   | Descrição do evento                    |
| `details`  | dict     | Dados adicionais (vendor, versão, etc.)|

---

## 8. Estrutura Oficial do Módulo

```
<module_id>/
├── manifest.yaml         ← obrigatório
├── backend/
│   └── main.py           ← entry_backend (obrigatório)
├── frontend/
│   └── index.tsx         ← entry_frontend (obrigatório)
├── assets/               ← opcional
├── docs/                 ← opcional
│   └── README.md
└── tests/                ← opcional
```

---

## 9. API Endpoints

| Method | Path                                    | Descrição                                   |
|--------|-----------------------------------------|---------------------------------------------|
| GET    | `/api/v1/registry/summary`              | Contadores agregados do registry            |
| GET    | `/api/v1/registry/modules`              | Lista todos os módulos com status runtime   |
| GET    | `/api/v1/registry/modules?developer_mode=true` | Inclui manifest_raw no payload        |
| GET    | `/api/v1/registry/modules/:module_id`   | Detalhe de um módulo específico             |
| GET    | `/api/v1/registry/loader/journal`       | Journal do último scan (Developer Mode)     |
| GET    | `/api/v1/health`                        | Health check de todos os módulos            |
| GET    | `/api/v1/health/:module_id`             | Health check de um módulo específico        |

---

## 10. Módulo hello_world

**Localização:** `modules/installed/hello_world/`

**Propósito:** validar a arquitetura do Module Engine. Não é um módulo funcional.

**O que valida:**
- Manifest com todos os campos obrigatórios
- Estrutura completa de diretórios
- Registro automático no ModuleRegistry ao subir o backend
- Aparência na tela Modules com status `INSTALLED`
- Exibição no Developer Mode com manifest_raw e logs de carregamento

---

## 11. Pontos de Extensão Preparados

### Marketplace

- `ModuleRegistry.register()` aceita entradas em runtime (não apenas no startup)
- `ModuleLoader._load_one()` pode ser chamado individualmente para instalar um módulo sem reiniciar
- Endpoint `POST /api/v1/modules` já aceita `checksum` e `signature`
- `modules/repository/` está reservado para módulos baixados do Marketplace

### Plugin Loader Dinâmico de Rotas

- `hello_world/backend/main.py` exporta um `router` FastAPI pronto para ser montado
- `AppRouter.tsx` tem comentário `PLUGIN LOADER HOOK` onde vai entrar `<Route path="modules/:moduleId/*">`
- O `ModuleEntry` contém `entry_backend` e `entry_frontend` para o loader saber o que importar

### Segurança

- `ParsedManifest.signature` e `.checksum` já existem no parser
- `ModuleValidator` tem um passo livre ao final do fluxo onde verificação de assinatura será inserida

### CLI

- `sdk/python/techforge_sdk/` é importável e funcionará como interface para `techforge install <module>`
- `ModuleLoader` é reutilizável pela CLI para validar antes de instalar

---

## 12. Developer Mode

Habilitar via toggle na página Modules.

Com Developer Mode ativo:
- Os cards de módulo exibem o `module_id` em fonte mono
- O botão "Loading Journal" aparece na toolbar
- O painel de detalhe exibe entry points e o manifest.yaml em JSON
- As requisições ao backend incluem `?developer_mode=true` (manifest_raw presente)
