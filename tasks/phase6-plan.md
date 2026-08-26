# Plano — Fase 6: Launcher & Runtime (fechamento das lacunas)

> Spec: docs/phases/06-Fase-06-Launcher-Runtime.md
> Auditoria: phase-audit.md — Fase 6 ~75%. Launcher funcional (single-instance,
> health-readiness, shutdown ordenado, logs). Este plano fecha o que falta.

## Premissas validadas

1. ✅ `launcher/techforge_launcher/__init__.py` sempre roda `_spawn([npm, "run", "dev"])`
   — não existe modo Desktop (spec §3/§10)
2. ✅ Backend NÃO serve os assets estáticos do frontend (sem StaticFiles)
3. ❌ `techforge logs` não existe (§16); start/stop/status existem
4. ❌ `techforge dev` não existe (§17) — dev mode é o único modo hoje
5. ✅ Runtime status endpoint existe (`/runtime/status`) mas sem uptime/frontend state
6. ⚠️ Supervisão: status() detecta PID morto on-demand; sem detecção proativa (§15)
7. ✅ Frontend build já gera `dist/` (vite build testado)

## Decisão arquitetural (spec §10 pede documentação da escolha)

**Backend servirá o frontend estático** (opção 1 da spec): menor nº de processos,
menor consumo de recursos — alinhado à diretriz "extremamente leve". No modo
Desktop o launcher sobe APENAS o backend (uvicorn), que serve dist/ e a API na
mesma porta. Zero node no runtime do usuário final.

## Slices

### Slice 1 — Modo Desktop: backend serve frontend estático (TDD) — spec §10
- `main.py`: se `settings.SERVE_STATIC_FRONTEND` (env, default false) e
  `core/frontend/dist` existir → montar StaticFiles em `/`
  (API continua em /api/v1; SPA fallback para index.html)
- Launcher ganha modo: `start(mode="desktop")` usa desktop por default quando
  dist/ existir; `techforge dev` força dev server
- Testes: static mount ligado/desligado, SPA fallback

**Aceite:** plataforma sobe só com backend; UI acessível na porta 8000.

### Slice 2 — `techforge logs` + `techforge dev` (§16/§17) (TDD)
- `techforge logs [--backend|--frontend|--launcher] [-n LINES]` — tail dos logs
- `techforge dev` — inicia backend reload + frontend dev server (fluxo atual)
- `techforge start` passa a usar Desktop mode quando dist/ existe

**Aceite:** comandos testados com CliRunner.

### Slice 3 — Runtime status enriquecido + supervisão leve (§14/§15) (TDD)
- `/runtime/status` inclui: uptime, frontend_mode (static|dev|none),
  modules_enabled count
- Detecção proativa simples: checagem de liveness dos PIDs em cada chamada de
  status → DEGRADED se processo morto (sem loop de supervisor)

**Aceite:** testes de estado DEGRADED.

### Slice 4 — Docs + browser E2E + relatório
- docs/architecture.md: decisão §10 (backend serve estático) + modos
- README: seção Desktop vs Dev atualizada
- Browser E2E: subir em modo desktop sem node rodando; validar UI + API na :8000
- tasks/phase-06-report.md + auditoria → Fase 6 ✅

## Fora de escopo (spec §18)
Instalador MSI, distribuição empacotada, multiusuário/server mode.

## Ordem
1 → 2 → 3 → 4; commit/push por slice após validação.
