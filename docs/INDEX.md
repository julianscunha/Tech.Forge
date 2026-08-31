---
title: Índice da Documentação — TechForge
category: governanca-setup
domain: [governanca-setup]
---

# Índice da Documentação — TechForge

> Organizado por audiência. Docs em português. Limitações conhecidas e
> decisões conscientes de escopo: [`limitations.md`](limitations.md).

## 1. Comece por aqui

| Doc | Tema |
|---|---|
| [README](../README.md) | Visão geral da plataforma, quick start, badges |
| [developer-center/intro](developer-center/intro.md) | Introdução ao Developer Center |
| [core-development-setup](developer-center/guides/core-development-setup.md) | Setup do Core (requisitos, testes, build) |
| [developer-center/guides/setup-windows](developer-center/guides/setup-windows.md) | Setup detalhado no Windows |
| [architecture](architecture.md) | Arquitetura: modos de execução, fonte única de verdade, lifecycle |

## 2. Referência para desenvolvedores de módulos (Developer Center)

| Doc | Tema |
|---|---|
| [reference/manifest](developer-center/reference/manifest.md) | Referência completa do manifest.yaml |
| [manifest.example.yaml](manifest.example.yaml) | Exemplo comentado de manifest |
| [guides/writing-docs](developer-center/guides/writing-docs.md) | Como escrever docs de módulos (padrão frontmatter) |
| [guides/development-guide](developer-center/guides/development-guide.md) | Guia de desenvolvimento de módulos |
| [guides/user-guide](developer-center/guides/user-guide.md) | Guia do usuário final — instalar, iniciar, usar, diagnosticar |
| [guides/it-deployment-guide](developer-center/guides/it-deployment-guide.md) | Guia de TI: requisitos, paths, logs, backup, troubleshooting |
| [guides/desktop-packaging](developer-center/guides/desktop-packaging.md) | Como gerar e depurar o build empacotado do backend (PyInstaller) |
| [sdk/backend](developer-center/sdk/backend.md) | SDK backend (contrato, router, notificações) |
| [sdk/frontend](developer-center/sdk/frontend.md) | SDK frontend (micro-frontend render) |
| [service-modules/overview](developer-center/service-modules/overview.md) | Service Modules e contratos públicos |
| [examples/hello-world](developer-center/examples/hello-world.md) | Exemplo passo a passo de módulo |

## 3. Arquitetura do Core

| Doc | Tema |
|---|---|
| [core/app-shell](developer-center/core/app-shell.md) | App Shell (estrutura visual permanente) |
| [core/module-registry](developer-center/core/module-registry.md) | Registry in-memory (fonte única de verdade) |
| [core/service-registry](developer-center/core/service-registry.md) | Service Registry: discovery, capabilities, invocação, erros |
| [core/dependency-governance](developer-center/core/dependency-governance.md) | Dependency Governance: declaração, direção, estados, grafo Mermaid |
| [core/module-runtime](developer-center/core/module-runtime.md) | Module Runtime: lifecycle hooks reais, ExecutionContext, SDK, Focus Mode |
| [core/module-trust](developer-center/core/module-trust.md) | Module Trust: integrity manifest, publisher, trust level, assinatura |
| [core/module-lifecycle](developer-center/core/module-lifecycle.md) | Ciclo de vida: install → activate → deactivate → remove |
| [core/module-catalog](developer-center/core/module-catalog.md) | Module Catalog: múltiplas fontes, descoberta remota, job de instalação |
| [core/persistence](developer-center/core/persistence.md) | Configuration, Data & Persistence: Storage API, migrations, config de módulo, Secret Store, filesystem paths |
| [core/quality-and-release](developer-center/core/quality-and-release.md) | Quality pipeline, níveis de teste, contract tests, versionamento, changelog, Release Readiness Report, CI, Module Release Checklist |
| [core/module-engine](developer-center/core/module-engine.md) | Module Engine: loader, validação, plugin router (detalhado) |
| [core/package-manager](developer-center/core/package-manager.md) | Package Manager (visão canônica) |
| [core/package-manager-internals](developer-center/core/package-manager-internals.md) | Package Manager: instalação .mod, cache, update (detalhado) |
| [core/launcher](developer-center/core/launcher.md) | Launcher: modos Desktop/Dev, single-instance, Safe Mode, /ready, erros de startup |
| [core/desktop-distribution](developer-center/core/desktop-distribution.md) | Desktop Distribution: install dir vs user data dir, empacotamento PyInstaller, repair-check |
| [core/runtime](developer-center/core/runtime.md) | Runtime status, uptime, DEGRADED |

## 4. Governança

| Doc | Tema |
|---|---|
| [governance/documentation-first-principle](developer-center/governance/documentation-first-principle.md) | Documentation First + Definition of Done documental |
| [context-map.yaml](context-map.yaml) | Help contextual: context_id → doc_id |

## 5. Limitações e roadmap

| Doc | Tema |
|---|---|
| [limitations](limitations.md) | Limitações conhecidas e decisões conscientes de escopo |
| [roadmap](roadmap.md) | O que já está pronto e o que depende de decisão futura |
| [roadmap/multi-user-server](roadmap/multi-user-server.md) | Visão: servidor central & multiusuário |
| [roadmap/external-module-ecosystem](roadmap/external-module-ecosystem.md) | Visão: ecossistema público de módulos |
| [roadmap/long-term-governance](roadmap/long-term-governance.md) | Visão: governança de longo prazo do Core |
| [architecture/](architecture/) | Inventário de componentes, contratos públicos, mapa de dependências |
| [adr/](adr/) | Decisões de arquitetura registradas |

## 6. Exemplos de módulos (referência)

| Doc | Tema |
|---|---|
| [examples/01](examples/01-System-Information-Service.md) | System Information Service (Service Module) |
| [examples/02](examples/02-System-Health-Check.md) | System Health Check (dependência entre módulos) |
