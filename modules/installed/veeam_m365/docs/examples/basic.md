---
title: Veeam M365 Sizing — Exemplo Básico
order: 1
tags: [veeam, m365, basic, example]
---

## Objetivo

Calcular o storage necessário para backup de Microsoft 365 com o mínimo de parâmetros.

## Entradas

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `users` | int | sim | Número de usuários licenciados M365 |
| `mailbox_quota_gb` | float | sim | Quota por caixa de correio em GB |

## Saídas

```json
{
  "total_gb": 25000.0,
  "recommended_repo_gb": 27500.0,
  "growth_factor": 1.1
}
```

## Exemplo

```python
from backend.main import module

result = await module.calculate_storage(
    users=500,
    mailbox_quota_gb=50,
)

print(result)
# {"total_gb": 25000.0, "recommended_repo_gb": 27500.0, "growth_factor": 1.1}
```

## Observações

- Parâmetros opcionais (`sharepoint_gb`, `teams_gb`, `retention_years`) usam valores padrão conservadores quando omitidos.
- `recommended_repo_gb` já inclui margem de crescimento — não é necessário aplicar buffer adicional manualmente.
