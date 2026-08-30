---
title: Launcher
category: arquitetura-core
domain: [arquitetura-core]
tags: [core, launcher, phase-6, startup]
---

# Launcher

Infraestrutura de bootstrap da plataforma. O Launcher é a única ação
que o usuário final precisa executar para ter o TechForge operacional.

## Arquitetura

```
techforge start
      ↓
Launcher (launcher/techforge_launcher/)
      ↓ valida ambiente (.venv, npm)
      ↓ inicia Backend  (uvicorn app.main:app)
      ↓ aguarda GET /api/v1/platform/status = 200
      ↓ inicia Frontend (npm run dev)
      ↓ aguarda GET http://127.0.0.1:5173 = 200
      ↓ abre navegador
TechForge operacional
```

O Launcher **não** contém lógica de negócio, não carrega módulos e não
duplica componentes do Core. Reaproveita `app.core.settings` como fonte única
de configuração (portas, paths).

## Comandos

| Comando | Função |
|---|---|
| `techforge start` | Inicia backend + frontend + navegador |
| `techforge stop` | Encerramento coordenado (frontend → backend) |
| `techforge status` | Estado de Launcher/Backend/Frontend/Database/Runtime |

Direto pelo Python: `python -m techforge_launcher <start|stop|status>`
(a partir de `launcher/`).

## Single-instance

Guardado em `logs/pids/state.json`. Uma segunda execução responde
"TechForge já está em execução." sem iniciar nova instância. PIDs obsoletos
(processo morto) são detectados e ignorados.

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
  separadamente quando quiser hot reload granular.
- **Produção/local:** apenas `techforge start`.
- Empacotamento (`TechForge.exe`) fica para fase posterior; o Launcher foi
  desenhado para que a estratégia de empacotamento seja acoplável sem mudança
  no Core.

## Portabilidade

Toda interação com SO passa por helpers (`_spawn`, `_terminate`, `_pid_alive`)
com branch Windows/POSIX. Server mode Linux (systemd/Docker) poderá reutilizar
o mesmo Core sem alterações.
