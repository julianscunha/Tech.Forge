# Phase 06 Report — Launcher & Runtime

## Launcher (já existia)
single-instance (pidfile + liveness), health-based readiness, shutdown
ordenado (só PIDs próprios), splash, logs/launcher.log.

## Slice 1 — Modo Desktop (§10) — NOVO
- `SERVE_STATIC_FRONTEND` (settings, default false) + `FRONTEND_DIST_PATH`
- `_mount_static_frontend()` em main.py: StaticFiles `/assets` + SPA fallback
  para rotas não-API; API `/api/v1/*` tem precedência
- Launcher: desktop mode automático quando `dist/index.html` existe — nenhum
  processo node no runtime do usuário final

## Slice 2 — CLI (§16/§17) — NOVO
- `techforge logs [--backend|--frontend|--launcher] [-n LINES]`
- `techforge dev` → launcher `start --dev` (reload + vite dev server)

## Slice 3 — Runtime status (§14/§15) — NOVO
- `RuntimeState.DEGRADED`; `register_component_pid()`; `check_liveness()`
  on-demand (Windows: OpenProcess fallback)
- `/runtime/status` agora inclui `uptime_seconds`, `frontend_mode`
  (static|dev|none), `components` liveness

## Tests
311 passed, 3 skipped. Novos: test_phase6_desktop.py (5),
test_phase6_logs_dev.py (4), test_phase6_runtime_status.py (5).

## Browser E2E (2026-08-26)
Backend sozinho (`SERVE_STATIC_FRONTEND=true`, sem vite):
- `GET /` → 200 index.html ✅
- `GET /marketplace` → 200 SPA fallback ✅ (UI carrega, assets 200)
- `GET /api/v1/runtime/status` → frontend_mode=static, uptime ✅
- Navegação interna e help contextual funcionando na :8000 ✅

## Docs
docs/architecture.md: seção "Modos de Execução" com a decisão §10.

## Known Issues
- Supervisão é on-demand (sem watchdog loop) — conforme spec §15,
  diagnóstico > reinício automático
- Instalador/distribuição adiados (spec §18 — fora de escopo)
