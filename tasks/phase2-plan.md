# Plano — Fase 2: Notification Foundation (fechamento da Fase 2)

> Spec: docs/phases/02-Fase-02-Core-Architecture.md §10, §13, §18, §19, §21
> Auditoria de origem: tasks/phase-audit.md (única lacuna real da Fase 2)

## Premissas validadas

1. ✅ Bell placeholder existe em `core/frontend/src/components/layout/Header.tsx` (comentário "placeholder for Phase notifications")
2. ✅ Não há serviço/API/modelo de notificações no backend (`grep` confirma ausência)
3. ✅ DB do Core pode hospedar notificações (spec §13 lista "notificações" como dado legítimo do Core)
4. ✅ Suíte atual: 194 testes passando; padrão de teste = sync pytest + TestClient
5. ✅ Frontend usa zustand; navegação via store (`store/nav.ts`)

## Escopo (simples por exigência da spec — "evitar sistemas complexos")

### Slice 1 — Backend: modelo + serviço + API
- Model `Notification` em `app/models/` (id, level, title, message, module_id?, read, created_at)
- Enum `level`: info | warning | error | success
- Serviço `app/services/notifications.py`: `create()`, `list()`, `count_unread()`, `mark_read()`
- Rotas em `app/api/routes/notifications.py`:
  - GET /api/v1/notifications?unread_only=
  - POST /api/v1/notifications (uso interno/futuro por módulos via Core)
  - POST /api/v1/notifications/{id}/read
  - POST /api/v1/notifications/read-all
  - GET /api/v1/notifications/unread-count
- Tabela criada via init_db existente

**Aceite:** testes cobrindo criação por nível, unread count, mark read/read-all.

### Slice 2 — Frontend: substituir o bell placeholder
- Store `store/notifications.ts` (zustand): lista + unread count, polling leve (ex.: a cada 30s) ou refresh on focus
- Dropdown no Header: lista, badge de não-lidas, marcar como lida, "marcar todas"
- Tipos espelhando o contrato da API em `types/`

**Aceite:** bell funcional com badge e dropdown; lint/build passam.

### Slice 3 — Documentação
- `docs/architecture.md`: seção Notification Foundation (contrato + regra §13 de data ownership)
- Relatório final `tasks/phase-02-report.md` no formato da spec (§ Regra final)
- Atualizar `tasks/phase-audit.md` → Fase 2 ✅ 14/14

## Fora de escopo (spec §20)

WebSocket/tempo-real, notificações por e-mail, preferências de usuário,
notificações geradas por módulos de negócio, persistência de histórico longo.

## Ordem de execução

Slice 1 (TDD) → Slice 2 → Slice 3 → relatório → commit/push.
