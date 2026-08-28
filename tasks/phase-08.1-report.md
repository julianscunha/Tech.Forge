# Phase 08.1 Report — Dependency Governance

## Slice 1 — Modelo + parser + BLOCKED
- `ModuleStatus.BLOCKED` (novo): "instalado, mas dependência obrigatória não
  satisfeita" — impossibilidade técnica, distinta do `DISABLED`
  administrativo. Todos os ~26 usos existentes do enum são comparação
  explícita, nenhum switch exaustivo — aditivo sem quebra.
- `ParsedManifest.dependencies: list[dict]` — campo raw novo, passthrough do
  `manifest.yaml`, separado do `dependencies` já existente em
  `docs/contracts/api.yaml` (conceito diferente, intocado).
- `app/dependency_engine/models.py`: `Dependency` (target_type, target_id,
  version_range, required, status, resolution), `DependencyStatus`
  (7 estados — §8), `TargetType` (module | capability).
- `app/dependency_engine/parser.py::DependencyParser.parse()`: usa
  `packaging.specifiers.SpecifierSet` — zero parser de versão próprio (§9).
  `requirements.txt` ganhou `packaging==26.3` (era dependência-fantasma).

## Slice 2 — Validator
- `app/dependency_engine/validator.py::DependencyValidator.validate()`:
  estrutura, tipo/id válidos, versão parseável, duplicidade (mesmo target
  duas vezes), e a regra arquitetural: Service Module ✗→ Application Module
  (só verificável quando o alvo já está instalado/conhecido).
- Integrado a `cli/techforge_cli/validators/module_validator.py` (novo passo
  `_check_dependency_governance`, mesmo padrão de `_check_documentation_first`).

## Slice 3 — Graph + ciclos
- `app/dependency_engine/graph.py::DependencyGraph.build()`: aresta
  módulo→módulo; dependência de capability resolve pro(s) `module_id`
  provider(es) via `ServiceRegistry.find_capability()` (Fase 8, sem
  duplicar discovery).
- `detect_cycles()` (DFS, caminho completo do ciclo), `topological_order()`
  (Kahn sobre out-degree — dependência ativa antes de quem depende dela).
- `export_mermaid()`: `flowchart TD` com aresta rotulada `module`/
  `capability` e destaque visual (`classDef`) dos nós em ciclo — decisão do
  usuário de preferir Mermaid a texto puro (spec só exige o mínimo textual).

## Slice 4 — Resolver
- `app/dependency_engine/resolver.py::DependencyResolver.resolve()`:
  combina `DependencyGraph` + `ModuleRegistry` + `ServiceRegistry` pra
  preencher os 7 estados de `DependencyStatus` por dependência declarada.
  Conflito de capability reaproveita `ServiceRegistry.list_conflicts()`
  (Fase 8); ciclo reaproveita `DependencyGraph.detect_cycles()` (Slice 3).

## Slice 5 — Integração com lifecycle
- `app/dependency_engine/lifecycle.py`: `check_can_activate`/
  `check_can_deactivate`/`check_can_remove` — consultados por
  `activate_module`/`deactivate_module` (`package_manager/lifecycle.py`) e
  `PackageManager.remove()` antes de mutar estado real.
- Ativação bloqueada → módulo vai para `BLOCKED` (não `INSTALLED`), retorna
  409 com as dependências não satisfeitas. Desativação/remoção bloqueadas
  quando existe dependent `INSTALLED` com dependência obrigatória apontando
  pro módulo (`RemoveStatus.BLOCKED`, novo).
- Dependência opcional ausente nunca bloqueia (`OPTIONAL_UNAVAILABLE`).

## Slice 6 — API + CLI
- `GET /api/v1/modules/{id}/dependencies`, `/modules/{id}/dependents`,
  `GET /api/v1/dependencies/validate`, `GET /api/v1/dependencies/graph`
  (retorna `{"mermaid": "flowchart TD\n..."}` já pronto pra renderizar).
- `techforge modules dependencies|dependents|validate-dependencies|graph` —
  mesmo padrão HTTP-only de `services.py` (zero lógica duplicada no CLI).

