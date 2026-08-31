---
title: Observability, Security and Desktop Validation
category: governanca-setup
domain: [governanca-setup]
tags: [architecture, consolidation]
---

# TechForge Core — Observability, Security e Desktop/Server Validation

> Verificação empírica contra o código real e execução real do fluxo
> Desktop (`techforge start`/`stop`), não confirmação por memória de
> spec. Ver também [`core-inventory.md`](core-inventory.md),
> [`dependency-map.md`](dependency-map.md),
> [`registry-consolidation.md`](registry-consolidation.md) e
> [`storage-configuration.md`](storage-configuration.md).

## Observability integration

Caminho oficial de execução de módulo (`service_registry/invoker.py::invoke()`)
conecta, num único lugar:

- **Logger**: `bind_log_context(module_id=..., execution_id=...)` — todo log
  emitido durante a execução carrega o contexto.
- **Metrics**: `metric_emitter.counter("module_executions")`,
  `.histogram("execution_duration")`, `.counter("execution_failures")`.
- **Execution History**: `_persist_execution_history()` grava
  sucesso/falha + duração via `ExecutionHistoryService`.
- **Error Registry**: `capture_error("execution", ...)` no path de falha.

**EventBus não é usado por `invoke()`** — isso foi verificado como
intencional, não como lacuna: o `EventBus` é usado consistentemente para
eventos de ciclo de vida e segurança (`package_manager.*`,
`security.*`, `runtime.*`, `module_loader.scan`), não para telemetria de
execução por chamada — Metrics + Execution History já cobrem esse volume,
publicar um evento por execução de módulo inundaria o barramento sem
consumidor real hoje.

**Detalhe de implementação notável**: `_persist_execution_history()`
detecta se já está dentro de um event loop rodando e, nesse caso, pula a
gravação (comentário no código já documenta isso — Observability nunca
pode quebrar a execução real do módulo). Isso funciona corretamente hoje
porque a única rota HTTP que chama `invoke()`
(`api/routes/services.py::invoke_service`) é deliberadamente `def` (não
`async def`) — Starlette roda handlers síncronos numa threadpool, fora do
loop, então a persistência ocorre normalmente nesse caminho. A outra
chamadora, `services/module_quality.py::_check_contract` (verificação de
exemplos do contrato durante release readiness), roda dentro do loop e
portanto tem sua execução de teste **não** persistida em Execution History
— comportamento correto por acaso da arquitetura atual (rotas de
release-readiness são `async def`), não por um design explícito
documentado. Não é um bug hoje, mas é frágil: se um novo call site de
`invoke()` for adicionado dentro de uma rota `async def`, a Execution
History desse novo caminho seria silenciosamente descartada sem nenhum
aviso além do log em nível debug.

**Conclusão**: integração confirmada e funcional. Nenhum caminho
alternativo de execução de módulo (bypass de `invoke()`) encontrado.

## Security integration

Cadeia esperada: Package Manager → Trust → Integrity → Security Policy →
Secret Provider → Diagnostics → Observability.

- **Secret Provider**: `keyring` é importado em exatamente um arquivo do
  Core (`security/secret_store.py`) — nenhum módulo ou serviço acessa
  segredo por fora de `ModuleSecretStore`. Sem bypass encontrado.
- **Trust/Integrity no fluxo de instalação**: o achado já registrado em
  `registry-consolidation.md` (`SecurityPolicy.allows_install()`/
  `requires_warning()` nunca chamados em `install()`) foi verificado
  também no fluxo de **update** — `PackageManager.update()`
  (`package_manager/manager.py:347`) segue exatamente o mesmo padrão:
  regenera o `integrity.json` **depois** de extrair a nova versão
  (linha 447), sem checar trust/assinatura da nova versão antes de
  aplicá-la. É a mesma lacuna, não uma segunda — confirma com evidência
  de código que o gap descrito no outro documento se estende ao update.
- **Remove**: não precisa desse gate (remoção não introduz código novo
  não verificado) — nenhum achado aqui.
- **Diagnostics/Observability no fluxo de segurança**: eventos de
  segurança (`security.module_blocked`, `security.signature_valid`,
  `security.integrity_failure`, `security.secret_*`) são publicados no
  `EventBus` nos pontos corretos (`archive_safety.py`,
  `module_verification.py`, `module_trust/verification.py`,
  `security/secret_store.py`) — essa parte da cadeia está conectada.

