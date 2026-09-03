# Implementation Plan: Frontend design review — correções

Origem: revisão visual (`/frontend-design`) em Dashboard, Módulos, Marketplace
e Developer Center via screenshot real (Playwright, 1440×900, build Desktop).

## Task List

### Fase 1: Idioma (maior impacto, menor risco)
- [x] Task 1: Traduzir labels de status/tipo hardcoded em inglês pro português
      — `ModuleStatusBadge`, `CompatibilityBadge`, `TrustBadge`,
      `ModuleTypeBadge`, `LoaderJournalViewer`, `PackageCard`,
      `PackageDetailPanel`, e (achados na varredura) o strip de contagem de
      `ModulesPage` e os labels da sidebar de `DeveloperCenterPage`.
      Categorias/tags livres de manifesto (Examples, System, Sales) ficam
      como estão — são dado do módulo, não string de UI.

### Checkpoint: Fase 1
- [x] `npm run lint`/`npm run build` limpos
- [x] Screenshot das 4 telas confirma zero string de status em inglês

### Fase 2: Layout e consistência visual
- [x] Task 2: Altura de card consistente (`ModuleCard`) — `min-h-[2.5em]`
      na descrição reserva a altura de 2 linhas mesmo com texto de 1 linha
- [x] Task 3: Border adicionada na tag de categoria de `ModuleCard` — sem
      isso o `bg-subtle` tinha contraste quase nulo contra o card e a tag
      "sumia" ao lado do `ModuleTypeBadge` colorido
- [x] Task 4: Reordenado em `PackageCard` — `Desativar`/`Ativar` antes de
      `Remover` (ação de risco por último)

### Checkpoint: Fase 2
- [x] Screenshot confirma grid alinhado e badges uniformes

### Fase 3: Investigação (podem virar não-ação se a causa for por design)
- [x] Task 5: `hello_world` mostra `Invalid` em `/modules` mas não em
      `/marketplace` — **não é bug**. `manager.py:537-538` pula módulos
      INVALID de propósito ("invalid modules have no package to show");
      `/modules` é a tela de diagnóstico (estado bruto do registry),
      `/marketplace` só lista pacotes gerenciáveis. Nada alterado.
- [x] Task 6: Painel do Developer Center ficava vazio com o artigo "quase
      selecionado" — não era um estado travado, era hierarquia seção →
      lista de artigos → conteúdo funcionando como projetado, só que sem
      necessidade quando a seção só tem 1 artigo. Corrigido: `loadSection`
      auto-abre quando `articles.length === 1` e nenhum artigo já está
      selecionado (não conflita com a navegação por busca, que seta
      `selectedArticle` antes do load). Não aplicado a `modules` (tem
      filtro por módulo) nem a `dependency-graph`.

### Checkpoint: Fase 3
- [x] Ambos achados documentados com causa raiz antes de qualquer fix
- [x] Fix aplicado só onde havia bug real (Task 6); Task 5 ficou como
      não-ação documentada

## Fora de escopo (adiado, não esquecido)
- Espaço morto / grid fill (Dashboard, Módulos, DevCenter) — precisa de
  decisão de layout (masonry? menos padding? mais conteúdo?), não é um
  fix pontual. Registrar em `docs/limitations.md` se não for tratado aqui.
- Labels uppercase-tracked no Dashboard — escolha estética (é o "tell"
  genérico apontado pela skill de design, mas não é bug), fica pendente
  de decisão explícita do usuário antes de mexer.

## Risks and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Traduzir status pode quebrar algum teste de frontend que assert no texto em inglês | Baixo | `npm run build`/lint não pegam isso — buscar teste antes de mudar |
| Fix do Developer Center pode ser mudança de estado maior que o esperado | Médio | Investigar (Task 6) antes de decidir escopo do fix |
