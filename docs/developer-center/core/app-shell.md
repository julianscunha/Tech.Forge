---
title: App Shell
order: 1
tags: [core, app-shell, layout, sidebar, header]
---

# App Shell

O App Shell é a estrutura visual permanente que envolve todos os módulos. É fornecido exclusivamente pelo Core e nunca pode ser modificado por um módulo.

## Componentes

```
┌─────────────────────────────────────────────────┐
│  Header (44px)                                  │
├──────────────┬──────────────────────────────────┤
│              │  Breadcrumb (30px)               │
│   Sidebar    ├──────────────────────────────────┤
│   (220px)    │                                  │
│              │   Área do Módulo (95%)            │
│              │   <Outlet />                      │
│              │                                  │
└──────────────┴──────────────────────────────────┘
```

### Header
- 44px de altura
- Toggle do sidebar
- Alternância de tema (claro/escuro)
- Notificações (sino)
- Propriedade exclusiva do Core

### Sidebar
- Largura: 220px (expandida) / 52px (recolhida)
- Construída automaticamente a partir dos manifests dos módulos
- Hierarquia: Categoria → Vendor → Módulo
- Ordenação pelo campo `order` do manifest
- Módulos não podem adicionar itens ao sidebar diretamente

### Área do Módulo
- Ocupa 95% da área útil
- Renderizada via React Router `<Outlet />`
- Cada módulo é montado na rota `/modules/<module_id>`

## Restrições para módulos

Os módulos **não podem**:
- Modificar o Header
- Adicionar itens ao Sidebar diretamente
- Abrir novas abas ou janelas
- Registrar elementos visuais globais

Os módulos **apenas** declaram metadados no `manifest.yaml` e o Core constrói a navegação automaticamente.
