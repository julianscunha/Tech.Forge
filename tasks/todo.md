# Tasks: System Health module upgrade

Plan: `tasks/plan.md` · Spec: `tasks/SPEC-system-health.md`

## Task 1: Cross-platform hardware + live metrics exports (psutil)

**Description:** Add `get_hardware_info()` and `get_live_metrics()` to
`system_information_service`, using `psutil` (already in the Core venv).
Hardware = CPU model/cores/threads, RAM total, disk(s) with capacity. Live
metrics = a single point-in-time reading of CPU%, RAM used%, per-disk used%.

**Acceptance criteria:**
- [ ] `get_hardware_info()` returns real, non-mocked data on this machine
- [ ] `get_live_metrics()` returns a fresh reading on every call (no caching)
- [ ] Works on non-Windows too (psutil is cross-platform) — no `if platform ==` branch needed here

**Verification:**
- [ ] `cd core/backend && .venv/Scripts/python.exe -m pytest ../../modules/installed/system_information_service/tests -q`
- [ ] Manual: call both from a REPL, compare CPU core count against Task Manager

**Dependencies:** None

**Files likely touched:**
- `modules/installed/system_information_service/backend/main.py`
- `modules/installed/system_information_service/tests/test_hardware_metrics.py`

**Estimated scope:** S

---

## Task 2: Windows-specific read wrappers (services, drivers, update status)

**Description:** Add `modules/installed/system_information_service/backend/windows.py`
with `list_services()`, `list_drivers()`, `update_status()` — each shells out
to PowerShell with `-Command "... | ConvertTo-Json"` for structured output,
parses JSON, and returns `[]`/`{}` gracefully on non-Windows or on failure
(never raises up to the caller). Wire into three new service exports:
`get_windows_services()`, `get_windows_drivers()`, `get_windows_update_status()`.

**Acceptance criteria:**
- [ ] Each wrapper function takes a `runner` callable (default `subprocess.run`) so tests can inject fake output — no live PowerShell call in tests
- [ ] Non-Windows or PowerShell-missing returns an explicit "unavailable" shape, not an exception
- [ ] Real run on this machine returns plausible values (checked manually, not asserted in the automated test)

**Verification:**
- [ ] `cd core/backend && .venv/Scripts/python.exe -m pytest ../../modules/installed/system_information_service/tests -q`
- [ ] `ruff check modules/installed/system_information_service/backend`
- [ ] Manual: run each export locally, cross-check `list_services()` count against `services.msc`

**Dependencies:** None (parallel with Task 1)

**Files likely touched:**
- `modules/installed/system_information_service/backend/windows.py`
- `modules/installed/system_information_service/backend/main.py`
- `modules/installed/system_information_service/tests/test_windows.py`
- `modules/installed/system_information_service/tests/fixtures/*.json`

**Estimated scope:** M

---

## Task 3: `apply_service_action` (whitelisted, revertible)

**Description:** Add `apply_service_action(name, action)` to the service
module — `action` is `"stop"` or `"revert"`. Only accepts `name` from a
hardcoded `SAFE_TO_MANAGE` whitelist (module-level constant, documented in
the module README). Before stopping, reads and stores the current
start-type via `windows.py`; `revert` restores it. Returns the prior state
so the caller (Application module) can persist it if it wants its own
history.

**Acceptance criteria:**
- [ ] Rejects any `name` outside the whitelist with a clear error, no exception leak
- [ ] `stop` then `revert` round-trips to the original state (tested against a real, safe, already-stopped-by-default service on this machine, e.g. Fax)
- [ ] Whitelist has 3-5 entries, none system-critical, each with a one-line comment explaining why it's safe

**Verification:**
- [ ] `pytest ../../modules/installed/system_information_service/tests -q`
- [ ] Manual: apply + revert against a real whitelisted service, confirm via `services.msc` before/after

**Dependencies:** Task 2