**Nenhum bypass novo encontrado** além do já registrado — esta verificação
apenas confirmou que ele também cobre `update()`, com evidência de código
específica.

## Desktop flow real

Executado de ponta a ponta neste ambiente:

```
techforge status   → tudo STOPPED (estado limpo antes do teste)
techforge start    → "TechForge operacional em http://127.0.0.1:8000"
techforge status   → Launcher/Backend/Frontend/Database/Runtime READY
```

- **Sem exposição de PowerShell/Python/Node**: o único comando digitado
  foi `techforge start`/`status`/`stop` — nenhum uvicorn, node ou script
  precisou ser invocado manualmente.
- **Health check**: `GET /api/v1/health` respondeu com status por módulo
  (`healthy_modules`, `unhealthy_modules`, lista detalhada).
- **Listagem via registry**: `GET /api/v1/registry/modules` retornou
  `hello_world` com `entry_frontend: "frontend/index.js"` e
  `status: INSTALLED` — reflete a correção feita anteriormente para esse
  módulo.
- **Asset do módulo carregou de fato**: `GET
  /api/v1/modules/hello_world/assets/frontend/index.js` → `200`, corpo é
  um ESM válido com `export default { render }`, confirmando em runtime
  real (não só por inspeção de arquivo) que o módulo de referência
  funciona no fluxo Desktop.
- **Shutdown limpo**: `techforge stop` → "TechForge encerrado.",
  `techforge status` subsequente mostrou tudo `STOPPED`, sem processo
  órfão.

**Achado colateral, fora de escopo**: `GET /api/v1/health` reportou três
entradas `INVALID` (`some_module`, `test_module`, `unknown`) por
`manifest.yaml not found` — são diretórios remanescentes em
`modules/installed/` sem manifesto, prováveis artefatos de execuções de
teste anteriores, não módulos reais. Não corrigido aqui (limpeza de
ambiente, não achado de arquitetura) — mencionado para não ser
confundido com um problema do health check em si.

## Desktop/Server coupling assessment

Sem migrar nada — só mapeando o que uma futura decisão de servidor central
precisaria resolver:

| Área | Observação |
|---|---|
| Paths | Já usa `platformdirs`/`settings` de forma consistente (confirmado em `storage-configuration.md`) — baixo acoplamento. |
| Storage | SQLite via `aiosqlite`, single-writer — assume um único processo de backend. Migração pra Postgres já é intenção documentada no CLAUDE.md, não é surpresa nova. |
| Configuration | Settings centralizado, sem hardcode remanescente relevante (Slice de storage/config já tratou isso). |
| Request context | Rotas não assumem `localhost` explicitamente no código — CORS é configurável via settings. Sem acoplamento adicional encontrado além do já esperado de uma app desktop. |
| Concurrency | `service_registry/invoker.py::invoke()` é síncrono e depende de a rota ser `def` (threadpool) para não colidir com o event loop — funciona porque há apenas uma rota chamando `invoke()` hoje; um servidor com mais entradas para execução de módulo precisaria repensar esse acoplamento explicitamente (ver nota em Observability acima). |
| Background execution | `POST /marketplace/install-remote/{module_id}` usa `asyncio.create_task()` com progresso rastreado num `dict` **in-memory** (`InstallJobRegistry._jobs`, `package_manager/install_job.py:55`). Isso amarra o job ao processo que o criou — um servidor com múltiplos workers/instâncias não conseguiria que outro worker respondesse `GET /install-jobs/{job_id}` para um job criado em outro processo. É o ponto de acoplamento mais concreto encontrado nesta avaliação para uma futura migração a servidor multi-processo. |

Nenhum destes pontos é corrigido aqui — são observações para uma decisão
futura sobre servidor central, não itens de correção desta consolidação.

## Suíte de testes

`cd core/backend && .venv/Scripts/python.exe -m pytest tests -q` →
**948 passed, 1 failed, 3 skipped** na primeira execução da suíte
completa. O teste que falhou
(`test_phase14_dashboard_backend.py::TestHeaviestModulesService::test_snapshot_computes_failure_rate`,
`RuntimeError: coroutine raised StopIteration`) foi re-executado
isoladamente e **passou** — é flakiness pré-existente de ordem/estado
entre testes (não uma regressão introduzida por esta verificação, que não
alterou nenhum código de produção). Registrado aqui como observação, não
como item de débito de arquitetura.
