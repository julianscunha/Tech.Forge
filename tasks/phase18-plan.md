# Plano — Fase 18: Platform Finalization & Architecture Consolidation

> Spec: docs/phases/18-Fase-18-Platform-Finalization-Architecture-Consolidation.md
> Pré-requisito: Fases 1-17 fechadas (ver `tasks/phase-audit.md`).
> Natureza da fase: **consolidação, não expansão** — revisão transversal,
> inventário, remoção de duplicação, validação de contratos. Não é uma
> fase de feature nova; a maior parte do trabalho é auditoria + fix de
> gaps reais encontrados, não código greenfield.

## Ponto de partida

`tasks/phase-audit.md` já contém boa parte do inventário exigido pelos
§4/§17 (status por fase, gaps conhecidos, decisões conscientes de
escopo) — construído incrementalmente ao longo das Fases 1-17. Esta
fase consolida/formaliza esse material em vez de recomeçar do zero, e
resolve os gaps 🔴 que ainda fazem sentido resolver agora (sem
antecipar Fase 13/18.1/19/20, que continuam adiadas).

**Fora de escopo (spec §48, decisão explícita)**: módulos reais
completos, marketplace complexo novo, redesign de UI sem necessidade,
migração pra servidor central, autenticação enterprise, microservices,
reescrita de componentes estáveis.

## Slices

### Slice 1 — Architecture Inventory + Dependency Map + Core Boundaries (§4-6)
Documentar (não implementar): inventário completo dos componentes do
Core (purpose/owner/interface/deps/lifecycle/persistence/tests/docs),
mapa de dependência oficial (UI→API→Application Services→Core
Services→Runtime/Registry→Infrastructure) e confirmação das fronteiras
Core/Module SDK/Module Runtime/Infrastructure/UI. Buscar ciclos,
acoplamento oculto, serviços duplicados, acesso direto a infra a partir
de módulos.
**Aceite**: `docs/architecture/` ganha os dois documentos; qualquer
ciclo/duplicação real encontrado vira item no Technical Debt Registry
(Slice 8) — não corrigido às cegas nesta slice.

### Slice 2 — Public Contracts Inventory + Versioning + Module Architecture/Lifecycle (§7-10)
Catálogo dos contratos públicos (ModuleManifest, ModuleExecutionContext,
ServiceContract, DependencyContract, StorageProvider, SecretProvider,
EventBus, MetricEmitter, DiagnosticProvider) com stability/versioning
policy. Validar modelo Application→Service (nunca o inverso) e o
lifecycle DISCOVERED→...→REMOVED contra o código real.
**Aceite**: catálogo documentado; qualquer contrato sem versão/policy
declarada ganha uma agora (Stable/Experimental/Deprecated).

### Slice 3 — Registry/Package/Dependency/Runtime consolidation (§11-14)
Confirmar fonte única de verdade pro registry (já é o in-memory
`registry` do module_engine, per CLAUDE.md) e ausência de resolver de
dependência paralelo, runtime oficial obrigatório. Corrigir qualquer
duplicação real encontrada (esperado: pouca, dado que essas fases já
foram fechadas com essa exigência).
**Aceite**: nenhum registry/resolver paralelo encontrado, ou os
encontrados são eliminados/documentados como débito.

### Slice 4 — Storage/Configuration consolidation (§15-16)
Revisar ownership de Platform Storage/Module Storage/Settings/Cache/
Logs/Secrets. Eliminar paths hardcoded, env vars duplicadas, arquivos
de config sobrepostos remanescentes.

**Checkpoint 1**: suíte completa (backend+CLI) sem regressão.

### Slice 5 — Documentation + AI Context consolidation + Example modules review (§17-20)
Auditoria de contradição entre docs oficiais (User Guide, Developer
Center, SDK, Service Contracts, Architecture, Security, Quality,
Release, Desktop). AI Context gerado só de fontes oficiais (sem regra
duplicada manual). Revisão dos módulos de exemplo (Hello World,
Example Service, etc.) — resolve o gap 🔴 conhecido do `entry_frontend`
não-compilado do `hello_world` (Fase 3, nunca fechado).

### Slice 6 — UI + API + CLI consolidation (§21-24)
Inventário de rotas (`/api/v1/*`) com purpose/schema/errors; inventário
de comandos CLI; navegação/Module Workspace/Dashboard revisados.
Remover endpoint/comando redundante real encontrado (esperado: nenhum
grande, dado padrão já seguido nas fases anteriores).

### Slice 7 — Observability + Security consolidation + Desktop/Server validation (§25-28)
Confirmar integração Logger/Events/Metrics/Diagnostics/Execution
History (Fase 14) e Package Manager/Trust/Integrity/SecurityPolicy/
SecretProvider (Fase 17) sem bypass acidental. Fluxo Desktop real
(install→launch→backend→ready→ui→module→shutdown) sem depender de
PowerShell/Python/Node exposto ao usuário final. Validar que
Desktop/Server não têm acoplamento impossível de migrar (paths,
storage, config, request context, concurrency, background execution).

**Checkpoint 2**: suíte completa + `techforge start` real (Desktop flow).

### Slice 8 — Performance baseline + Core weight + Failure isolation + Data integrity + Backward compat + Deprecation policy (§29-36)
Medir baseline real (startup, idle memory, module discovery/activation,
execução simples, shutdown) — registrar, não inventar metas. Revisar
dependências do Core (necessidade real). Provocar falhas
(module/dependency/storage/package/network/config) e confirmar
isolamento. Documentar política de deprecação (Mark→Document→Warn→
Migrate→Remove) — nova, formaliza o que já era prática implícita.

### Slice 9 — Quality Final Gate + Readiness Report + Technical Debt Registry + ADRs + Fechamento (§37-47, critérios finais)
Executar todos os quality gates existentes (static/unit/integration/
contract/architecture/security/doc compliance/module validation/build/
smoke/e2e). Gerar `docs/architecture/platform-readiness-report.md`
(formato do §38). Criar `docs/adr/` com as decisões-chave já tomadas
nas Fases 1-17 (ADR-001 Modular Architecture … ADR-006 Module Trust,
mínimo). Registro de dívida técnica simples a partir do que sobrou do
`tasks/phase-audit.md` (🔴 ainda abertos). Teste arquitetural §43 (o
módulo real futuro, Veeam M365 Sizing, pode ser construído sem alterar
Core internals?) — resposta documentada, sem implementar o módulo.
Fechamento: `tasks/phase-audit.md` + `tasks/phase-18-report.md`
consolidado contra os 42 critérios de aceitação do spec.

## Known Issues esperados (carregados do phase-audit.md, não bloqueiam a fase)

Itens 🔴 do phase-audit.md que fazem sentido resolver nesta fase (por
serem consolidação, não feature nova) vs. os que ficam registrados como
débito técnico formal (Slice 9) por dependerem de infraestrutura ainda
não construída (instalador Windows, servidor central) — decisão
específica por item feita durante a slice correspondente, não
antecipada aqui.
