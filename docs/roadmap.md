---
title: Roadmap — TechForge
category: governanca-setup
domain: [governanca-setup]
tags: [roadmap, limitations]
---

# Roadmap

## O que já está pronto

O Core do TechForge está completo e estável: engine de módulos (loader,
validação, navegação dinâmica), Package Manager (instalar, ativar,
desativar, atualizar, remover — todos com rollback), Service Registry e
Dependency Governance entre módulos, Module Runtime com lifecycle hooks
reais, Security/Integrity/Module Trust (assinatura, verificação,
publisher registry), Marketplace com catálogo multi-fonte, Configuration
& Persistence (migrations, config por módulo, Secret Store), Quality &
Release Engineering (CI, testes por nível, Release Readiness Report),
Observability & Diagnostics (logs estruturados, métricas, correlação de
falhas), e empacotamento Desktop (modo local sem dependências de
runtime expostas ao usuário final).

O detalhamento de cada componente vive em [`docs/architecture/`](architecture/)
e no [Developer Center](developer-center/); o que não está implementado ou
funciona com restrição conhecida está em [`limitations.md`](limitations.md).

## Decisões em aberto

Duas frentes maiores estão deliberadamente pausadas, aguardando uma
necessidade de negócio real em vez de serem antecipadas por especulação:

- **Suporte multiusuário / servidor central.** Hoje o TechForge é
  otimizado para uso single-user em desktop. Um modo servidor
  compartilhado (múltiplos usuários, autenticação, deployment
  centralizado) exigiria decisões de arquitetura significativas
  (concorrência, isolamento de dados por usuário, autenticação) que não
  fazem sentido implementar sem um caso de uso concreto puxando o
  design.
- **Ecossistema público de módulos.** A plataforma já suporta múltiplas
  fontes de catálogo (local, oficial, customizada via GitHub), mas abrir
  isso para publicação de terceiros em escala — com curadoria, revisão de
  segurança e distribuição pública — é uma decisão de produto e de
  governança que ainda não foi tomada.

Enquanto essas decisões não acontecem, o próximo passo natural é
**construir módulos reais** sobre o Core existente — a plataforma já foi
validada arquiteturalmente para suportar isso sem exigir mudanças no
Core em si.

## Como contribuir agora

Veja a seção "Contribuindo" do [README](../README.md). Contribuições de
módulos são bem-vindas através do catálogo de módulos; contribuições ao
Core devem primeiro abrir uma discussão, já que o princípio do projeto é
manter o Core enxuto e sem lógica de negócio.
