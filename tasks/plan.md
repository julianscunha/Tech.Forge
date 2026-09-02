# Implementation Plan: System Health module upgrade

Spec: `tasks/SPEC-system-health.md`

## Overview

Upgrade `system_information_service` (Service) with real hardware/OS read
exports, and rebuild `system_health_check` (Application) into a dashboard
with live metrics, a rule-based recommendation engine, confirm-to-apply
service actions, and a before/after report. Built bottom-up: cross-platform
data first, then Windows-specific data, then the app backend that consumes
it, then the app frontend, then packaging/PR.

## Two-repo note (discovered during Task 1)

`modules/installed/*` in this repo is gitignored on purpose (`/modules/` in
`.gitignore`) — it's the local, unpacked runtime copy the Core loads for
`techforge dev`, not source control. The real module source lives in the
sibling repo `D:\Github\Tech.Forge.Modules` (`submissions/<id>/` during a
PR, packaged into `.mod` by CI after merge — see its `CONTRIBUTING.md`).
Plan: keep developing/testing in this repo's `modules/installed/*` for fast
iteration; only at Task 14 copy the finished source into
`Tech.Forge.Modules/submissions/<id>/`, run `techforge validate-module`,
and open the PR from there.

## Architecture Decisions

- Service module exports stay read-only except one narrow write:
  `apply_service_action`, gated to a hardcoded whitelist — the only place in
  either module that mutates OS state.
- `windows.py` isolates every subprocess/PowerShell call behind small
  functions returning plain dicts/lists, so tests can feed captured sample
  output instead of depending on a real Windows host.
- Recommendation engine (`recommendations.py`) is pure functions over plain
  data — no I/O, no SDK calls inside it — so behavior tests never need
  `TestClient` or mocks.
- Frontend gets its own Vite/React/TS workspace under
  `frontend/` (package.json + src/), mirroring `lead_tracker/frontend`,
  compiling to the single `frontend/index.js` the manifest already points
  to. No new chart dependency — gauges/sparklines are hand-rolled SVG.

## Task List

### Phase 1: Data foundation (Service module)
- [ ] Task 1: Cross-platform hardware + live metrics exports (psutil)
- [ ] Task 2: Windows-specific read wrappers (services, drivers, update status)
- [ ] Task 3: `apply_service_action` (whitelisted, revertible)

### Checkpoint: Phase 1
- [ ] `pytest modules/installed/system_information_service/tests -q` green
- [ ] `ruff check` clean on touched files
- [ ] Manual: hit each new export via a Python REPL against the real machine, confirm real (non-mocked) values

### Phase 2: App backend (system_health_check)
- [ ] Task 4: `GET /dashboard` (hardware + live metrics + status)
- [ ] Task 5: Recommendation engine + `GET /recommendations`
- [ ] Task 6: `POST /recommendations/{id}/apply` + snapshot persistence (sdk.database)
- [ ] Task 7: `GET /report` (before/after aggregation)

### Checkpoint: Phase 2
- [ ] `pytest modules/installed/system_health_check/tests -q` green
- [ ] Manual: full curl/httpie walk of dashboard → recommendations → apply → report against the running Core

### Phase 3: App frontend
- [ ] Task 8: Vite/React workspace scaffold, builds to `frontend/index.js`
- [ ] Task 9: Dashboard view (hardware cards + live gauges)
- [ ] Task 10: Recommendations list + apply confirm UI
- [ ] Task 11: Report view (before/after)

### Checkpoint: Phase 3
- [ ] `npm run build` clean, no new dependency beyond react/react-dom/vite/typescript (same as lead_tracker)
- [ ] Manual: `techforge dev`, open the module in-app, run the full flow in a real browser (Playwright), screenshot each view

### Phase 4: Packaging and release
- [ ] Task 12: manifest.yaml version bumps, docs (overview.md, examples) for both modules, CHANGELOG
- [ ] Task 13: Full local verification (both modules' test suites, ruff, frontend build/lint)
- [ ] Task 14: Open PR against `Tech.Forge.Modules`, wait for review/approval, reinstall from catalog, retest live

### Checkpoint: Complete
- [ ] All Success Criteria in the spec are met
- [ ] PR merged, module reinstalled from the marketplace, retested live (not just local)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| PowerShell output format varies across Windows versions | Med | Parse via `-Command "... | ConvertTo-Json"` (structured, not text-scraped); tests use captured fixtures per task 2 |
| A whitelisted service turns out load-bearing on some machine | High | Whitelist ships with only universally-optional services (Fax, WMPNetworkSvc, MapsBroker); every apply stores prior state for revert; documented in module README as "Ask first" territory for any addition |
| Frontend build introduces bundle bloat | Low | No chart library; same dependency set as `lead_tracker` (react, react-dom only) |
| Tests become flaky by touching the real OS | Med | `windows.py` wrappers are the only OS boundary; everything above them is tested with synthetic/fixture data (mirrors TD-010 lesson: isolate the flaky boundary, don't let it leak) |

## Open Questions

None blocking — proceed per spec defaults.
