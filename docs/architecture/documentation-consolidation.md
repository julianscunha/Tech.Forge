---
title: Documentation Consolidation
category: governanca-setup
domain: [governanca-setup]
tags: [architecture, consolidation]
---

# TechForge Core — Documentation + AI Context Consolidation

> Ver também [`core-inventory.md`](core-inventory.md),
> [`public-contracts.md`](public-contracts.md) e
> [`registry-consolidation.md`](registry-consolidation.md).

## Hello World frontend fix

Gap real, já registrado em [`docs/limitations.md`](../limitations.md)
como resolvido: o endpoint
de assets (`api/routes/module_assets.py::_ALLOWED_SUFFIXES`) só serve
`.js`/`.mjs` (e outros assets estáticos), nunca `.tsx` — confirmado no
código, não é suposição. `hello_world/manifest.yaml` apontava
`entry_frontend: frontend/index.tsx`, então o dynamic import do
`ModuleHost.tsx` sempre recebia 404 pra esse módulo em runtime.

**Corrigido**: `frontend/index.tsx` (React/JSX, nunca compilado)
substituído por `frontend/index.js` — JS puro (ESM), seguindo o mesmo
padrão já usado por `system_health_check/frontend/index.js` (sem
framework, `export default { render(container) }`, DOM API nativa).
Conteúdo replica a mesma UI de identificação que o `.tsx` antigo
descrevia (card + badge + linha de versão do SDK/CLI), sem lógica de
negócio nova. `manifest.yaml` atualizado (`entry_frontend:
frontend/index.js`); `index.tsx` antigo removido (morto assim que o
manifest deixou de apontar pra ele).

`docs/limitations.md` não lista mais este item — gap do `entry_frontend`
não compilado está resolvido.

**Achado colateral não corrigido**: `system_information_service/frontend/index.tsx`
tem exatamente o mesmo problema (`.tsx` não servível pelo allowlist),
mas não foi corrigido nesta slice — está fora do escopo explícito
(gap conhecido era só o do `hello_world`) e sua UI é mínima
(`export default function SystemInformationServicePage() { return null }`,
Service Module sem UI obrigatória). Registrado como novo item de débito
técnico no Technical Debt Registry.

## Contradições de documentação (§17)

Varredura focada (não exaustiva) comparando os documentos novos de
`docs/architecture/` contra `docs/architecture.md` (pré-existente) e
`docs/developer-center/core/module-trust.md`:

- **Lifecycle de módulo** (`docs/architecture.md:93-94`, `INSTALLED ⇄
  DISABLED` / `DISABLED → REMOVED`): consistente com o que
  `public-contracts.md` confirmou no código real. Sem
  contradição — o doc pré-existente já usa os nomes reais, não o
  enum de exemplo de 7 estados da spec.
- **Trust gate na instalação** (`module-trust.md`): já documenta
  corretamente que `DesktopSecurityPolicy.allows_install()` é sempre
  `True` e que `requires_warning()` "sinaliza aviso" — o texto em si
  não contradiz o código. O problema (achado já registrado em
  `registry-consolidation.md`) é que `requires_warning()` nunca é
  chamado por nenhum call-site — é uma lacuna de integração, não uma
  contradição de documentação. Já registrado no Technical Debt
  Registry, não duplicado aqui.

**Nenhuma contradição factual nova encontrada** nesta varredura entre
os documentos oficiais auditados.

## AI Context (§18)

`AIContextExporter.export()` (`app/doc_engine/__init__.py:82-177`)
monta o documento inteiramente a partir de:
- `doc_index.by_category(category)` — entradas indexadas pelo
  `DocIndexer` a partir dos arquivos reais de documentação
  (`docs/developer-center/`, docs de módulo);
- `indexer.all_contracts()` + `service_registry.find_service()` —
  dados ao vivo do registry, não texto fixo;
- seções seguintes (Dependency Governance, Trust, etc., não lidas
  linha a linha nesta slice) seguem o mesmo padrão de montagem por
  categoria/dados ao vivo, sem nenhuma string de regra de negócio
  hardcoded encontrada na função.

**Confirmado**: nenhuma regra duplicada manualmente — o exporter é
puramente estrutural (títulos/ordem de seção fixos), o conteúdo vem
sempre de fonte única (arquivos de doc indexados + estado ao vivo do
registry/service registry). Sem achado, sem correção necessária.

## Example modules review (§19-20)

Revisão rápida dos 3 módulos instalados contra os contratos
documentados em `public-contracts.md`:

| Módulo | `module_type` | Frontend | Conformidade |
|---|---|---|---|
| `hello_world` | service | `index.js` (corrigido nesta slice) | ✅ agora conforme |
| `system_health_check` | application | `index.js` (já conforme desde antes) | ✅ conforme — bom exemplo de referência pro contrato de frontend |
| `system_information_service` | service | `index.tsx` (não compilado) | ⚠️ mesmo gap do hello_world, não corrigido (ver acima) |

Nenhum dos 3 módulos foi reescrito além do fix pontual do
`hello_world`. `system_health_check` já é o exemplo correto do
contrato de frontend — recomendação (não implementada nesta slice,
fora de escopo): usar `system_health_check` como referência ao
corrigir `system_information_service` no futuro.

## Resumo

| Item | Resultado |
|---|---|
| Hello World frontend | Corrigido — gap 🔴 da Fase 3 fechado |
| Contradições de docs | Nenhuma nova encontrada na varredura focada |
| AI Context | Confirmado gerado só de fontes oficiais, sem regra duplicada |
| Example modules | `system_information_service` tem o mesmo gap de frontend não compilado — registrado como débito técnico no Technical Debt Registry |

**Pytest**: suíte completa — 949 passed, 3 skipped, sem regressão
(único teste que toca o asset `.tsx` do hello_world já era tolerante a
`(200, 404)`, ver `test_phase3_assets.py::test_module_asset_serves_entry_file`).
