---
title: Índice da Documentação — TechForge
category: governanca-setup
domain: [governanca-setup]
---

# Índice da Documentação — TechForge

> Organizado por audiência. Docs em português; cada fase define escopo,
> "o que não implementar" e critérios de aceitação. Status de implementação:
> [`tasks/phase-audit.md`](../tasks/phase-audit.md).

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
| [core/module-lifecycle](developer-center/core/module-lifecycle.md) | Ciclo de vida: install → activate → deactivate → remove |
| [core/module-engine](developer-center/core/module-engine.md) | Module Engine: loader, validação, plugin router (detalhado) |
| [core/package-manager](developer-center/core/package-manager.md) | Package Manager (visão canônica) |
| [core/package-manager-internals](developer-center/core/package-manager-internals.md) | Package Manager: instalação .mod, cache, update (detalhado) |
| [core/launcher](developer-center/core/launcher.md) | Launcher: modos Desktop/Dev, single-instance, shutdown |
| [core/runtime](developer-center/core/runtime.md) | Runtime status, uptime, DEGRADED |

## 4. Governança

| Doc | Tema |
|---|---|
| [governance/documentation-first-principle](developer-center/governance/documentation-first-principle.md) | Documentation First + Definition of Done documental |
| [context-map.yaml](context-map.yaml) | Help contextual: context_id → doc_id |

## 5. Fases do projeto (specs)

Status real em [`tasks/phase-audit.md`](../tasks/phase-audit.md). Relatórios e
planos por fase em [`tasks/`](../tasks/).

### Implementadas ✅

| Fase | Spec | Tema |
|---|---|---|
| 1 | [phases/01](phases/01-Fase-01-Foundation.md) | Foundation (FastAPI + React/TS + SQLite) |
| 2 | [phases/02](phases/02-Fase-02-Core-Architecture.md) | Core Architecture + Notification Foundation |
| 3 | [phases/03](phases/03-Fase-03-Module-System.md) | Module System (loader, validação, navegação) |
| 4 | [phases/04](phases/04-Fase-04-Marketplace-Package-Manager.md) | Marketplace & Package Manager (activate/deactivate) |
| 5 | [phases/05](phases/05-Fase-05-Developer-Center.md) | Developer Center & Doc Engine |
| 6 | [phases/06](phases/06-Fase-06-Launcher-Runtime.md) | Launcher & Runtime (modo Desktop) |
| 7 | [phases/07](phases/07-Fase-07-Documentation-Compliance-Checker.md) | Documentation Compliance Checker |
| 8 | [phases/08](phases/08-Fase-08-Service-Registry.md) | Service Registry: descoberta via contratos |
| 8.1 | [phases/08.1](phases/08.1-Fase-08.1-Dependency-Governance.md) | Dependency Governance: declaração, direção, ciclos, lifecycle |
| 9 | [phases/09](phases/09-Fase-09-Module-Runtime-Execution.md) | Module Runtime & Execution: lifecycle hooks reais, ExecutionContext, Focus Mode |

### Pendentes

| Fase | Spec | Tema |
|---|---|---|
| 10 | [phases/10](phases/10-Fase-10-Security-Integrity-Module-Trust.md) | Security, Integrity & Module Trust |
| 11 | [phases/11](phases/11-Fase-11-Module-Marketplace-Distribution.md) | Marketplace Distribution |
| 12 | [phases/12](phases/12-Fase-12-Configuration-Data-Persistence.md) | Configuration & Persistence |
| 13 | [phases/13](phases/13-Fase-13-Central-Server-Multi-User-Readiness.md) | Central Server Readiness (Linux) |
| 14 | [phases/14](phases/14-Fase-14-Observability-Telemetry-Diagnostics.md) | Observability & Diagnostics |
| 15 | [phases/15](phases/15-Fase-15-Platform-Quality-Testing-Release-Engineering.md) | Quality, Testing & Release |
| 16 | [phases/16](phases/16-Fase-16-Desktop-Distribution-User-Experience.md) | Desktop Distribution & UX |
| 17 | [phases/17](phases/17-Fase-17-Platform-Security-Trust-Hardening.md) | Security Hardening |
| 18 | [phases/18](phases/18-Fase-18-Platform-Finalization-Architecture-Consolidation.md) | Finalização & Consolidação |
| 18.1 | [phases/18.1](phases/18.1-Fase-18.1-External-Module-Sources-Module-Declaration.md) | External Module Sources |
| 19 | [phases/19](phases/19-Fase-19-Public-Release-Readiness-Open-Ecosystem.md) | Public Release Readiness |
| 20 | [phases/20](phases/20-Fase-20-Long-Term-Core-Governance-Ecosystem-Maintenance.md) | Governança de longo prazo |

## 6. Exemplos de módulos (referência)

| Doc | Tema |
|---|---|
| [examples/01](examples/01-System-Information-Service.md) | System Information Service (Service Module) |
| [examples/02](examples/02-System-Health-Check.md) | System Health Check (dependência entre módulos) |
