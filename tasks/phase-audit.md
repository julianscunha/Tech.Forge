# TechForge — Phase Audit (2026-08-30)

Método: specs de docs/phases vs código real + execução de testes.
Backend: 721 testes passando, organizados por nível via pytest markers —
unit/integration/contract/e2e/smoke/regression (`cd core/backend && .venv/Scripts/python.exe -m pytest tests -q`).
CLI: 113 testes passando. Frontend: sem testes automatizados (vitest não
encontra arquivos *.test.*) — `npm run lint`/`npm run build` funcionam
(gap do `eslint` ausente do `package.json`, pré-existente desde antes da
Fase 12, fechado na Fase 15).

| Fase | Tema | Status | Lacunas principais |
|---|---|---|---|
| 1 | Foundation | ✅ 14/14 | health `/api/v1/platform/health` implementado (spec §5); docs/architecture.md criado; setup em docs/developer-center/guides/core-development-setup.md |
| 2 | Core Architecture | ✅ 14/14 | Notification Foundation implementada (modelo/serviço/API/bell UI) — ver tasks/phase-02-report.md |
| 3 | Module System | ✅ 16/16 | CLI modules list/show/validate reutiliza o Core; dynamic entry_frontend (contrato micro-frontend render(container)); ver tasks/phase-03-report.md |
| 4 | Marketplace & Package Manager | ✅ fechada | ciclo activate/deactivate com lazy loading, source model, SDK notifications→Core; ver tasks/phase-04-report.md |
| 5 | Developer Center & Doc Engine | ✅ fechada | CLI `docs list/search/get/export-context`; help contextual (context_id + UI); versionamento documental — ver tasks/phase-05-report.md |
| 6 | Launcher & Runtime | ✅ fechada | modo Desktop (backend serve dist/, zero node); `techforge logs`/`dev`; runtime status c/ uptime+DEGRADED — ver tasks/phase-06-report.md |
| 7 | Documentation Compliance Checker | ✅ fechada | CLI validate-module c/ compliance (§12), notificações (§15), DoD no ai-context (§17), quality gate §9 (TODO/conteúdo vazio) e exemplo verificável §10 (hello_world+veeam_m365) — ver tasks/phase-07-report.md |
| 8 | Service Registry | ✅ fechada | `app/service_registry/` (discovery, invocação, erros tipados, conflito) + API `/services*` + CLI `techforge services` + AI Context — ver tasks/phase-08-report.md |
| 8.1 | Dependency Governance | ✅ fechada | `app/dependency_engine/` (parser, validator, graph+ciclos+Mermaid, resolver, lifecycle hooks) + API `/modules/{id}/dependencies\|dependents` + `/dependencies/validate\|graph` + CLI + Developer Center (grafo visual) + AI Context — ver tasks/phase-08.1-report.md |
| 9 | Module Runtime & Execution | ✅ fechada | `app/module_runtime/` (loader único, Runtime State separado do Administrative State, lifecycle hooks reais enable/disable/health_check, ExecutionContext, ModuleExecutionResult+cancellation/progress esqueleto) + API `/runtime/modules*` + CLI + Focus Mode + AI Context — ver tasks/phase-09-report.md |
| 10 | Security, Integrity & Module Trust | ✅ fechada | `app/module_trust/` (integrity manifest por-arquivo, Publisher Registry SQLite, TrustResolver, SignatureProvider abstrato) + API `/modules/{id}/integrity\|trust\|verify` + `/modules/trust` (lote) + `/publishers*` + CLI + Trust badge no frontend + AI Context — ver tasks/phase-10-report.md |
| 11 | Marketplace Distribution | ✅ fechada | `CatalogAggregator` (múltiplas fontes, cache TTL, detecção de conflitos), `OfficialCatalogProvider` (index.json), `CustomCatalogProvider` (GitHub API), `CatalogSourceConfig` CRUD, API `/catalog/*` com paginação/filtros, CLI `techforge catalog`, UI Catálogo 3-zona (sidebar + filtro + grid), Remote install jobs (ACQUIRING/VALIDATING/INSTALLING), Notificações (transição de fonte, instalação), Developer Center docs, AI Context — ver tasks/phase-11-report.md |
| 12 | Configuration & Persistence | ✅ fechada | Migrations via Alembic (substitui whitelist ad-hoc), `configuration.fields` no manifest + validação tipada (pydantic dinâmico) + persistência (`module_configurations`) + API/CLI/UI, Module Storage API key-value (`context.storage`, isolamento estrutural por module_id), `ModulePaths` (data/cache/exports/temp) + exclusão de integridade, Secret Store via `keyring` (`context.secrets`) + redação em log, `TTLCache` genérico extraído do Catálogo, config migration no update (`migrate_config` hook, rollback), `GET /api/v1/config` (gap do §29 nunca fechado antes), `context.configuration` conectado à config persistida (gap real encontrado na auditoria final — Fase 9 nunca conectou). Limitação conhecida, decisão do usuário: sem tipo lista/array na config de módulo — ver tasks/phase-12-report.md |
| 13 | Central Server Multi-User | ⏸️ adiada | decisão do usuário (2026-08-29): sem prioridade de multiusuário/servidor agora; foco é otimizar a experiência single-user. Nada além de settings básicos implementado. Revisitar só quando houver necessidade real de deployment centralizado. |
| 14, 16–20 | Observability / Desktop dist / Security hardening / Finalization / Public release / Governance | ❌ não iniciadas | fragmentos herdados: logging básico, single-instance launcher. Ordem recomendada (decisão 2026-08-30, foco single-user): 15→**14**→16→17→18; 18.1/19/20 condicionadas a decisão futura sobre ecossistema externo público (mesmo racional da Fase 13 adiada) |
| 15 | Platform Quality, Testing & Release Engineering | ✅ fechada | pytest markers (unit/integration/contract/e2e/smoke/regression) em ~600 testes + fixtures centralizadas para testes novos, architecture tests via `ast-grep`, contract tests genéricos (`extract_example_calls` executa exemplos reais de `api.yaml` contra `service_registry.invoker`), correção real do compatibility checker (quebrava em versão pre-release) e do `_assert_semver` do manifest (mesma causa raiz), `ruff` (backend) + `eslint` (frontend, gap pré-existente fechado) com 2 bugs reais corrigidos (`NameError` latente, `F821`), `GET /system/version` + `techforge version` (fecha versão hardcoded divergente no CLI e no `package.json` do frontend), `CHANGELOG.md` (Keep a Changelog, validado), Release Readiness Report (`GET /release/readiness`, `techforge release-check`) + Module Quality/Release Readiness por módulo (`GET /modules/{id}/quality\|release-readiness`, `techforge modules quality\|release-check`), `built_at` em `BuildResult` + `build-info.json` do frontend, canais de pre-release no manifest (`channel: stable\|beta\|development`, mecanismo apenas), CI (`.github/workflows/ci.yml`, 2 jobs) + smoke test + e2e crítico real (install→validate→activate→execute→deactivate→remove com `.mod` construído em disco), Developer Center + AI Context (Definition of Done) — ver tasks/phase-15-report.md |

