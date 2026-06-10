# hello_world Module

**Category:** Examples  
**Vendor:** TechForge  
**Version:** 1.0.0  
**Status:** Reference / Architecture validation

---

## Purpose

This module exists solely to validate the Phase 2 plugin architecture.
It is **not** a functional tool.

It demonstrates:
- A valid `manifest.yaml` with all required fields.
- The required directory structure (`backend/`, `frontend/`, `assets/`, `docs/`, `tests/`).
- The backend entry point contract (`router`, lifecycle hooks).
- The frontend entry point contract (default export, lifecycle hooks).
- Automatic registration in the ModuleRegistry at startup.
- Appearance in the Modules page with status `INSTALLED`.

## What it does NOT do

- No real business logic.
- No database interaction.
- No external API calls.
- No UI rendering (the frontend component is a stub).

## Lifecycle

| Event       | Behavior         |
|-------------|------------------|
| `install()` | No-op            |
| `enable()`  | No-op            |
| `disable()` | No-op            |
| `upgrade()` | No-op            |
| `health_check()` | Returns `{status: "ok"}` |
| `uninstall()` | No-op          |

## How to use as a template

Copy this entire directory to `modules/installed/<your_module_id>/`,
update `manifest.yaml`, and implement the backend and frontend entry points.
