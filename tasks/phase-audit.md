# TechForge — Phase Audit (2026-08-25)

Método: specs de docs/phases vs código real + execução de testes.
Backend: 192 testes passando (`cd core/backend && .venv/Scripts/python.exe -m pytest tests -q`).
Frontend: sem testes (vitest não encontra arquivos *.test.*).

| Fase | Tema | Status | Lacunas principais |
|---|---|---|---|
| 1 | Foundation | ✅ 14/14 | health `/api/v1/platform/health` implementado (spec §5); docs/architecture.md e docs/development.md criados |
| 2 | Core Architecture | ✅ 13/14 | **Notification Foundation ausente** (sem serviço/API info/warning/error/success; bell é placeholder) |
| 3 | Module System | ⚠️ 11/16 | CLI `modules list/show/validate` inexistente; validador da CLI duplica lógica do Core; entry_frontend não carregado dinamicamente (ModuleHost estático); estados do registry divergem da spec (INSTALLED/DISABLED/INVALID/INCOMPATIBLE) |
| 4 | Marketplace & Package Manager | ⚠️ ~70% | **activate/deactivate ausente** ("Desativar ≠ Remover"); modelo de origem (catalog/local/dev); dependências no manifest; CLI de módulos |
| 5 | Developer Center & Doc Engine | ✅ ~85% | CLI `docs list/search/export-context`; help contextual (context_id); versionamento documental |
| 6 | Launcher & Runtime | ⚠️ ~75% | **modo Desktop com frontend estático** (launcher roda `npm run dev` sempre); comando `techforge logs`; supervisão contínua (DEGRADED proativo) |
| 7 | Documentation Compliance Checker | ✅ implementada | CLI de compliance dedicada (acessível via API `/docs/completeness`) |
| 8 | Service Registry | ❌ | `app/services/registry.py` é CRUD de Category/Module, não Service Registry |
| 8.1 | Dependency Governance | ❌ | sem dependency graph/resolução; manifest não valida dependências |
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
- Manifest sem campo `dependencies` (Fase 8.1)
