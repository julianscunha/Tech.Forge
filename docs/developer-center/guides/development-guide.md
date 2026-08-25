---
title: Guia Completo de Desenvolvimento
category: sdk-desenvolvimento
domain: [sdk-desenvolvimento]
tags: [guide, tutorial, create-module, validate, package, install]
order: 1
---

# Guia Completo de Desenvolvimento de Módulos

Este guia leva você do zero à instalação de um módulo funcional no TechForge.

## Pré-requisitos

- Python 3.11+
- Node.js 18+
- TechForge CLI instalado (`cd cli && pip install -e .`)

## Passo 1 — Criar o scaffold

```bash
techforge create-module
```

O CLI solicitará:

```
Module id:    my_tool
Name:         My Tool
Category:     Backup
Vendor:       Acme Corp
Author:       Dev Name
Description:  Ferramenta para backup de dados.
```

Isso cria:

```
my_tool/
├── manifest.yaml
├── backend/main.py
├── frontend/index.tsx
├── assets/
├── docs/README.md
└── tests/test_module.py
```

## Passo 2 — Implementar o backend

Abra `backend/main.py`. A classe `MyToolModule` já está gerada com todos os hooks. Implemente conforme necessário:

```python
async def install(self) -> None:
    sdk.logger.info("Criando tabelas...")
    # await sdk.database.execute("CREATE TABLE IF NOT EXISTS ...")

async def health_check(self) -> HealthResult:
    # Verificar conectividade, recursos, etc.
    return HealthResult.ok("Sistema operacional.")
```

## Passo 3 — Implementar o frontend

Abra `frontend/index.tsx`. O `moduleConfig` e o componente padrão já estão gerados:

```tsx
export const moduleConfig: ModulePageConfig = {
  moduleId: "my_tool",
  title:    "My Tool",
  icon:     "puzzle",      // troque pelo ícone adequado
  // ...
}

export default function MyToolPage() {
  return (
    <ModulePage>
      <PageHeader title="My Tool" />
      {/* Implemente aqui */}
    </ModulePage>
  )
}
```

## Passo 4 — Validar

```bash
techforge validate-module my_tool/
```

Saída esperada (20 checks):
```
✓ Directory exists
✓ manifest.yaml present
✓ manifest.yaml parseable
✓ Required fields        (inclui icon e order)
✓ icon format
✓ order value
✓ Platform compatibility
✓ Backend: router exported
✓ Frontend: moduleConfig exported
...
✓ Module is valid and ready to install.
```

## Passo 5 — Empacotar

```bash
techforge package-module my_tool/ --output dist/
# → dist/my_tool-1.0.0.mod
# → dist/my_tool-1.0.0.mod.sha256
```

## Passo 6 — Instalar

**Via Marketplace (recomendado):**
```bash
cp dist/my_tool-1.0.0.mod modules/repository/
# Abrir Marketplace → aba Disponíveis → Install
```

**Via importação manual:**
- Marketplace → botão "Import .mod" → selecionar o arquivo

**Via linha de comando:**
```bash
cp -r my_tool/ modules/installed/
# Reiniciar o backend
```

## Passo 7 — Verificar

1. Backend: log deve mostrar `Module loaded: My Tool v1.0.0`
2. Sidebar: módulo aparece em `Categoria → Vendor → My Tool`
3. Módulos: status `INSTALLED`
4. Navegação: `/modules/my_tool` carrega o componente

## Estrutura de documentação

Adicione documentação em `docs/`:

```
my_tool/docs/
├── overview.md           ← visão geral (indexada automaticamente)
├── contracts/
│   └── api.yaml          ← contrato de serviço (se aplicável)
└── examples/
    ├── basic.md
    └── advanced.md
```

A documentação é indexada automaticamente ao instalar o módulo e fica disponível no Developer Center.
