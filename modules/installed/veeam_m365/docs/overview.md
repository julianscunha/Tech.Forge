---
title: Veeam M365 Sizing — Overview
order: 1
tags: [veeam, m365, backup, sizing, microsoft-365]
---

# Veeam M365 Sizing

**Category:** Backup  
**Vendor:** Veeam  
**Version:** 1.0.0  
**Icon:** shield-check  
**Order:** 10

## Descrição

Sizing para Microsoft 365. Módulo dedicado ao cálculo de capacidade e dimensionamento de soluções Veeam Backup for Microsoft 365.

## Status

Stub — implementação pendente. A estrutura de manifesto, diretórios e contratos SDK está completa e validada.

## Campos do manifest

```yaml
icon: shield-check   # ícone de segurança para categoria Backup
color: blue          # identidade visual Veeam
order: 10            # primeiro na categoria Backup/Veeam
```

## Próximos passos

- Implementar calculadora de storage (Exchange, SharePoint, Teams, OneDrive)
- Adicionar suporte a múltiplos tenants M365
- Integrar com API Veeam para recomendações automáticas