## Limitações e Problemas Conhecidos (consolidado)

Levantado via busca por palavra-chave (`Limitações Conhecidas`/`Known Issues`)
em todo `tasks/phase-*-report.md`, não releitura integral de cada um — ver o
relatório de origem pra contexto completo de cada item. Objetivo: um lugar só
pra avaliar viabilidade de resolver, sem reabrir 15 arquivos toda vez.

**Legenda:** 🔴 gap real, ainda aberto · 🟡 edge case / cosmético, baixa prioridade · ⚪ decisão consciente de design, não é bug (fica registrado pra não ser "redescoberto")

| Origem | Item | Status | Nota |
|---|---|---|---|
| Fase 3 | `hello_world` entrega `entry_frontend` como `.tsx` não compilado — o contrato do Module Frontend exige JS/ESM compilado | 🔴 | Confirmado ainda verdade em 2026-08-30 (`modules/installed/hello_world/frontend/index.tsx`); o mecanismo de dynamic import (`ModuleHost.tsx`) já é real, só falta o módulo de referência servir o formato certo |
| Fase 4 | Hot-unload de módulo em runtime não implementado — desativar não descarrega módulo já montado, requer restart | 🔴 | Fase 9 (Module Runtime) citou como candidato mas não resolveu |
| Fase 4 | `RemoteRepositoryProvider` continua stub (`NotImplementedError`), comentário no código ainda cita "Phase 5" | 🟡 código morto | Funcionalidade equivalente foi entregue por outro caminho (`CatalogAggregator`/`CustomCatalogProvider`, Fase 11) — classe ficou órfã, candidata a remoção simples |
| Fase 6 | Launcher sem watchdog/restart automático (supervisão on-demand) | ⚪ | Spec pede explicitamente "diagnóstico > reinício automático" |
| Fase 7 | `cli/techforge_cli/validators/module_validator.py` duplica parte da validação §16 que já existe em `DocCompletenessChecker` | 🔴 | Citado de novo no relatório da Fase 8 sem correção |
| Fase 8 | Conflito de capability entre providers é **reportado**, não resolvido (sem política de precedência) | 🔴 | Citado de novo no relatório da Fase 8.1 sem correção |
| Fase 8.1 / 9 | `BLOCKED` / Runtime State não recalculados automaticamente no boot quando uma dependência fica insatisfeita com a plataforma desligada — só reavaliado em `activate`/`initialize` explícito | 🔴 | Mencionado 2x (Fase 8.1 e Fase 9), nenhuma fase seguinte resolveu |
| Fase 9 | `POST /runtime/modules/{id}/execute` e `/cancel` (previstos na spec) nunca implementados | ⚪ | Sem módulo real com ação de execução declarada — endpoint genérico seria vazio ou arbitrário; fica pra quando houver caso de uso |
| Fase 9 | `CancellationToken`/`ProgressReport` existem só como tipos testados, nenhum módulo usa | ⚪ | Mesma razão do item acima |
| Fase 10 | `TRUSTED` é estruturalmente inalcançável — sem `SignatureProvider` real, `techforge sign-module`/`verify-signature` não existem | 🔴 | Bloqueado por assinatura criptográfica real — candidato natural da Fase 17 (Security Hardening) |
| Fase 10 | `ModuleCLIValidator`/`AIContextExporter` (contextos síncronos) não consultam o Publisher Registry real — só o ID declarado no manifest | 🔴 | Gap de correção, não é decisão de design — a API async (`GET /modules/{id}/trust`) já faz certo |
| Fase 11 | Instalar/consultar uma versão antiga específica de um módulo — armazenamento já existe (`.mod` de toda versão publicada fica em `modules/<id>/`, nunca sobrescrito), mas nada expõe/instala uma versão que não seja a mais recente do `index.json` | 🔴 | O relatório original atribuiu isso à "Fase 15" — a Fase 15 real (Quality/Release Engineering) não cobriu esse escopo; item ficou órfão, ninguém pegou |
| Fase 12 | Secret Store sem fallback para SO sem backend `keyring` compatível (Linux headless sem D-Bus/Secret Service) | 🟡 | Só relevante se houver deploy Linux sem sessão gráfica |
| Fase 12 | Frontend nunca verificado visualmente em navegador real — sem ferramenta de browser automation disponível nas sessões até agora | 🟡 | Continua verdade; `npm run build` cobre compilação, não comportamento visual |
| Fase 15 | Marker de teste `regression` registrado mas nunca usado | ⚪ | Nenhum bug foi corrigido nas fases desde então que justificasse um |
| Fase 15 | `techforge validate-module` quebra no console PowerShell/Windows por encoding cp1252 (glifos do `rich`) | 🟡 | Não reproduzido em CI (Ubuntu/UTF-8); só afeta a experiência local do dev no Windows |

**Decisões conscientes de escopo, já adiadas por decisão explícita do usuário (não listar de novo — ver a tabela de fases acima)**: config de módulo sem tipo lista/array (Fase 12), Module Storage API só key-value sem provisionamento de schema relacional (Fase 12), Runtime/Execution Configuration como camadas distintas (Fase 12) — todas revisitar só quando um módulo real precisar, não especular agora.

**Já resolvidas** (mantido aqui só pra registrar que a busca as considerou, sem preencher a lista de pendências): `eslint` ausente do frontend (Fases 2/3/5/12 → resolvido na Fase 15); "Discovery em escala" do Service Registry sem busca (Fase 8 → resolvido no mesmo ciclo, ver `tasks/phase8-followup-capability-search.md`); `Header.tsx` bell placeholder (aguardava Fase 2 → `NotificationBell` real, confirmado em código); `ModuleHost.tsx` dynamic import de `entry_frontend` (aguardava Fase 9 → mecanismo real implementado, confirmado em código — só o item da Fase 3 acima, sobre o hello_world não estar compilado, continua aberto).

