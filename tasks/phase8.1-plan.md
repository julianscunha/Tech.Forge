# Plano — Fase 8.1: Dependency Governance

> Spec: docs/phases/08.1-Fase-08.1-Dependency-Governance.md
> Pré-requisito: Fase 8 (Service Registry) ✅ fechada — ver tasks/phase-08-report.md.

## Premissas validadas (investigação de código real)

1. ✅ `ModuleStatus` (`app/module_engine/enums.py`) hoje tem só
   `INSTALLED/DISABLED/INVALID/INCOMPATIBLE`. Todos os ~26 usos no código
   são comparação `==`/`in (...)` explícita, nenhum switch exaustivo —
   seguro adicionar `BLOCKED` sem quebrar nada.
2. ✅ `packaging` já está instalado no venv (transitivo, v26.0) e
   `packaging.specifiers.SpecifierSet(">=1.0.0,<2.0.0")` funciona contra
   `packaging.version.Version` — reuso direto, zero parser próprio (spec §9).
   Falta declarar em `requirements.txt` (hoje é dependência-fantasma).
3. ⚠️ `ServiceContract.dependencies: list[str]` (Fase 5/7, `api.yaml`) é uma
   lista simples de service_id, **sem** version_range/required/target_type,
   testada (`test_phase5.py`) e exposta em `/docs/contracts` +
   `ServiceContractPanel.tsx`. **Não é o mesmo conceito** da Fase 8.1 — fica
   intocada; a governança nova usa um campo **separado** no `manifest.yaml`.
4. ✅ `ParsedManifest` (`manifest.py`) aceita campo novo `dependencies: list[dict]`
   de forma aditiva (default `[]`, fora de `REQUIRED_FIELDS`) sem quebrar
   testes existentes.
5. ✅ Pontos de gancho no ciclo de vida já identificados:
   `lifecycle.py::activate_module` (antes de `set_status(..., INSTALLED)`),
   `lifecycle.py::deactivate_module` (antes de `set_status(..., DISABLED)`),
   `manager.py::remove()` (antes de `registry.deregister()`).
6. ✅ `service_registry.find_capability()`/`find_service()` já é a fonte
   oficial de discovery de capability — o `DependencyResolver` só consulta,
   não duplica (spec §23).
7. ✅ `hello_world`/`veeam_m365` não têm relação de negócio real entre si —
   não serão usados como Provider/Consumer fictício (decisão do usuário).
8. ✅ Página de detalhe de módulo já existe
   (`core/frontend/src/components/modules/ModuleDetailPanel.tsx`) — ponto
   natural pra seções Dependencies/Dependents/Status/Resolution (§21).

## Decisões arquiteturais (confirmadas com o usuário)

1. **Onde declarar**: campo novo `dependencies` em `manifest.yaml` (não em
   `api.yaml`) — `{target: {type: module|capability, id}, version_range,
   required}`. Sem mistura com o `dependencies` já existente do contrato.
2. **`BLOCKED`**: novo valor em `ModuleStatus` (não campo derivado à parte).
   Tratado como não-`INSTALLED` nos pontos que já excluem
   `DISABLED`/`INVALID`/`INCOMPATIBLE` da montagem de rotas e navegação —
   nenhuma mudança extra necessária nesses arquivos.
3. **Provider/Consumer de teste**: tudo via `tmp_path` (mesmo padrão das
   Fases 7/8) — sem criar módulo novo permanente no repo.
4. **Pacote novo**: `app/dependency_engine/` (nome sugerido pela própria
   spec §18), paralelo a `module_engine/`, `service_registry/`, `doc_engine/`.

## Novo pacote

```
core/backend/app/dependency_engine/
  models.py     # Dependency, DependencyStatus (enum §8), DependencyResolution
  parser.py     # DependencyParser — lê manifest_raw["dependencies"]
  validator.py  # estrutura, tipo, id, versão, direção Service↛Application, duplicidade
  graph.py      # DependencyGraph — arestas module→module (capability resolve via ServiceRegistry), DFS de ciclo
  resolver.py   # DependencyResolver — combina graph + ModuleRegistry + ServiceRegistry → DependencyResolution
  lifecycle.py  # hooks: check_can_activate / check_can_deactivate / check_can_remove
```

## Slices

### Slice 1 — Modelo + parser + BLOCKED (TDD) — §4/§5/§8/§9/§16
- `requirements.txt`: adiciona `packaging`.
- `ModuleStatus.BLOCKED` novo.
- `ParsedManifest.dependencies: list[dict]` (raw, passa direto do manifest.yaml).
- `dependency_engine/models.py`: `Dependency` (target_type, target_id,
  version_range, required, status, resolution — §5), `DependencyStatus`
  (SATISFIED/MISSING/INCOMPATIBLE_VERSION/DISABLED/CONFLICT/CYCLIC/
  OPTIONAL_UNAVAILABLE — §8).
- `dependency_engine/parser.py::DependencyParser.parse(manifest_raw) ->
  list[Dependency]`: lê a lista, usa `packaging.specifiers.SpecifierSet`
  pro `version_range`.

**Aceite:** manifest sem `dependencies` → lista vazia; manifest com
dependency de module e de capability parseados corretamente; version_range
inválido rejeitado no parse.

### Slice 2 — Validator (TDD) — §17
- `dependency_engine/validator.py::DependencyValidator.validate(module_type,
  dependencies, registry) -> list[DoDCheck-like]`: estrutura válida, `type`
  ∈ {module, capability}, `id` não vazio, `version_range` parseável,
  `required` bool, sem duplicidade (mesmo target duas vezes).