**Files likely touched:**
- `modules/installed/system_information_service/backend/windows.py`
- `modules/installed/system_information_service/backend/main.py`
- `modules/installed/system_information_service/tests/test_apply_service_action.py`

**Estimated scope:** S

---

## Checkpoint: Phase 1
- [ ] All Phase 1 tests green, `ruff check` clean
- [ ] Every new export called manually against the real machine at least once

---

## Task 4: `GET /dashboard` (Application module)

**Description:** New route in `system_health_check` aggregating
`get_hardware_info`, `get_live_metrics`, `get_windows_services`,
`get_windows_drivers`, `get_windows_update_status` via `sdk.services.invoke`
into one response, reusing the existing `_unavailable()` fallback pattern
from `run_health_check` for when the dependency is missing/disabled.

**Acceptance criteria:**
- [ ] Single response shape combining all five reads
- [ ] Degrades per-section (e.g. drivers unavailable on non-Windows) rather than failing the whole response
- [ ] Existing `/health` endpoint (Fase 8.1 reference behavior) keeps working unchanged

**Verification:**
- [ ] `pytest ../../modules/installed/system_health_check/tests -q`
- [ ] Manual: `techforge dev`, `curl localhost:8000/api/v1/modules/system_health_check/dashboard`

**Dependencies:** Tasks 1, 2

**Files likely touched:**
- `modules/installed/system_health_check/backend/main.py`
- `modules/installed/system_health_check/tests/test_dashboard.py`

**Estimated scope:** S

---

## Task 5: Recommendation engine + `GET /recommendations`

**Description:** `backend/recommendations.py` — pure functions, one per
category (service/driver/update/hardware), each `(data) -> list[Recommendation]`.
A `build_recommendations(dashboard_data) -> list[Recommendation]` composes
them. Route calls `/dashboard`'s data internally (or re-fetches) and returns
the list.

**Acceptance criteria:**
- [ ] At least one real rule per category from the spec (service: a
      whitelisted service currently running; driver: unsigned driver present;
      update: last update older than N days)
- [ ] Every rule has its own unit test with synthetic input — no SDK/HTTP in these tests
- [ ] `applicable=True` only ever appears on service-category recommendations

**Verification:**
- [ ] `pytest ../../modules/installed/system_health_check/tests -q`
- [ ] Manual: with a whitelisted service running, confirm it shows up as a recommendation

**Dependencies:** Task 4

**Files likely touched:**
- `modules/installed/system_health_check/backend/recommendations.py`
- `modules/installed/system_health_check/backend/main.py`
- `modules/installed/system_health_check/tests/test_recommendations.py`

**Estimated scope:** M

---

## Task 6: `POST /recommendations/{id}/apply` + snapshot persistence

**Description:** Apply route resolves a recommendation id to its
service-action target, calls `sdk.services.invoke(..., "apply_service_action", ...)`,
and persists a snapshot row (`sdk.database`) before and after with a
timestamp and the metric set from `/dashboard`'s live-metrics section.
Rejects non-`applicable` recommendation ids outright.

**Acceptance criteria:**
- [ ] Snapshot table created on first use (simple `CREATE TABLE IF NOT EXISTS`)
- [ ] Apply on a non-applicable id returns 4xx, no state change
- [ ] Successful apply writes exactly two snapshot rows (before, after) linked by a shared `apply_id`

**Verification:**
- [ ] `pytest ../../modules/installed/system_health_check/tests -q`
- [ ] Manual: apply a real whitelisted-service recommendation end to end, inspect the module's sqlite db file for the two rows

**Dependencies:** Tasks 3, 5

**Files likely touched:**
- `modules/installed/system_health_check/backend/main.py`
- `modules/installed/system_health_check/backend/snapshots.py`
- `modules/installed/system_health_check/tests/test_apply.py`

**Estimated scope:** M

---

## Task 7: `GET /report` (before/after aggregation)

