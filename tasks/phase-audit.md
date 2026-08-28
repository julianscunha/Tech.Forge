# TechForge — Phase Audit (2026-08-25)

Método: specs de docs/phases vs código real + execução de testes.
Backend: 192 testes passando (`cd core/backend && .venv/Scripts/python.exe -m pytest tests -q`).
Frontend: sem testes (vitest não encontra arquivos *.test.*).

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
| 9 | Module Runtime Execution | ⚠️ mínimo | só runtime status + eventos startup/shutdown (fundação Fase 6) |
| 10 | Security & Module Trust | ⚠️ rudimentar | apenas checksum SHA-256 + TrustLevel enum nunca populado; sem assinatura/publisher registry |
| 11 | Marketplace Distribution | ⚠️ local-only | `RemoteRepositoryProvider` = NotImplementedError ×3 (`package_manager/repository.py:157-170`); marketplace/ vazio |
| 12 | Configuration & Persistence | ❌ | só settings.py global |
| 13 | Central Server Multi-User | ❌ | nada além de settings básicos |
| 14–20 | Observability / Quality / Desktop dist / Security hardening / Finalization / Public release / Governance | ❌ não iniciadas | fragmentos herdados: logging básico, single-instance launcher, PLATFORM_VERSION única |

## Hooks/stubs ativos (próximos alvos naturais)

- `RemoteRepositoryProvider.{list_available,get_package,fetch_mod_path}` — NotImplementedError (Fase 11)
- `Header.tsx` bell placeholder — aguarda Notification Foundation (Fase 2)
- `ModuleHost.tsx` — dynamic import de entry_frontend adiado (Fase 9)

## Nota para o plano da Fase 4 (decisão 2026-08-25)

Incluir no escopo da Fase 4 a integração `NotificationsSDK.push()` (sdk/python)
→ `NotificationService` do Core (`POST /api/v1/notifications`, campo module_id),
pois nenhuma fase atribui explicitamente esse canal. A Fase 4 é a primeira
consumidora da Notification Foundation (spec §20: install/fail/incompatibility/
activate/deactivate/remove devem notificar — "não criar um segundo sistema").
Logs de módulo (contexto de log próprio) ficam cobertos pela Fase 9 §22.

## Diretrizes do usuário para a Fase 4 (decisão 2026-08-25, confirmadas)

1. Semântica do disable = POUPAR RECURSOS: módulo DISABLED não carrega entry_backend
   no startup (lazy loading), não loga, não aparece na navegação, rotas não respondem.
2. Hot-disable em runtime: decidir no plano se entra ou fica para depois
   (desmontagem quente é mais complexa — imports já feitos).
3. Activate/deactivate via API + UI (botões Marketplace/Modules) + notificações
   via Notification Foundation (spec Fase 4 §20).
4. Remove JÁ EXISTE (manager.remove + DELETE /marketplace/remove + hook uninstall);
   não reimplementar.
