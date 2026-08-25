# Plano — Fase 4: Marketplace & Package Manager (fechamento: ciclo activate/deactivate)

> Spec: docs/phases/04-Fase-04-Marketplace-Package-Manager.md
> Auditoria: tasks/phase-audit.md — Fase 4 está ~70%. Instalação/remoção/atualização/
> import/compatibilidade/operation log JÁ funcionam (test_phase4.py). Este plano fecha
> o que falta, seguindo as DIRETRIZES DO USUÁRIO registradas em phase-audit.md.

## Premissas validadas no código

1. ✅ `Module.is_enabled` existe no DB (default True) mas NADA o altera — sem endpoint,
   comando ou lógica de activate/deactivate
2. ✅ Remove já existe e funciona (`manager.remove()`, `DELETE /marketplace/remove/{id}`,
   hook `uninstall()` no contrato) — NÃO reimplementar
3. ✅ Plugin Loader carrega TODOS os módulos de modules/installed/ na startup — não
   consulta is_enabled (lazy loading do disable precisa ser implementado aqui)
4. ✅ Notification Foundation pronta (Fase 2): `NotificationService.create()` +
   API com campo module_id
5. ✅ NavigationBuilder não filtra por is_enabled — desativado ainda aparece no menu
6. ✅ Modelo de origem (source: catalog/local/development) inexistente

## Diretrizes do usuário (vinculantes)

- **Disable = poupar recursos**: módulo DISABLED não carrega entry_backend no startup,
  não loga, não aparece na navegação, rotas mudas
- **Hot-disable em runtime**: decidir abaixo
- **Remove**: não tocar (já existe)

## Decisão proposta — hot-disable

**Não implementar hot-disable nesta fase.** Desmontar imports já feitos em Python é
frágil (sys.modules compartilhado, risco de vazamento entre módulos). Semântica:

```text
Deactivate  → grava is_enabled=False + remove da navegação IMEDIATAMENTE
              (rotas existentes respondem 404 semanticamente até restart)
Activate    → grava is_enabled=True; entry_backend carrega no próximo boot
              OU imediatamente via mount_module_routers pontual (barato, seguro)
```

Ativação PODE ser quente (carregar sob demanda é seguro); desativação quente fica
documentada como limitação conhecida. Alinhado ao objetivo "poupar recursos" real:
o ganho principal vem do boot lazy.

## Slices

### Slice 1 — Backend: ciclo activate/deactivate (TDD)
- `PackageManager.activate(module_id)` / `.deactivate(module_id)`:
  - valida estado atual (INSTALLED↔DISABLED)
  - persiste `is_enabled` no DB via registry service
  - registra no operation_log
  - cria notificação (NotificationService) por evento: ativado/desativado
- Rotas: `POST /api/v1/marketplace/activate/{id}` e `/deactivate/{id}`
- Loader respeita is_enabled: módulos DISABLED ficam fora do mount e da navegação
  (NavigationBuilder filtra)
- Módulos desativados: rotas respondem 404 com mensagem clara

**Aceite:** testes de transição de estados, filtro de navegação, loader lazy,
notificações geradas.

### Slice 2 — Modelo de origem + integração SDK→Core notifications (TDD)
- Campo `source_type` (catalog|local|development) + `source_location` no modelo Module;
  preenchido no install/import (local default; catalog quando vier do repositório)
- Endpoint expõe source na resposta de /modules
- `NotificationsSDK.push()` passa a entregar no Core via POST /api/v1/notifications
  (com fallback silencioso para fila local se plataforma offline)

**Aceite:** origem visível na UI; push do SDK aparece no bell.

### Slice 3 — UI Marketplace/Modules + CLI
- MarketplacePage/ModulesPage: botões Ativar/Desativar/Remover distintos por estado
  (spec §12: nunca o mesmo botão para ações diferentes), badge de status e origem
- CLI: `techforge modules available|installed|activate|deactivate|remove` delegando
  ao Package Manager via HTTP (sem duplicar lógica, spec §19)
- Dashboard: contagem ativos/desativados/erro (spec §21 — leve)

**Aceite:** fluxo completo install→activate→deactivate→remove pela UI; browser E2E.

### Slice 4 — Docs + relatório + browser E2E final
- docs/architecture.md: ciclo de vida e semântica do disable
- README: seção lifecycle atualizada
- tasks/phase-04-report.md + auditoria → Fase 4 ✅

## Fora de escopo (spec §25)
Marketplace remoto funcional (RemoteRepositoryProvider continua stub), dependências
(Fase 8.1), assinatura digital (Fase 10), watched folder (§8 — explícito não fazer).

## Ordem
Slice 1 → 2 → 3 → 4; commit/push por slice após validação.
