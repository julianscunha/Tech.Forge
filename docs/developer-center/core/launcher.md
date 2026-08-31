---
title: Launcher
category: arquitetura-core
domain: [arquitetura-core]
tags: [core, launcher, phase-6, phase-16, startup, safe-mode]
---

# Launcher

Infraestrutura de bootstrap da plataforma. O Launcher é a única ação
que o usuário final precisa executar para ter o TechForge operacional.
Ver também [core/desktop-distribution](desktop-distribution.md) para a
separação Application Install / User Data e o empacotamento do backend.

## Arquitetura

```
techforge start
      ↓
Launcher (launcher/techforge_launcher/)
      ↓ valida ambiente (.venv, npm)
      ↓ inicia Backend  (uvicorn app.main:app)
      ↓ aguarda GET /api/v1/platform/ready = 200   (Fase 16 §5/§15/§42)
      ↓ inicia Frontend (npm run dev, só em modo dev)
      ↓ aguarda GET http://127.0.0.1:5173 = 200    (só em modo dev)
      ↓ abre navegador (ou foca a instância já aberta, Fase 16 §6)
TechForge operacional
```

O Launcher **não** contém lógica de negócio, não carrega módulos e não
duplica componentes do Core. Reaproveita `app.core.settings` como fonte única
de configuração (portas, paths).

`GET /api/v1/platform/ready` (Fase 16) é distinto de `/health`: só fica 200
depois que `RuntimeState.READY` é atingido (DB + Module Loader + Service
Registry completos) — `/health` só confirma que o processo responde.

## Comandos

| Comando | Função |
|---|---|
| `techforge start` | Inicia backend + frontend + navegador |
| `techforge stop` | Encerramento coordenado (frontend → backend) |
| `techforge status` | Estado de Launcher/Backend/Frontend/Database/Runtime |
| `techforge dev` | Modo desenvolvimento: backend com reload + vite dev server |
| `techforge safe-mode` | Core mínimo — nenhum módulo é carregado (§16/§18) |
| `techforge repair-check` | Verifica integridade dos arquivos do Core (§33) |
| `techforge diagnostics` | Diagnóstico técnico (Fase 14) |

Direto pelo Python: `python -m techforge_launcher <start|stop|status> [--dev] [--safe-mode]`
(a partir de `launcher/`).

## Single-instance

Guardado em `logs/pids/state.json`. Uma segunda execução com instância viva
**reabre a URL** (foca a aplicação existente, Fase 16 §6) em vez de só
avisar que já está rodando. PIDs obsoletos (processo morto) são detectados
e ignorados.

## Safe Mode (Fase 16 §16/§18)

`techforge safe-mode` seta `TECHFORGE_SAFE_MODE=true` só no processo do
backend spawnado. O Plugin Loader (`app/module_engine/plugin_loader.py`)
pula a montagem de `entry_backend` de **todos** os módulos — o registry
continua populado normalmente (Dashboard/Diagnostics mostram os módulos
como instalados, sem rota própria respondendo), permitindo desativar ou
remover um módulo problemático e reiniciar normal. É global, não
seletivo: não há tentativa de "adivinhar" qual módulo é o culpado.

## Erros de startup (Fase 16 §15/§35)

Falha de `/ready` (timeout) ou do frontend nunca mostra `Connection
refused` ou stack trace ao usuário — sempre uma mensagem curta + um
Diagnostic Code (`TF-STARTUP-001` backend, `TF-STARTUP-002` frontend,
catálogo em `app/observability/diagnostic_codes.py`) + a ação recomendada
(`techforge diagnostics`). Detalhe técnico completo vai só para
`logs/launcher.log`.

## Encerramento

Ordem obrigatória: Frontend → Backend → Launcher. Somente PIDs registrados
pelo próprio Launcher são terminados — nenhum processo python/node genérico
do sistema é afetado.

## Logs

`logs/launcher.log` registra startup, processos iniciados, health checks,
shutdown, erros e tempo total de inicialização. Falhas exibem mensagem simples
ao usuário; detalhe técnico fica apenas no log.

## Desenvolvimento vs Produção

- **Dev:** continuar subindo backend (`python run.py`) e frontend (`npm run dev`)
  separadamente quando quiser hot reload granular, ou `techforge dev`.
- **Produção/local:** apenas `techforge start`.
- Empacotamento do backend (`scripts/build-backend.ps1`, PyInstaller
  `--onedir`) existe desde a Fase 16 — ver
  [core/desktop-distribution](desktop-distribution.md). Instalador Windows
  GUI (Inno Setup/MSI) ainda não existe.

## Portabilidade

Toda interação com SO passa por helpers (`_spawn`, `_terminate`, `_pid_alive`)
com branch Windows/POSIX. Server mode Linux (systemd/Docker) poderá reutilizar
o mesmo Core sem alterações.