**Description:** `backend/report.py` reads snapshot rows grouped by
`apply_id`, computes % delta per metric (e.g. RAM used% before vs after),
and returns a list of `{apply_id, applied_at, recommendation_title, deltas}`.

**Acceptance criteria:**
- [ ] Handles zero snapshots (empty report, not an error)
- [ ] % delta math covered by a unit test with synthetic before/after rows
- [ ] Report is read-only — no side effects

**Verification:**
- [ ] `pytest ../../modules/installed/system_health_check/tests -q`
- [ ] Manual: after Task 6's real apply, hit `/report`, confirm the delta matches what you observed

**Dependencies:** Task 6

**Files likely touched:**
- `modules/installed/system_health_check/backend/report.py`
- `modules/installed/system_health_check/backend/main.py`
- `modules/installed/system_health_check/tests/test_report.py`

**Estimated scope:** S

---

## Checkpoint: Phase 2
- [ ] All Phase 2 tests green
- [ ] Manual curl walk: dashboard → recommendations → apply → report, against the real running Core

---

## Task 8: Vite/React workspace scaffold

**Description:** `frontend/` gets its own `package.json` (react, react-dom,
typescript, vite — same versions as `lead_tracker/frontend`), `vite.config.ts`
building a single ESM `frontend/index.js` matching the `default { render }`
contract `ModuleHost` expects, `src/main.tsx` as entry.

**Acceptance criteria:**
- [ ] `npm run build` produces `frontend/index.js` that exports `default { render }`
- [ ] No dependency beyond react/react-dom (+ their dev/type/build tooling)
- [ ] Old hand-written `frontend/index.js` content is replaced, not left alongside the new build output

**Verification:**
- [ ] `cd modules/installed/system_health_check/frontend && npm install && npm run build`
- [ ] Manual: `techforge dev`, open the module, confirm it still renders (even if just a placeholder) with no console error

**Dependencies:** None (parallel with Phase 1/2)

**Files likely touched:**
- `modules/installed/system_health_check/frontend/package.json`
- `modules/installed/system_health_check/frontend/vite.config.ts`
- `modules/installed/system_health_check/frontend/tsconfig.json`
- `modules/installed/system_health_check/frontend/src/main.tsx`

**Estimated scope:** S

---

## Task 9: Dashboard view (hardware cards + live gauges)

**Description:** React components rendering `/dashboard`'s hardware section
as summary cards and live metrics (CPU/RAM/disk %) as hand-rolled SVG
gauges (no chart library). Polls `/dashboard` on an interval for the "live"
feel.

**Acceptance criteria:**
- [ ] Renders real data from the running Core (not fixture data) when previewed manually
- [ ] Gauges are plain SVG/React, zero new npm dependency
- [ ] Unavailable sections (e.g. drivers on non-Windows) show a clear empty state, not a crash

**Verification:**
- [ ] `npm run build` clean
- [ ] Manual (Playwright): `techforge dev`, navigate to the module, screenshot the dashboard

**Dependencies:** Tasks 4, 8

**Files likely touched:**
- `modules/installed/system_health_check/frontend/src/Dashboard.tsx`
- `modules/installed/system_health_check/frontend/src/Gauge.tsx`
- `modules/installed/system_health_check/frontend/src/api.ts`

**Estimated scope:** M

---

## Task 10: Recommendations list + apply confirm UI

**Description:** List from `/recommendations`, each item showing category/
severity/title/description; `applicable=True` items get an "Aplicar" button
that opens a confirm step (explicit second click) before calling
`POST /recommendations/{id}/apply`.

