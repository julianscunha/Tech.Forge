---
title: Desktop Distribution
category: arquitetura-core
domain: [arquitetura-core]
tags: [core, desktop, paths, packaging, developer-mode]
---

# Desktop Distribution

Transforma o TechForge numa aplicação corporativa de fácil
instalação/uso, separando explicitamente **Application Install** (código)
de **User Data** (dados do usuário), sem exigir Python/Node instalados na
máquina do usuário final. Ver também [core/launcher](launcher.md) para o
ciclo de vida do processo.

## Application Install vs User Data

`app/core/paths.py` define dois conceitos distintos:

```
install_dir()     → onde está o código (read-only em produção)
user_data_dir()   → onde ficam DB, logs, módulos instalados
```

Resolução de `install_dir()`:

- **Congelado** (`sys.frozen`, executável PyInstaller): diretório do
  próprio `sys.executable`. `Path(__file__)` dentro de um bundle congelado
  não tem relação com a árvore real — usar `__file__` aqui foi um bug real
  encontrado empacotando o backend pela primeira vez.
- **Não congelado** (dev/CI): raiz do repositório (`Path(__file__)` × 5
  parents), como sempre foi.

Resolução de `user_data_dir()`, em ordem:

1. `TECHFORGE_DATA_DIR` (env var, override explícito — útil pra testes/CI)
2. Mesmo diretório de `install_dir()`, se ele contiver `.git` (árvore de
   dev — `pytest`/`techforge start` locais não mudam nada)
3. `platformdirs.user_data_dir("TechForge", "TechForge")` — produção
   instalada (`%LOCALAPPDATA%\TechForge\TechForge` no Windows)

`ensure_user_data_dirs()` cria `config/`, `logs/`, `modules/{installed,
repository,cache}` dentro de `user_data_dir()` na primeira execução (spec
§14 "Create Data Directories") — sem isso, o SQLite não abre o arquivo do
banco num diretório que ainda não existe (outro bug real do Slice 7).

`settings.py` deriva `DATABASE_URL`, `MODULES_INSTALLED_PATH`,
`MODULES_REPOSITORY_PATH`, `MODULES_CACHE_PATH`, `LOGS_PATH` e o `.env` de
`USER_DATA_DIR`. `FRONTEND_DIST_PATH` continua em `BASE_DIR`/`install_dir()`
— é artefato de código, não dado do usuário.

## Empacotamento do backend

`scripts/build-backend.ps1` gera um executável standalone via PyInstaller
`--onedir` (não `--onefile` — mais lento pra iniciar e mais sujeito a
bloqueio de antivírus corporativo). Roda a partir do `.venv` já existente
em `core/backend/.venv`, sem virar dependência do projeto.

Duas particularidades exigidas por um bundle congelado, ambas
descobertas rodando o `.exe` de verdade (não visíveis testando com mocks):

- `techforge_server.py` (entry point) passa o **objeto** `app` pro
  `uvicorn.run()`, não a string `"app.main:app"` — import-by-string falha
  dentro do bundle.
- `alembic/` e `alembic.ini` são bundlados via `--add-data`: são dados
  lidos por caminho de arquivo em runtime (`app/db/migrations.py`), não
  código Python importado — a análise estática do PyInstaller nunca os
  veria sozinha.

Escopo atual: só o executável do backend. Instalador Windows GUI
(Inno Setup/MSI), auto-update e uninstall formais ficam fora — ver
[`docs/limitations.md`](../../limitations.md).

## Safe Mode e paths reais na UI

Ver [core/launcher — Safe Mode](launcher.md#safe-mode) para o
mecanismo. Developer Mode (Settings → Developer Mode) expõe
`install_dir`/`user_data_dir` reais (via `GET /diagnostics/health`,
`platform.paths`) e um botão "Recarregar módulos"
(`POST /api/v1/registry/rescan`) que refaz o scan de `modules/installed/`
sem reiniciar o processo — reusa o mesmo `PackageManager._hot_reload()`
chamado após install/update/remove.

## `techforge repair-check`

Reaproveita o integrity manifest do Module Trust (hash SHA-256 por arquivo,
`app/module_trust/integrity.py`) aplicado ao código do próprio Core
(`app/module_trust/core_repair.py`), não a módulos. `--generate` grava
`core-integrity.json` na raiz da instalação a partir do estado atual;
sem flag, compara contra o disco agora. Só verifica — nunca tenta
restaurar nada automaticamente (spec §33).

## Fora de escopo (decisão consciente)

- Instalador Windows GUI completo — só o script de build do backend.
- Update flow do Core além do "arquiteturalmente previsto" (a separação
  de paths já cobre "user data preservado ao reinstalar").
- Uninstall com opções formais e Repair "restaurar componentes" além da
  verificação de `repair-check`.
- Proxy corporativo além de confirmar que nada assume acesso direto à
  internet.

Ver [`docs/limitations.md`](../../limitations.md) para o registro consolidado.
