# Phase 04 Report — Marketplace & Package Manager (fechamento)

## Install / Remove / Update
Já implementados e testados (test_phase4.py). Remove NÃO foi alterado.

## Activate / Deactivate (novo — §9/§10)
- `POST /api/v1/marketplace/activate/{id}` · `/deactivate/{id}`
- Semântica de recursos (diretriz do produto): DISABLED não monta entry_backend
  no boot, sai da navegação, rotas mudas; arquivos preservados ("Desativar ≠ Remover")
- Flag persistida: `<module>/data/state.json` + `Module.is_enabled` no DB
- Activate é quente (monta rotas sob demanda); hot-unload documentado como
  evolução futura (Fase 9)

## Source Model (§4, novo)
`source_type` (catalog|local|development) + `source_location` no ParsedManifest
e na tabela Module. Default "local" em instalações por .mod/import.

## Notifications Integration (§20, novo)
`NotificationsSDK.push()` entrega via POST /api/v1/notifications (com fallback
silencioso para fila local offline). Eventos do ciclo de vida geram notificações:
ativado (success), desativado (warning).

## UI (§12)
PackageCard com botões distintos por estado: Install / Update / Remove /
Activate / Deactivate — nunca o mesmo botão para ações diferentes.

## CLI (§19)
`techforge modules activate|deactivate|remove <id>` delegando ao Core API.
Confirmação explícita no remove (--yes pula).

## Tests
271 passed, 3 skipped (backend 210 + CLI 61).
Novos: tests/test_phase4_lifecycle.py (8), tests/test_phase4_source.py (4).

## Browser E2E (2026-08-25)
- Deactivate do hello_world pela UI → status DISABLED, notificação criada,
  módulo fora da navegação, botão virou Activate ✅
- Activate pela UI → status INSTALLED ✅

## Build
Frontend OK. Backend sem regressões.

## Known Issues
- Hot-unload em runtime não implementado (documentado; Fase 9)
- RemoteRepositoryProvider segue stub (Fase 11)
