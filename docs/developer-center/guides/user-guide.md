---
title: Guia do Usuário
category: sdk-desenvolvimento
domain: [sdk-desenvolvimento]
tags: [guide, user-guide, phase-16, desktop]
---

# Guia do Usuário — TechForge Desktop

Este guia cobre o uso do TechForge do ponto de vista de quem só quer usar
a plataforma, sem precisar conhecer Python, Node ou terminal. Se você
precisa desenvolver ou depurar o Core, veja o
[Guia de Desenvolvimento](development-guide.md) e
[core/desktop-distribution](../core/desktop-distribution.md).

## Instalar

Hoje não existe um instalador gráfico (`.msi`/`.exe` de instalação) —
esse é um item ainda não implementado, registrado em
`tasks/phase-audit.md`. Instalação atual:

1. Obter o código-fonte (clone do repositório ou artefato de release).
2. Seguir [core-development-setup](core-development-setup.md) uma única
   vez pra preparar o `.venv` e o build do frontend.

Um build empacotado do backend (sem exigir Python instalado) pode ser
gerado com `scripts/build-backend.ps1` — ver
[core/desktop-distribution](../core/desktop-distribution.md).

## Iniciar

```bash
techforge start
```

Abre o navegador padrão automaticamente assim que o backend estiver
pronto. Rodar `techforge start` de novo com o TechForge já aberto reabre
a mesma janela/aba em vez de duplicar o processo.

## Usar o Dashboard

O Dashboard mostra status da plataforma, módulos instalados/ativos,
categorias e avisos. Não é o produto principal — os módulos são. Cards
podem ser reordenados (arrastar) e ocultados (engrenagem no canto).

## Abrir e instalar módulos

- **Abrir um módulo já instalado:** menu lateral → nome do módulo. Abre
  dentro do TechForge (nunca numa aba nova).
- **Instalar um módulo novo:** Marketplace → Catálogo → escolher módulo →
  Instalar.
- **Ativar/Desativar:** página do módulo → alternância de status.
  Desativar poupa recursos sem apagar dados; requer reinício pra liberar
  memória completamente (hot-unload ainda não existe).

## Atualizar um módulo

Marketplace → aba do módulo instalado → "Atualizar" (aparece quando há
versão nova disponível na fonte configurada).

## Diagnosticar um problema

- Página **Diagnostics**: erros recentes, execuções, uso de recursos.
- Se a plataforma não iniciar: a mensagem de erro traz um "Diagnostic
  Code" (ex. `TF-STARTUP-001`) — rode `techforge diagnostics` para mais
  detalhes.
- **Safe Mode** (`techforge safe-mode`): inicia só o Core, sem carregar
  nenhum módulo — use se um módulo estiver impedindo o uso normal, para
  desativar ou remover o módulo problemático e reiniciar normal.

## Desinstalar

Fluxo formal de desinstalação (com opção de manter/apagar dados) ainda
não existe — item registrado como pendente em `tasks/phase-audit.md`. Por
enquanto, remover a pasta local remove tudo (código e dados juntos, já
que a separação instalação/dados só se aplica de fato num build
empacotado e instalado via `platformdirs`).