- Regra de direção (§3/§17): se módulo declarante é `service` e a
  dependência é `type: module` cujo alvo (se já instalado/conhecido no
  `ModuleRegistry`) é `module_type: application` → `INVALID_DEPENDENCY_DIRECTION`.
  Se o alvo não está instalado ainda, não dá pra checar — documentar a
  limitação (não é possível validar direção contra módulo desconhecido).
- Integrar ao `cli/techforge_cli/validators/module_validator.py` (seção
  nova, mesmo padrão do `_check_documentation_first`).

**Aceite:** service→application rejeitado quando o alvo é conhecido;
duplicidade rejeitada; `techforge validate-module` mostra os checks novos.

### Slice 3 — Graph + ciclos (TDD) — §6/§27
- `dependency_engine/graph.py::DependencyGraph.build(module_registry,
  service_registry) -> DependencyGraph`: aresta módulo→módulo (capability
  dependency resolve pro `module_id` do provider via
  `service_registry.find_capability()`).
- `detect_cycles() -> list[list[str]]` (DFS, caminho completo do ciclo).
- `topological_order()` pra ordem de ativação (§10).

**Aceite:** grafo sem ciclo retorna ordem válida; grafo com A→B→C→A detecta
o ciclo e devolve o caminho.

### Slice 4 — Resolver (TDD) — §7/§8/§15/§23
- `dependency_engine/resolver.py::DependencyResolver.resolve(module_id) ->
  list[Dependency]` com `status` preenchido: consulta `ModuleRegistry`
  (module dependency) ou `ServiceRegistry.find_capability()` (capability
  dependency), valida `version_range` contra a versão do provider,
  determina `SATISFIED/MISSING/INCOMPATIBLE_VERSION/DISABLED/CONFLICT/
  CYCLIC/OPTIONAL_UNAVAILABLE`.
- Conflito de capability (§15): se `service_registry.find_capability()`
  retorna mais de um provider ACTIVE e não há prioridade declarada →
  `CONFLICT` (reaproveita `list_conflicts()` da Fase 8, não duplica).

**Aceite:** todos os 7 estados cobertos por teste unitário com módulos em
`tmp_path`.

### Slice 5 — Integração com Lifecycle (TDD) — §10/§11/§12/§13/§14/§19/§20/§28/§29
- `dependency_engine/lifecycle.py`:
  - `check_can_activate(module_id) -> (bool, list[Dependency])`: bloqueia
    ativação se dependência `required` não `SATISFIED`; módulo vai pra
    `BLOCKED` em vez de `INSTALLED`.
  - `check_can_deactivate(module_id) -> (bool, list[str])`: bloqueia se
    existem dependents `INSTALLED` com dependência `required` apontando
    pra este módulo.
  - `check_can_remove(module_id) -> (bool, list[str])`: mesma regra do
    deactivate.
- `lifecycle.py::activate_module`/`deactivate_module` e
  `manager.py::remove()` chamam esses checks antes de mutar estado.
- Optional dependency ausente → `OPTIONAL_UNAVAILABLE`, não bloqueia (§14).
- Falha de runtime de um provider (§29): quando `service_registry` marca um
  serviço `FAILED`/`UNAVAILABLE`, dependentes com dependência `required`
  daquela capability são reavaliados no próximo `sync()` (reusa o hook já
  existente, sem cascata agressiva).

**Aceite:** teste de integração — Provider ativo, Consumer com dependência
obrigatória ativa normalmente; tentar desativar Provider com Consumer ativo
→ bloqueado; desativar Consumer primeiro → desativar Provider funciona.

### Slice 6 — API + CLI (TDD) — §25/§26
- Rotas: `GET /api/v1/modules/{id}/dependencies`,
  `/api/v1/modules/{id}/dependents`, `GET /api/v1/dependencies/validate`,
  `GET /api/v1/dependencies/graph`.
- CLI: `techforge modules dependencies <id>`, `dependents <id>`,
  `validate-dependencies`, `graph` — mesmo padrão HTTP-only de `services.py`.

**Aceite:** rotas e comandos testados (schema Pydantic próprio, CliRunner).

### Slice 7 — Frontend + Developer Center + AI Context + regra final
- `ModuleDetailPanel.tsx`: seções Dependencies (com resolução) / Dependents
  / Status (badge `BLOCKED` novo, mesmo padrão de `ModuleStatusBadge.tsx`).
- Visualização hierárquica textual do grafo (§22) — sem lib de grafo nova.
- `docs/developer-center/core/dependency-governance.md` (novo): como
  declarar, module vs capability dependency, direção, required/optional,
  ranges, conflitos, ciclos, impacto no lifecycle.
- `AIContextExporter`: seção "Dependency Governance" (mesmo padrão de
  "Service Contracts").
- Teste integrado completo do §30 (Provider + Consumer em `tmp_path`):
  install → resolve → activate (ordem correta) → tentar desativar Provider
  → bloqueado → desativar Consumer → desativar Provider → permitido →
  remoção.
- `tasks/phase-08.1-report.md` + `phase-audit.md` atualizado.
- Validar no navegador (Playwright, como na Fase 8).

**Aceite:** todos os 20 critérios §32 marcados, suíte completa +
`npm run build` limpos.

## Fora de escopo (spec §31, reafirmado)
Download automático de dependências, Marketplace remoto, resolvedor
distribuído, múltiplas versões simultâneas, execução em containers,
autenticação, permissões.

## Ordem
1 → 2 → 3 → 4 → 5 → 6 → 7; rodar suíte completa (`pytest tests -q` +
`npm run build`) após cada slice; commit/push por slice.
