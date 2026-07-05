---
title: Service Modules
order: 1
tags: [service-modules, api-yaml, contracts, exports]
---

# Service Modules

Service Modules são módulos que expõem funcionalidades para outros módulos consumirem. Eles publicam um **contrato de serviço** em `docs/contracts/api.yaml`.

## Identificação

Um módulo de serviço declara `module_type: service` no manifest:

```yaml
id: storage_service
name: Storage Service
module_type: service
category: Infrastructure
vendor: TechForge
```

## Contrato de serviço — api.yaml

O arquivo `docs/contracts/api.yaml` define a interface pública do serviço:

```yaml
service_id: storage_service
description: Serviço centralizado de armazenamento para módulos
version: 1.0.0
dependencies: []

exports:
  - name: upload_file
    description: Faz upload de um arquivo para o armazenamento centralizado
    parameters:
      - name: module_id
        type: str
        description: ID do módulo solicitante
        required: true
      - name: filename
        type: str
        description: Nome do arquivo no destino
        required: true
      - name: content
        type: bytes
        description: Conteúdo do arquivo
        required: true
    returns: "str — path do arquivo armazenado"
    examples:
      - "path = await upload_file('my_module', 'report.pdf', pdf_bytes)"

  - name: download_file
    description: Baixa um arquivo do armazenamento centralizado
    parameters:
      - name: path
        type: str
        description: Path retornado por upload_file
        required: true
    returns: "bytes — conteúdo do arquivo"
    examples:
      - "data = await download_file('/storage/my_module/report.pdf')"
```

## Como o Developer Center exibe um serviço

Ao acessar um Service Module no Developer Center, você verá:

- **Nome e versão** do serviço
- **Descrição** completa
- **Dependências** (outros serviços que este serviço usa)
- **Exports** — cada função com parâmetros, tipos e exemplos
- **Consumidores** — módulos que usam este serviço

## Como consumir um serviço

```python
# No backend do seu módulo
from techforge_sdk import create_sdk
sdk = create_sdk("my_module")

# Fase futura: sdk.services.get("storage_service").upload_file(...)
# Por ora: chamada direta via HTTP interno
```

## Exemplos estruturais

```
my_service_module/
├── manifest.yaml            ← module_type: service
├── backend/
│   └── main.py
├── frontend/
│   └── index.tsx
└── docs/
    ├── overview.md          ← descrição geral
    ├── contracts/
    │   └── api.yaml         ← contrato de serviço
    └── examples/
        ├── basic.md
        ├── advanced.md
        └── integration.md
```
