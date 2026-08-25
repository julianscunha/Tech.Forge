---
title: Índice da Documentação — TechForge.v2
category: governanca-setup
domain: [governanca-setup]
---

# Índice da Documentação — TechForge.v2

> Organizado por categoria. Fonte: leitura dos cabeçalhos e objetivos de cada documento.
> Docs em português; cada fase define escopo, "o que não implementar" e critérios de aceitação.

## 1. Fundação & Arquitetura Core

| Doc | Tema |
|---|---|
| [phases/01](phases/01-Fase-01-Foundation.md) | Foundation: fundação inicial (FastAPI + React/TS + SQLite), sem módulos de negócio — **✅ implementada** |
| [phases/02](phases/02-Fase-02-Core-Architecture.md) | Core Architecture: responsabilidades, contratos e componentes do Core |

> Documentação técnica do Core já implementado: [`system/00-indice.md`](system/00-indice.md).

## 2. Sistema de Módulos

| Doc | Tema |
|---|---|
| [phases/03](phases/03-Fase-03-Module-System.md) | Module System: descoberta, validação, carregamento de módulos |
| [phases/09](phases/09-Fase-09-Module-Runtime-Execution.md) | Module Runtime: ciclo de execução dos módulos ativos |

## 3. Marketplace, Distribuição & Dependências

| Doc | Tema |
|---|---|
| [phases/04](phases/04-Fase-04-Marketplace-Package-Manager.md) | Marketplace & Package Manager: catálogo, instalação, ativação/remoção |
| [phases/08.1](phases/08.1-Fase-08.1-Dependency-Governance.md) | Dependency Governance: resolução, compatibilidade, conflitos e ciclos |
| [phases/11](phases/11-Fase-11-Module-Marketplace-Distribution.md) | Marketplace & Distribution: fontes locais/internas |
| [phases/18.1](phases/18.1-Fase-18.1-External-Module-Sources-Module-Declaration.md) | Módulos externos por URL/arquivo local |

## 4. Serviços & Contratos

| Doc | Tema |
|---|---|
| [phases/08](phases/08-Fase-08-Service-Registry.md) | Service Registry: descoberta de capacidades via contratos públicos |

## 5. Documentação & Developer Experience

| Doc | Tema |
|---|---|
| [phases/05](phases/05-Fase-05-Developer-Center.md) | Developer Center & Documentation Engine |
| [phases/07](phases/07-Fase-07-Documentation-Compliance-Checker.md) | Compliance Checker: validação automática de docs dos módulos |

## 6. Execução & Experiência do Usuário

| Doc | Tema |
|---|---|
| [phases/06](phases/06-Fase-06-Launcher-Runtime.md) | Launcher: execução sem terminais manuais |
| [phases/16](phases/16-Fase-16-Desktop-Distribution-User-Experience.md) | Distribuição Desktop e UX corporativa |

## 7. Configuração, Persistência & Infra

| Doc | Tema |
|---|---|
| [phases/12](phases/12-Fase-12-Configuration-Data-Persistence.md) | Configuration, Data & Persistence |
| [phases/13](phases/13-Fase-13-Central-Server-Multi-User-Readiness.md) | Central Server & Multi-User Readiness (Linux) |

## 8. Segurança & Confiança

| Doc | Tema |
|---|---|
| [phases/10](phases/10-Fase-10-Security-Integrity-Module-Trust.md) | Security, Integrity & Module Trust: integridade, origem, assinatura |
| [phases/17](phases/17-Fase-17-Platform-Security-Trust-Hardening.md) | Security Hardening: endurecimento do Core/Runtime/pacotes/secrets |

## 9. Qualidade & Observabilidade

| Doc | Tema |
|---|---|
| [phases/14](phases/14-Fase-14-Observability-Telemetry-Diagnostics.md) | Observability, Telemetry & Diagnostics |
| [phases/15](phases/15-Fase-15-Platform-Quality-Testing-Release-Engineering.md) | Quality, Testing & Release Engineering |

## 10. Governança & Ciclo de Vida da Plataforma

| Doc | Tema |
|---|---|
| [phases/18](phases/18-Fase-18-Platform-Finalization-Architecture-Consolidation.md) | Finalização: revisão transversal antes dos módulos reais |
| [phases/19](phases/19-Fase-19-Public-Release-Readiness-Open-Ecosystem.md) | Public Release Readiness & Open Ecosystem |
| [phases/20](phases/20-Fase-20-Long-Term-Core-Governance-Ecosystem-Maintenance.md) | Governança de longo prazo pós-publicação |

## Exemplos de Módulos (referência)

| Doc | Tema |
|---|---|
| [examples/01](examples/01-System-Information-Service.md) | System Information Service (Service Module exemplo) |
| [examples/02](examples/02-System-Health-Check.md) | System Health Check (exemplo com dependência entre módulos) |
