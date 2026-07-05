---
title: SDK Frontend
order: 2
tags: [sdk, react, typescript, components, design-system]
---

# SDK Frontend (TypeScript / React)

O SDK Frontend fornece componentes e tokens de design para os frontends dos módulos. Use sempre os componentes do SDK para manter consistência visual com o Core.

## Importação

```tsx
import {
  ModulePage, PageHeader, Card, DataTable,
  Button, Modal, EmptyState, LoadingState,
  FormField, TextInput, Badge, NotificationToast,
} from '@techforge/sdk'
```

## Componentes principais

### ModulePage

Wrapper obrigatório para toda página de módulo.

```tsx
export default function MyPage() {
  return (
    <ModulePage>
      <PageHeader
        title="Minha Ferramenta"
        description="Descrição curta do que esta página faz."
        actions={<Button variant="primary">Ação</Button>}
      />
      {/* conteúdo */}
    </ModulePage>
  )
}
```

### Card

```tsx
<Card padding="md">   {/* none | sm | md | lg */}
  Conteúdo do card
</Card>
```

### DataTable

```tsx
const columns = [
  { key: "name",    header: "Nome" },
  { key: "status",  header: "Status", render: (row) => <Badge>{row.status}</Badge> },
  { key: "version", header: "Versão", mono: true, align: "right" },
]

<DataTable
  columns={columns}
  data={items}
  keyField="id"
  loading={isLoading}
  emptyLabel="Nenhum item encontrado."
/>
```

### Modal

```tsx
<Modal
  open={isOpen}
  onClose={() => setOpen(false)}
  title="Confirmar ação"
  size="sm"          // sm | md | lg
  footer={
    <>
      <Button variant="ghost" onClick={() => setOpen(false)}>Cancelar</Button>
      <Button variant="primary" onClick={handleConfirm}>Confirmar</Button>
    </>
  }
>
  Conteúdo do modal
</Modal>
```

### Button

```tsx
<Button variant="primary">Salvar</Button>
<Button variant="secondary">Cancelar</Button>
<Button variant="ghost">Ver mais</Button>
<Button variant="danger">Excluir</Button>
<Button loading={isSaving}>Processando…</Button>
```

### EmptyState / LoadingState

```tsx
<EmptyState
  title="Nenhum resultado"
  description="Crie um novo item para começar."
  icon={<BoxIcon />}
  action={<Button variant="primary">Criar</Button>}
/>

<LoadingState message="Carregando dados…" />
```

## moduleConfig — contrato obrigatório

Todo módulo frontend deve exportar um `moduleConfig`:

```tsx
import type { ModulePageConfig } from '@techforge/sdk'

export const moduleConfig: ModulePageConfig = {
  moduleId:    "my_module",       // deve bater com o id do manifest
  title:       "My Module",
  icon:        "database",        // ícone lucide-react (kebab-case)
  category:    "Backup",
  vendor:      "Acme",
  route:       "/modules/my_module",
  description: "Descrição curta.",
}

export default function MyModulePage() { ... }
```

## Tokens de design

```tsx
import { colors, spacing, radius, cls } from '@techforge/sdk'

// Botão primário com tokens
<button className={cls.buttonPrimary}>Salvar</button>

// Superfície elevada
<div className={cls.card}>Conteúdo</div>
```
