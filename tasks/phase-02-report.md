# Phase 02 Report — Core Architecture (fechamento: Notification Foundation)

## Architecture
Responsabilidades do Core definidas e separadas (module_engine / package_manager /
runtime / doc_engine). Notification Foundation adicionada como serviço do Core.

## Core Boundaries
Notificações são dados de plataforma (spec §13); nenhum dado de negócio no Core.

## App Shell
Consolidado. Bell placeholder do Header substituído por `NotificationBell`
funcional (badge de não-lidas, dropdown, marcar lida/todas).

## Registry Foundation
Sem alterações (já implementada).

## Runtime Foundation
Sem alterações (já implementada).

## Tests
199 passed (`cd core/backend && .venv/Scripts/python.exe -m pytest tests -q`).
Novos: `tests/test_phase2_notifications.py` (5 testes — níveis, validação 422,
unread count, mark read/read-all, filtro unread_only).

## Browser E2E (validação real, 2026-08-25)
Backend + frontend no ar; validado via navegador:
- Badge "3" no bell com 3 notificações não lidas ✅
- Dropdown lista as notificações com ícones por nível e "Marcar todas" ✅
- Marcar uma como lida → badge 3→2 ✅
- "Marcar todas" → badge some, unread-count=0 na API ✅
- Sem erros de JS no console; polling a cada 30s confirmado nos logs do backend ✅

## Build
Frontend build OK (`tsc -b && vite build`, gzip JS ~96 kB).

## API
```text
GET  /api/v1/notifications?unread_only=&limit=
POST /api/v1/notifications            {level, title, message?, module_id?}
GET  /api/v1/notifications/unread-count
POST /api/v1/notifications/{id}/read
POST /api/v1/notifications/read-all
```

## Database
Nova tabela `notifications` (id, level, title, message, module_id?, read, created_at),
criada automaticamente pelo init_db.

## Known Issues
- ESLint não instalado/configurado em core/frontend (script `lint` falha sem config).
  Pré-existente, fora do escopo desta fase; tratar na Fase 15 (Quality Gates).
