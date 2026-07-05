---
title: Veeam M365 Sizing — Exemplo Avançado
order: 2
tags: [veeam, m365, advanced, example, sharepoint, teams, retention]
---

## Objetivo

Demonstrar o uso completo da calculadora de sizing, incluindo todos os parâmetros opcionais e múltiplos cenários comparativos.

## Entradas

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `users` | int | sim | Número de usuários licenciados M365 |
| `mailbox_quota_gb` | float | sim | Quota por caixa de correio em GB |
| `sharepoint_gb` | float | não | Consumo total de SharePoint em GB |
| `teams_gb` | float | não | Consumo total de Teams em GB |
| `retention_years` | int | não | Período de retenção em anos |

## Saídas

`dict` com `total_gb`, `recommended_repo_gb` e `growth_factor` para cada cenário.

## Exemplo

```python
from backend.main import module

# Cenário 1: empresa pequena, retenção curta
small_company = await module.calculate_storage(
    users=100,
    mailbox_quota_gb=25,
    sharepoint_gb=500,
    teams_gb=200,
    retention_years=1,
)

# Cenário 2: empresa grande, compliance rigoroso
enterprise = await module.calculate_storage(
    users=5000,
    mailbox_quota_gb=100,
    sharepoint_gb=50000,
    teams_gb=15000,
    retention_years=7,
)

print(f"Pequena empresa: {small_company['recommended_repo_gb']:.0f} GB")
print(f"Enterprise:      {enterprise['recommended_repo_gb']:.0f} GB")

# Comparar fator de crescimento entre cenários
if enterprise["growth_factor"] > small_company["growth_factor"]:
    print("Enterprise tem maior margem de crescimento devido à retenção estendida.")
```

## Observações

- `retention_years` mais longos aumentam proporcionalmente o `growth_factor` — políticas de compliance (ex: 7 anos) elevam significativamente o storage recomendado.
- Para tenants multi-workload (Exchange + SharePoint + Teams), sempre informe os três campos de consumo para obter um sizing preciso.
- O cálculo não substitui uma análise de crescimento histórico real do tenant — use como estimativa inicial.
