---
title: Veeam M365 Sizing — Exemplo de Integração
order: 3
tags: [veeam, m365, integration, example, reporting]
---

## Objetivo

Demonstrar como um módulo de relatórios comercial pode consumir `veeam_m365` para gerar uma proposta de dimensionamento automaticamente.

## Entradas

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `tenant_profile` | dict | sim | Perfil do tenant M365 do cliente |

## Saídas

`dict` com a proposta consolidada, incluindo storage recomendado e estimativa de custo.

## Exemplo

```python
"""
sales_proposal_module/backend/main.py
========================================
Módulo comercial que depende de veeam_m365 para gerar propostas de backup.
"""
from techforge_sdk import create_sdk

sdk = create_sdk("sales_proposal_module")


async def generate_backup_proposal(tenant_profile: dict) -> dict:
    """
    Gera uma proposta de backup consultando o serviço veeam_m365.

    tenant_profile esperado:
        {
            "users": int,
            "mailbox_quota_gb": float,
            "sharepoint_gb": float,
            "teams_gb": float,
            "retention_years": int,
        }
    """
    # Importação direta (mesmo processo) — padrão recomendado para Service Modules
    from modules.installed.veeam_m365.backend.main import module as veeam_module

    sizing = await veeam_module.calculate_storage(
        users=tenant_profile["users"],
        mailbox_quota_gb=tenant_profile["mailbox_quota_gb"],
        sharepoint_gb=tenant_profile.get("sharepoint_gb", 0),
        teams_gb=tenant_profile.get("teams_gb", 0),
        retention_years=tenant_profile.get("retention_years", 1),
    )

    sdk.logger.info(
        "Proposta gerada: %.0f GB recomendados para %d usuários",
        sizing["recommended_repo_gb"], tenant_profile["users"],
    )

    return {
        "tenant": tenant_profile,
        "sizing": sizing,
        "estimated_monthly_cost_usd": sizing["recommended_repo_gb"] * 0.023,  # exemplo
    }


# Uso
proposal = await generate_backup_proposal({
    "users": 800,
    "mailbox_quota_gb": 50,
    "sharepoint_gb": 8000,
    "teams_gb": 3000,
    "retention_years": 3,
})
print(proposal)
```

## Declarando a dependência no manifesto

```yaml
# sales_proposal_module/docs/contracts/api.yaml
service_id: sales_proposal_module
dependencies:
  - veeam_m365
exports:
  - name: generate_backup_proposal
    description: Gera proposta de backup consultando veeam_m365
    parameters:
      - name: tenant_profile
        type: dict
        description: Perfil do tenant M365
        required: true
    returns:
      type: BackupProposal
    examples:
      - "proposal = await generate_backup_proposal({...})"
```

## Observações

- Módulos de serviço como `veeam_m365` devem ser importados diretamente quando ambos rodam no mesmo processo Python — evite overhead de HTTP para chamadas internas.
- Sempre declare a dependência em `dependencies` no contrato — isso permite que o Documentation Engine exporte o grafo de dependências no AI Context.
- O cálculo de custo é ilustrativo; substitua pela tabela de preços real do seu provedor de storage.
