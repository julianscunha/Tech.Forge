---
title: Guia de TI e Implantação
category: sdk-desenvolvimento
domain: [sdk-desenvolvimento]
tags: [guide, it, deployment, phase-16, desktop]
---

# Guia de TI e Implantação

Referência técnica pra quem precisa implantar, dar suporte ou manter o
TechForge Desktop numa máquina corporativa. Complementa o
[Guia do Usuário](user-guide.md) e [core/desktop-distribution](../core/desktop-distribution.md).

## Requisitos

- Windows 10/11 (plataforma inicial suportada — POSIX funciona em dev,
  mas o empacotamento atual é Windows-first).
- Sem Python/Node necessários quando usando o backend empacotado
  (`scripts/build-backend.ps1`); modo dev/fonte exige Python 3.11+ e
  Node 20+.
- Portas padrão: `8000` (backend), `5173` (frontend, só em modo dev).

## Paths

| O quê | Onde |
|---|---|
| Código (install dir) | Diretório do executável/repositório — read-only em produção |
| Dados do usuário (DB, logs, módulos) | `%LOCALAPPDATA%\TechForge\TechForge` (Windows, produção instalada) |
| Dados do usuário (dev/CI) | Raiz do repositório (coincide com o código) |

Override explícito: variável de ambiente `TECHFORGE_DATA_DIR`. Nunca
depender de caminho hardcoded — ver `app/core/paths.py`.

## Instalação

Não há instalador Windows GUI (Inno Setup/MSI) nesta fase — pendência
registrada em `tasks/phase-audit.md`. Hoje: distribuir o executável
gerado por `scripts/build-backend.ps1` + o build de produção do frontend
(`core/frontend/dist/`), ou o código-fonte completo com `techforge start`.

## Proxy e rede corporativa

Nada no Core assume acesso direto à internet além de:
- Instalação/atualização de módulos via catálogo remoto (`OFFICIAL_CATALOG_BASE_URL`).
- Módulos individuais que declarem uso de APIs externas.

O Core inicia e funciona totalmente offline (`Core startup`, módulos
locais, documentação local) sem internet. Configuração explícita de
proxy HTTP/HTTPS/certificados corporativos ainda não existe como tela —
item preparado arquiteturalmente (nenhuma lib assume conexão direta sem
seguir configuração de proxy do SO), não implementado como UI nesta fase.

## Logs

- `logs/backend.log`, `logs/frontend.log`, `logs/launcher.log` —
  `techforge logs --backend|--frontend|--launcher [-n N] [--follow]`.
- Formato JSON-lines para o backend (Fase 14), com rotação por tamanho
  (`LOG_MAX_BYTES`) e retenção configurável por nível (`LOG_RETENTION_DAYS`).
- `techforge diagnostics` e a página Diagnostics agregam erros recentes,
  execuções e uso de recursos.

## Backup

Copiar o diretório de dados do usuário (ver tabela de Paths acima)
preserva DB, módulos instalados e configuração. Não há ferramenta de
backup automatizada nesta fase.

## Atualização

Update flow completo do Core (check → download → validate → backup →
install → restart → migration → validate) está previsto
arquiteturalmente mas não implementado como fluxo de usuário nesta fase
— reinstalar preservando o diretório de dados do usuário já cobre o caso
prático hoje, dado que instalação e dados são fisicamente separados.

## Troubleshooting

| Sintoma | Ação |
|---|---|
| "Não foi possível iniciar o Backend" + `TF-STARTUP-001` | `techforge diagnostics`; ver `logs/backend.log` e `logs/launcher.log` |
| Porta já em uso | `techforge status`; encerrar o processo externo antes de `techforge start` |
| Módulo trava o Core | `techforge safe-mode`; desativar/remover o módulo problemático; reiniciar normal |
| Suspeita de arquivo corrompido/alterado | `techforge repair-check` (requer manifesto gerado com `--generate` no build) |
