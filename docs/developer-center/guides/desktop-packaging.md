---
title: Empacotamento Desktop
category: sdk-desenvolvimento
domain: [sdk-desenvolvimento]
tags: [guide, packaging, pyinstaller]
---

# Empacotamento Desktop

Como gerar e depurar o build empacotado do backend. Complementa
[core/desktop-distribution](../core/desktop-distribution.md) (arquitetura)
e [core/launcher](../core/launcher.md) (ciclo de vida do processo).

## Gerar o build

```powershell
.\scripts\build-backend.ps1
```

Requer o `.venv` do backend já criado (`core/backend/.venv`). Instala
PyInstaller ad-hoc nesse venv (não é dependência do projeto — só do
processo de build) e gera:

```
core/backend/dist-backend/techforge-backend/techforge-backend.exe
```

## Testar o build isoladamente

O jeito mais confiável de pegar bug de empacotamento é rodar o `.exe`
puro, sem nada do ambiente de dev por perto:

```bash
rm -rf "$env:LOCALAPPDATA\TechForge"   # simula clean machine
./dist-backend/techforge-backend/techforge-backend.exe
curl http://127.0.0.1:8000/api/v1/platform/ready
```

Testes automatizados com mocks (`monkeypatch`) não pegam boa parte dos
bugs de empacotamento — três apareceram só rodando o `.exe` de verdade
(import-by-string do uvicorn, `__file__` sem sentido dentro do
bundle, diretórios de dados nunca criados). Sempre validar com o
executável real antes de considerar um build pronto.

## Problemas conhecidos e como diagnosticar

| Sintoma | Causa provável | Onde olhar |
|---|---|---|
| `Could not import module app.main` | Import-by-string do uvicorn não funciona congelado | `techforge_server.py` deve passar o objeto `app`, não a string |
| `unable to open database file` | Diretório de `user_data_dir()` não existe ainda | `app.core.settings.ensure_user_data_dirs` deve rodar antes de qualquer acesso ao DB |
| `Path doesn't exist: .../_internal/alembic` | `alembic/`/`alembic.ini` não bundlados (são dados, não código) | `--add-data` no `build-backend.ps1` |
| `ModuleNotFoundError: aiosqlite` | SQLAlchemy resolve o driver por string a partir da `DATABASE_URL`, PyInstaller não enxerga | `--hidden-import aiosqlite` no `build-backend.ps1` |
| `install_dir()` aponta pra lugar sem sentido | `Path(__file__)` dentro do bundle não reflete a árvore real | `install_dir()` deve checar `sys.frozen` e usar `sys.executable` |

## Escopo atual

Só o executável do backend, sem instalador Windows GUI (Inno
Setup/MSI) — packaging validation em clean machine real fica
pendente até existir um instalador de fato. Ver [`docs/limitations.md`](../../limitations.md).
