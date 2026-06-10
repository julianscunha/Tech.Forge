# TechForge Architecture Specification v1.0

## 1. Visão Geral

TechForge é uma plataforma corporativa modular destinada à execução de ferramentas técnicas e comerciais através de módulos independentes.

O objetivo principal da plataforma é permitir que novas funcionalidades sejam adicionadas através de módulos sem necessidade de alterações no Core da aplicação.

A plataforma deve operar inicialmente em modo desktop/local e futuramente suportar implantação centralizada em servidores Linux com múltiplos usuários simultâneos.

---

# 2. Objetivos

## Objetivos Principais

* Plataforma modular baseada em plugins.
* Instalação local em qualquer desktop.
* Possibilidade de migração futura para ambiente servidor.
* Interface moderna, limpa e focada no conteúdo.
* Marketplace integrado para distribuição de módulos.
* SDK oficial para desenvolvimento de módulos.
* Sistema de validação e assinatura de módulos.
* Estrutura padronizada para desenvolvedores terceiros.

## Não Objetivos

* ERP.
* CRM completo.
* Sistema com múltiplos níveis complexos de permissão.
* Dashboard executivo com KPIs e gráficos excessivos.

---

# 3. Princípios Arquiteturais

## Módulo é o protagonista

A plataforma deve ocupar o mínimo possível da interface.

Meta:

* 95% da área útil destinada aos módulos.
* 5% destinada ao Core.

## Core desacoplado

O Core não deve conter regras de negócio dos módulos.

Responsabilidades do Core:

* Navegação.
* Registro de módulos.
* Marketplace.
* SDK.
* Configuração.
* Health Check.
* Logs.
* Atualizações.

## Desenvolvimento orientado a plugins

O sucesso da arquitetura será medido pela capacidade de adicionar novos módulos sem alterar o código do Core.

---

# 4. Stack Tecnológica

## Frontend

* React
* TypeScript
* Vite
* TailwindCSS
* shadcn/ui

## Backend

* Python
* FastAPI

## Banco de Dados

Modo Local:

* SQLite

Modo Servidor:

* PostgreSQL

Acesso sempre realizado através do SDK.

---

# 5. Estrutura do Projeto

```text
techforge/

core/

sdk/

cli/

marketplace/

modules/
├── repository/
└── installed/

shared/

docs/

config/

logs/
```

---

# 6. Estrutura de um Módulo

```text
module_name/

manifest.yaml

backend/

frontend/

assets/

docs/

tests/
```

---

# 7. Manifesto do Módulo

Exemplo:

```yaml
id: veeam_m365

name: Veeam M365 Sizing

version: 1.0.0

platform_min_version: 1.0.0

platform_max_version: 2.0.0

category: Backup

vendor: Veeam

author: TechForge Team

description: Sizing para Microsoft 365

entry_backend: backend/main.py

entry_frontend: frontend/index.tsx

signature:

checksum:

homepage:

documentation:
```

---

# 8. Categorias

Exemplo:

Backup

* Veeam
* Commvault

Virtualização

* VMware
* Hyper-V

Cloud

* AWS
* Azure

Comercial

* Leads
* Propostas

As categorias serão montadas automaticamente pelo Core.

---

# 9. App Shell

O Core fornecerá:

* Header compacto.
* Sidebar recolhível.
* Breadcrumb.
* Notificações.
* Marketplace.
* Configurações.

Os módulos serão carregados dentro da área principal da aplicação.

Não será permitido abrir módulos em novas abas.

Não será permitido que módulos controlem menus globais.

---

# 10. Ciclo de Vida dos Módulos

Métodos obrigatórios:

* install()
* enable()
* disable()
* upgrade()
* health_check()
* uninstall()

---

# 11. SDK

Backend:

* sdk.database
* sdk.storage
* sdk.logger
* sdk.settings
* sdk.notifications

Frontend:

* sdk.ui.card
* sdk.ui.table
* sdk.ui.form
* sdk.ui.modal
* sdk.ui.notification

---

# 12. Marketplace

Funcionalidades:

* Instalar módulo
* Atualizar módulo
* Remover módulo
* Verificar compatibilidade
* Validar assinatura
* Validar checksum

Categorias:

* Instalados
* Disponíveis
* Atualizações

---

# 13. Segurança

Todo módulo deverá possuir:

* Versionamento
* Checksum
* Assinatura
* Compatibilidade declarada

O sistema deverá exibir alertas quando houver:

* Assinatura inválida
* Checksum divergente
* Versão incompatível

---

# 14. Developer Center

Conteúdo:

* Introdução
* Estrutura dos módulos
* Manifesto
* SDK Backend
* SDK Frontend
* Exemplos
* Boas práticas
* Publicação

---

# 15. Roadmap

Fase 1

* Core
* Layout
* App Shell

Fase 2

* Module Loader
* Registry

Fase 3

* Marketplace

Fase 4

* Developer Center
* CLI

Fase 5

* Assinaturas
* Compatibilidade
* Health Checks

Somente após a conclusão dessas fases os módulos funcionais serão desenvolvidos.
