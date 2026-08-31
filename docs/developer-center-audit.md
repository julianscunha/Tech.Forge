---
title: Auditoria do Developer Center
category: governanca-setup
domain: [governanca-setup]
tags: [documentation, developer-center]
---

# Auditoria de Indexação e Duplicidade — Developer Center

Este documento registra o resultado de uma auditoria sobre
`docs/developer-center/`: se todo o conteúdo ali é de fato publicado em
runtime pelo `doc_engine`, e se há duplicidade de conteúdo entre
arquivos.

## Como a indexação funciona

Não existe manifesto/allowlist de arquivos individuais. O
`DocIndexer` (`core/backend/app/doc_engine/indexer.py`) varre
`docs/developer-center/` automaticamente:

- Arquivos `.md` no nível raiz (`intro.md`, `index.md`, `README.md`) →
  categoria `INTRO`.
- Cada subdiretório é mapeado por **nome fixo** para uma categoria
  (`CORE_DOC_DIRS`, 9 entradas: `core`, `guides`, `sdk`, `reference`,
  `examples`, `service-modules`, `faq`, `marketplace`, `governance`).
  Dentro de um subdiretório reconhecido, a varredura é recursiva
  (`**/*.md`) — qualquer `.md` novo lá dentro é indexado
  automaticamente, sem precisar registrar em lugar nenhum.

**O único ponto de risco real**: um subdiretório com nome que não
esteja nessa lista fixa de 9 nomes seria silenciosamente ignorado
(nunca indexado, nunca aparece no Developer Center, sem erro nem
aviso). Hoje isso não é um problema — todos os 8 subdiretórios que
existem em disco (`core`, `guides`, `sdk`, `reference`, `examples`,
`service-modules`, `faq`, `governance`) batem exatamente com a lista
reconhecida. Mas é um risco silencioso pra manter em mente: criar uma
categoria nova exige lembrar de adicionar o nome em `CORE_DOC_DIRS`
antes de popular a pasta.

## Validação em runtime

Confirmado subindo a plataforma real e consultando
`GET /api/v1/docs/summary` e `GET /api/v1/docs/list`:

- **43 documentos indexados no total**, sendo **32 vindos de
  `docs/developer-center/`** e 11 de módulos instalados
  (`hello_world`, `system_health_check`, `system_information_service`).
- Os 32 arquivos `.md` de `docs/developer-center/` batem 1:1 com os 32
  documentos das categorias `intro`/`architecture`/`guide`/
  `sdk-backend`/`sdk-frontend`/`manifest-reference`/`examples`/
  `service-module`/`faq`/`governance` retornados pela API.
- **Nenhum arquivo órfão encontrado** — tudo que existe em disco está
  publicado.
- **Nenhum link morto encontrado** nos links internos
  (`](arquivo.md)`) dentro de `docs/developer-center/` — todos os
  destinos existem.

Plataforma parada de forma limpa ao final (`techforge stop`), sem
processo órfão.

## Duplicidade encontrada

Nenhum arquivo é literalmente idêntico a outro (checado por hash). Mas
três pares cobrem o mesmo assunto em profundidades diferentes, sem uma
fonte única clara — recomendado para revisão humana, não corrigido
aqui por exigir decisão de reorganização:

1. **`core/package-manager.md`** (visão geral curta: operações, formato
   `.mod`, API REST, compatibilidade) **vs.
   `core/package-manager-internals.md`** (documentação técnica
   profunda cobrindo os mesmos tópicos, mais hot reload, repository
   provider, campos de segurança, operation log). O primeiro parece um
   resumo do segundo — candidato a virar uma seção "Visão Geral" dentro
   do documento técnico, ou o técnico virar um apêndice linkado a
   partir do resumo.

2. **`core/module-registry.md`** (responsabilidades, estados, API
   Python de leitura/escrita, API REST, hot reload) **vs. a seção "5.
   ModuleRegistry" de `core/module-engine.md`**, que repete a mesma
   estrutura (Leitura / Escrita) sobre o mesmo componente. Parece uma
   extração que nunca foi consolidada de volta — candidato a manter só
   um dos dois, com o outro linkando pra ele.

3. **`guides/setup-windows.md`** (226 linhas, setup detalhado + 7
   seções de troubleshooting específicas do Windows) **vs.
   `guides/core-development-setup.md`** (66 linhas, os mesmos passos de
   setup backend/frontend em versão enxuta e multiplataforma). Público
   é o mesmo (quem vai rodar o Core localmente) — candidato a fazer um
   apontar pro outro explicitamente (ex: setup enxuto linkando "com
   problemas no Windows? veja o guia detalhado") em vez de ensinar o
   mesmo passo a passo duas vezes.

**Não são duplicidade** (públicos ou ângulos diferentes, mantidos como
estão): `core/runtime.md` (estado da plataforma) vs.
`core/module-runtime.md` (execução de módulo) — componentes distintos,
mesmo com nomes parecidos; `guides/it-deployment-guide.md` (TI
implantando pra usuários finais) vs. `guides/development-guide.md`
(desenvolvedor criando um módulo) vs. `guides/user-guide.md` (usuário
final) — três audiências diferentes.

**Observação fora de escopo**: dentro de `modules/installed/hello_world/docs/`,
tanto `overview.md` quanto `README.md` são indexados como documentos
`module` separados — mesmo módulo, dois arquivos de entrada. Não é
`docs/developer-center/`, mas vale revisar se `README.md` deveria ser
indexado como documentação de módulo ou é resíduo de scaffold.
