---
title: Service Registry
category: arquitetura-core
domain: [arquitetura-core]
tags: [core, service-registry, capabilities, invocation]
order: 3
---

# Service Registry

O Service Registry é o mecanismo central de descoberta e consumo de
capacidades públicas fornecidas por Service Modules — permite que
Application Modules localizem e invoquem serviços sem conhecer sua
implementação interna.

## Modelo

```text
Service Module
      │ declara (docs/contracts/api.yaml: capabilities + exports)
      ▼
Service Contract          (APIYamlParser, sem duplicação)
      │ registrado
      ▼
ServiceDescriptor          (service_id, module_id, versões, status, contrato)
      │ discover / resolve
      ▼
Application Module
```

## Capabilities

Uma capability é um identificador estável e hierárquico do que um serviço
oferece (ex: `veeam.m365.calculate`, `aws.cost.read`). Declaradas dentro do
próprio `docs/contracts/api.yaml` já validado pelo `APIYamlParser` — nenhum segundo
lugar de metadados:

```yaml
service_id: veeam_m365
capabilities: [veeam.m365.calculate]
exports:
  - name: calculate_storage
    ...
```

## Estados

Module state (`INSTALLED`/`DISABLED`, ver [Module Registry](module-registry.md))
é separado de service availability:

| Status | Significado |
|--------|-------------|
| `REGISTERED` | Descoberto, ainda não avaliado como disponível |
| `ACTIVE` | Módulo `INSTALLED` + contrato válido — pode ser invocado |
| `DISABLED` | Módulo desativado — capacidades indisponíveis |
| `FAILED` | Módulo `service` sem contrato válido — registrado, mas sem exports invocáveis |
| `UNAVAILABLE` | Reservado para falha de disponibilidade sem ser desativação |
| `REMOVED` | Não aparece mais no registry (módulo removido) |

## Persistência

In-memory, reconstruível — mesmo padrão do
[Module Registry](module-registry.md) (fonte única de verdade). Nenhuma
tabela nova no banco. `service_registry.rebuild()` é chamado no boot e após
qualquer mutação (`activate`/`deactivate`/`install`/`update`/`remove`).

## API Python

```python
from app.service_registry.registry import service_registry

service_registry.find_service("veeam_m365")            # ServiceDescriptor | None
service_registry.find_by_module("veeam_m365")
service_registry.find_capability("veeam.m365.calculate")  # list[ServiceDescriptor]
service_registry.list_services()
service_registry.list_capabilities()                    # dict[capability, [service_id]]
service_registry.list_conflicts()                       # capabilities com >1 provider ACTIVE
service_registry.search("cost")                          # busca por keyword, todas as categorias
```

### Busca (discovery em escala)

Com muitos módulos instalados, listar tudo não escala. `search()` casa a
palavra-chave (case-insensitive, substring) contra `service_id`,
`capabilities` e nome/descrição de cada export — **atravessa todas as
categorias de módulo**, porque filtrar por categoria não responde "essa
capacidade já existe?" (a capacidade pode estar categorizada em qualquer
lugar). Exposto via `GET /api/v1/services?q=<termo>` e
`techforge services search <termo>`.

## Invocação

Chamada direta de função Python — sem round-trip HTTP interno, sem processo
extra:

```python
from app.service_registry.invoker import invoke

result = invoke("veeam_m365", "calculate_storage", users=500, mailbox_quota_gb=50)
```

`invoke()` resolve o serviço (status `ACTIVE` obrigatório), valida os
argumentos contra o `ServiceExport.parameters` do contrato (obrigatórios,
tipos básicos, sem argumento desconhecido) e importa dinamicamente
`backend/main.py` do módulo — reconhece tanto função de nível de módulo
(`hello_world.ping`) quanto método da instância `ModuleContract` exportada
como `module` (`veeam_m365.calculate_storage`).

## Erros

```text
SERVICE_NOT_FOUND · CAPABILITY_NOT_FOUND · SERVICE_DISABLED ·
SERVICE_UNAVAILABLE · CONTRACT_VIOLATION · INVALID_ARGUMENTS ·
SERVICE_EXECUTION_FAILED
```

Uma falha da função invocada nunca vaza stack trace interno ao chamador —
vira `ServiceExecutionFailedError`; o detalhe fica só no log do Core.

## Conflitos

Duas capabilities iguais entre serviços `ACTIVE` são **reportadas, nunca
resolvidas silenciosamente**: `list_conflicts()` retorna
`{capability: [service_ids]}`, e uma notificação (Notification Foundation,
com dedupe) é criada a cada novo conflito detectado.

## API REST

```
GET /api/v1/services                              → lista todos os serviços
GET /api/v1/services?q=<termo>                    → busca por keyword (§ Busca acima)
GET /api/v1/services/{service_id}                 → um descriptor
GET /api/v1/services/{service_id}/contract         → contrato completo
GET /api/v1/services/capabilities                  → mapa capability → [service_id]
GET /api/v1/services/capabilities/{capability}      → provedores de uma capability
```

Somente consulta — nenhuma rota genérica de invocação pública.

## CLI

```bash
techforge services list
techforge services search <termo>
techforge services show <service_id>
techforge services capabilities
techforge services contract <service_id>
techforge services status
```

## Developer Center e AI Context

O `ServiceContractPanel` exibe capabilities e status do serviço; o
`AIContextExporter` inclui ambos na seção "Service Contracts", para que uma
IA gerando um Application Module saiba quais serviços pode consumir e em
que estado estão.

## Pontos de extensão pendentes

- Resolução de conflito além de "reportar" (política de precedência).
- `ServiceContract.dependencies` já existe no modelo mas não é validado —
  Dependency Governance cobre esse ponto.
- Múltiplas versões simultâneas de um mesmo serviço.
