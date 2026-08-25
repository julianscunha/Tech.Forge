---
title: Documentation First Principle
category: governanca-setup
domain: [governanca-setup]
tags: [governance, documentation, definition-of-done, contracts, examples, dod]
order: 1
---

# §16 — Documentation First Principle

> Nenhuma funcionalidade é considerada concluída sem documentação publicada.

A documentação é parte integrante da funcionalidade — não um anexo opcional. Este princípio rege todos os componentes da plataforma: SDK Backend, SDK Frontend, Service Modules, Application Modules, APIs Públicas, Contratos, Templates, CLI e extensões do Marketplace.

## Definition of Done (DoD)

Toda funcionalidade precisa de **quatro** elementos para ser considerada pronta:

| Elemento | Descrição |
|---|---|
| **Implementação** | Código funcional |
| **Contrato** | Definição formal de entrada e saída |
| **Documentação** | Publicada no Developer Center |
| **Exemplo** | Pelo menos um exemplo funcional |

## Module Type: service

Módulos declarados com `module_type: service` no manifesto têm exigências adicionais:

```yaml
id: my_service
module_type: service
```

Esses módulos **devem** publicar:

```
docs/
├── overview.md
├── contracts/
│   └── api.yaml
└── examples/
    ├── basic.md
    ├── advanced.md
    └── integration.md
```

## Contrato — campos obrigatórios por export

Cada item em `exports` do `api.yaml` deve declarar:

```yaml
exports:
  - name: get_monthly_costs
    description: Retorna custos mensais consolidados.
    parameters:
      - name: start_date
        type: date
        required: true
      - name: end_date
        type: date
        required: true
    returns:
      type: CostSummary[]
    examples:
      - "result = await get_monthly_costs(start, end)"
```

| Campo | Obrigatório |
|---|---|
| `name` | sim |
| `description` | sim |
| `parameters[].type` | sim (para cada parâmetro) |
| `parameters[].required` | sim (para cada parâmetro) |
| `returns` | sim |
| `examples` | sim — pelo menos 1 |

O `techforge validate-module` e o `DocCompletenessChecker` do backend verificam automaticamente cada um desses campos.

## Os três tiers de exemplo

| Arquivo | Propósito |
|---|---|
| `basic.md` | Uso mínimo — menor caminho possível até um resultado |
| `advanced.md` | Uso completo — todos os parâmetros, cenários comparativos |
| `integration.md` | Consumo por **outro módulo** — demonstra dependências entre serviços |

Cada exemplo segue a estrutura padronizada:

```markdown
## Objetivo
## Entradas
## Saídas
## Exemplo
## Observações
```

## Documentação AI-Friendly

Toda documentação deve:

- Usar **Markdown puro**, sem dependência de renderizadores proprietários
- Seguir a estrutura previsível: Objetivo → Entradas → Saídas → Exemplo → Observações
- Conter **exemplos completos**, nunca pseudocódigo
- Usar **terminologia consistente** com o restante da plataforma
- Declarar **contratos explícitos** — nunca depender de comportamento implícito

Essas diretrizes garantem que tanto desenvolvedores humanos quanto modelos de IA consigam consumir a documentação sem ambiguidade.

## Verificando completude

### Via CLI

```bash
techforge validate-module modules/installed/my_module
```

Os checks prefixados com `§16` no relatório correspondem a este princípio.

### Via API

```bash
GET /api/v1/docs/completeness                 # todos os módulos
GET /api/v1/docs/completeness/{module_id}      # um módulo específico
```

Resposta:

```json
{
  "module_id": "my_module",
  "module_type": "service",
  "is_complete": true,
  "score": 100.0,
  "missing": [],
  "checks": [
    {"name": "Implementation: backend", "passed": true, "required": true, "detail": "..."},
    {"name": "§16 Example: basic.md",   "passed": true, "required": true, "detail": "..."}
  ]
}
```

## Governança do Marketplace

> Nenhuma funcionalidade poderá ser publicada no Marketplace sem atender aos requisitos de documentação definidos nesta seção.

Esta regra será aplicada como gate de publicação em fases futuras do Marketplace. Por ora, o `DocCompletenessChecker` serve como ferramenta de auditoria — desenvolvedores devem rodar a verificação antes de empacotar (`techforge package-module`).

## Auto-documentação futura

A arquitetura está preparada para gerar documentação automaticamente a partir de:

- **Decorators** do SDK (`@sdk.document(...)`)
- **Contratos** já estruturados (`api.yaml`)
- **Tipagem** (type hints Python / TypeScript)
- **Manifestos** (`manifest.yaml`)

A documentação gerada automaticamente **complementa**, mas nunca substitui, a documentação escrita manualmente. O ponto de integração é `DocIndex.add()` — uma futura geração automática chamaria esse método da mesma forma que o `DocIndexer` faz hoje a partir de arquivos `.md`.