**Acceptance criteria:**
- [ ] Non-applicable items never show an apply control
- [ ] Apply requires two distinct user actions (click + confirm), matching the spec's "never silent" boundary
- [ ] Loading/error states handled (apply failure shows a message, doesn't silently no-op)

**Verification:**
- [ ] `npm run build` clean
- [ ] Manual (Playwright): apply a real whitelisted-service recommendation through the UI, confirm the service state actually changed

**Dependencies:** Tasks 5, 6, 9

**Files likely touched:**
- `modules/installed/system_health_check/frontend/src/Recommendations.tsx`
- `modules/installed/system_health_check/frontend/src/ConfirmDialog.tsx`

**Estimated scope:** M

---

## Task 11: Report view (before/after)

**Description:** Renders `/report`'s list as before/after comparisons with
a computed "% melhorou" per metric, most recent first.

**Acceptance criteria:**
- [ ] Empty state when no applies have happened yet
- [ ] Shows real delta from a real apply performed in Task 10's manual check

**Verification:**
- [ ] `npm run build` clean
- [ ] Manual (Playwright): screenshot the report view after at least one real apply

**Dependencies:** Tasks 7, 9

**Files likely touched:**
- `modules/installed/system_health_check/frontend/src/Report.tsx`

**Estimated scope:** S

---

## Checkpoint: Phase 3
- [ ] `npm run build` clean, dependency set unchanged (react/react-dom only)
- [ ] Full manual flow walked in a real browser via Playwright, screenshots taken of all three views

---

## Task 12: Manifests, docs, CHANGELOG

**Description:** Bump `version` in both modules' `manifest.yaml`, update
`docs/overview.md` and `docs/examples/*.md` for both modules to describe
the new capabilities, add a CHANGELOG entry per module.

**Acceptance criteria:**
- [ ] Manifest versions bumped following semver (new features → minor)
- [ ] Docs describe every new export/route, no stale references to the old minimal behavior
- [ ] `integrity.json` regenerated if the Package Manager requires it for local install

**Verification:**
- [ ] Manual: read both `docs/overview.md` end to end, confirm nothing describes removed/changed behavior incorrectly

**Dependencies:** Tasks 1-11

**Files likely touched:**
- `modules/installed/system_information_service/manifest.yaml`
- `modules/installed/system_information_service/docs/overview.md`
- `modules/installed/system_health_check/manifest.yaml`
- `modules/installed/system_health_check/docs/overview.md`
- `modules/installed/*/CHANGELOG.md`

**Estimated scope:** S

---

## Task 13: Full local verification

**Description:** Run both modules' full test suites, `ruff check`, frontend
`npm run build`, and a full manual Playwright walk one more time after all
docs/manifest changes, to catch anything the individual task checkpoints missed.

**Acceptance criteria:**
- [ ] Both test suites green
- [ ] `ruff check` clean across all touched backend files
- [ ] Frontend build clean
- [ ] Every Success Criterion in `tasks/SPEC-system-health.md` checked off

**Verification:**
- [ ] `pytest ../../modules/installed/system_information_service/tests ../../modules/installed/system_health_check/tests -q`
- [ ] `ruff check modules/installed/system_information_service/backend modules/installed/system_health_check/backend`
- [ ] `npm run build` in the module frontend

**Dependencies:** Task 12

**Files likely touched:** None (verification only)

**Estimated scope:** XS

---

## Task 14: Open PR against Tech.Forge.Modules, release loop

**Description:** Push the finished module pair to the external
`Tech.Forge.Modules` repo as a PR, wait for review/approval, then — once
merged — reinstall the module from the marketplace in this TechForge
instance and retest live (not just the local dev copy).

**Acceptance criteria:**
- [ ] PR opened with a description linking back to the spec's objective
- [ ] After merge: module reinstalled via Marketplace, not just present under `modules/installed/`
- [ ] Live retest confirms the full dashboard → recommendation → apply → report flow on the reinstalled copy

**Verification:**
- [ ] Manual: full flow retested after reinstall, screenshots taken

**Dependencies:** Task 13

**Files likely touched:** None in this repo (target is `Tech.Forge.Modules`)

**Estimated scope:** S (process, not code)

---

## Checkpoint: Complete
- [ ] All Success Criteria in `tasks/SPEC-system-health.md` met
- [ ] PR merged, module reinstalled from catalog, retested live