## Slice 7 — Frontend + Developer Center + AI Context + regra final
- `ModuleDetailPanel.tsx`: seções "Dependências" (com status resolvido) e
  "Dependentes"; `ModuleStatusBadge.tsx` ganhou o badge `BLOCKED`.
- Developer Center: seção nova "Dependency Graph" renderizando o Mermaid
  real via `mermaid` (única dependência nova do frontend nesta fase —
  confirmado que não havia nenhuma lib de diagramação antes).
- `AIContextExporter`: seção "Dependency Governance" com o Mermaid real da
  instalação (só aparece quando há arestas — instalação sem dependências
  declaradas não polui o contexto).
- `docs/developer-center/core/dependency-governance.md` (novo): declaração,
  direção, estados, grafo, API/CLI, fora de escopo.
- Teste integrado completo (§30, tudo em `tmp_path`, Provider+Consumer
  fictícios — decisão do usuário de não usar `hello_world`/`veeam_m365`
  para isso): resolve → SATISFIED → desativar Provider com Consumer ativo
  → bloqueado → desativar Consumer → desativar Provider → permitido →
  reativar (ordem correta) → remoção do Provider com Consumer ativo →
  bloqueada (`RemoveStatus.BLOCKED`).

## Decisões arquiteturais (confirmadas com o usuário antes do plano)
1. `dependencies` declarado em `manifest.yaml` (não em `api.yaml`) — sem
   mistura com o `dependencies` já existente do contrato de serviço.
2. `BLOCKED` como novo valor de `ModuleStatus`, não campo derivado à parte.
3. Provider/Consumer de teste inteiramente via `tmp_path` — nenhum módulo
   fictício novo permanente no repositório.
4. Grafo exportado como Mermaid (`flowchart TD`), não apenas texto/JSON —
   pensado para uma IA lendo o AI Context já visualizar a topologia real.

## Decisão de implementação (não perguntada, resolvida durante o Slice 4)
A spec não detalha se uma dependência **opcional** ausente deve produzir
`MISSING`/`DISABLED` (mesmo texto que uma obrigatória) ou um estado próprio.
Optou-se por `OPTIONAL_UNAVAILABLE` sempre que a condição de indisponibilidade
(alvo não encontrado, desativado, ou sem provider ACTIVE) recai sobre uma
dependência `required: false` — preserva a distinção semântica "isto está
faltando e é grave" vs. "isto está faltando e é esperado" sem introduzir um
oitavo estado fora do §8.

## Tests
369 passed, 3 skipped (suíte completa `core/backend/tests`) + 79 CLI
(`cli/tests`, inalterado — nenhum comando novo introduz teste unitário
próprio no pacote CLI, cobertura via integração no backend).
Arquivo novo: `test_phase8_1_dependency_governance.py` (63 casos cobrindo
os 6 primeiros slices + o teste integrado do Slice 7); `test_phase7_ai_context.py`
ganhou 2 casos para a seção "Dependency Governance".

## Backend / Frontend / API / Database
Nenhuma tabela nova. Campos novos são aditivos (`ModuleEntry.module_type`
já existia da Fase 8; `ParsedManifest.dependencies` é novo mas com default
`[]`). Frontend: `npm run build` limpo (`tsc -b && vite build`), única
dependência nova é `mermaid`.

## Build
`npm run build` ✅. `npm run lint` continua não rodando neste ambiente —
mesmo problema pré-existente já documentado no relatório da Fase 8
(`eslint` ausente como devDependency), não introduzido por esta fase.

## Known Issues
- Conflito de capability continua **reportado**, não resolvido — política
  de precedência é decisão de fase futura (mesma ressalva da Fase 8).
- `BLOCKED` não é recalculado automaticamente no boot para módulos cuja
  dependência ficou insatisfeita enquanto a plataforma estava desligada —
  só é atribuído no momento de uma tentativa explícita de `activate`. Fora
  do escopo dos hooks descritos no plano (activate/deactivate/remove); um
  recálculo de boot ficaria para uma fase futura de runtime execution
  (Fase 9) se necessário.
- Reavaliação de dependentes após falha de runtime de um provider (spec
  §29) é coberta pelo `sync()` já existente da Fase 8 (que roda após
  qualquer mutação do Service Registry) — nenhuma cascata agressiva de
  desativação automática foi implementada, por não estar no critério de
  aceite do plano.
