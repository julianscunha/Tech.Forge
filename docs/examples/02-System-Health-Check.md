---
title: TechForge — Exemplo 02
category: fases
domain: [fases, exemplos-faq]
---

# TechForge — Exemplo 02
## System Health Check

> Segundo módulo de referência externo do TechForge.
>
> **Objetivo:** validar uma Application Module independente que consome um Service Module externo através de dependência e contrato público.

## 1. Identidade

Repository sugerido:

```text
techforge-system-health-check
```

Classificação:

```text
Type: Application
Mode: Passive
```

## 2. Dependência

Este módulo depende de:

```text
System Information Service
```

Regra:

```text
Application
        ↓
depends on
        ↓
Service
```

Nunca importar diretamente código interno do outro repositório.

A comunicação deve utilizar exclusivamente o contrato público do Service Module.

## 3. Objetivo funcional

Ao abrir o módulo:

```text
User
↓
Run Health Check
↓
Call System Information Service
↓
Collect information
↓
Apply simple health rules
↓
Display result
```

## 4. Health checks iniciais

Implementar regras simples:

```text
Memory available
CPU availability
Operating system detected
Runtime detected
Service communication
```

Exemplo:

```text
System Health Check

System
✓ Healthy

CPU
✓ Information available

Memory
✓ 62% available

Runtime
✓ Compatible
```

Não transformar o módulo em um monitor corporativo complexo.

O objetivo é validar a plataforma.

## 5. Manifest

Adaptar ao padrão oficial:

```yaml
module:
  id: com.techforge.examples.system-health-check
  name: System Health Check
  version: 1.0.0

classification:
  type: application
  mode: passive

platform:
  min_version: "1.0.0"

dependencies:
  modules:
    - id: com.techforge.examples.system-information-service
      version: ">=1.0.0,<2.0.0"
      required: true

capabilities:
  provides:
    - system-health-check
  consumes:
    - system-information
```

## 6. Interface

O módulo deve abrir dentro do TechForge.

Não:

```text
New browser tab
External application window
Separate localhost UI
```

A interface deve usar o shell e o espaço de conteúdo disponibilizados pela plataforma.

Layout sugerido:

```text
System Health Check

[ Run Health Check ]

────────────────────────

System      ✓ Healthy
CPU         ✓ Available
Memory      ✓ Healthy
Runtime     ✓ Compatible

Last Check: timestamp
```

## 7. Dependency behavior

Testar cenários:

### Service ausente

```text
System Information Service is required.

[ Install Dependency ]
```

### Service incompatível

```text
Required:
>= 1.0.0 < 2.0.0

Installed:
2.0.0

Status:
Incompatible
```

### Service disponível

```text
Open module
↓
Resolve dependency
↓
Call public contract
↓
Execute
```

## 8. Estrutura sugerida

```text
techforge-system-health-check/
├── manifest.yaml
├── README.md
├── src/
├── frontend/
├── docs/
│   ├── overview.md
│   └── examples/
│       └── basic.md
├── tests/
└── packaging/
```

## 9. Testes

Validar:

```text
Manifest
Application registration
Dependency declaration
Dependency resolution
Service contract consumption
UI rendering
Health check execution
Missing dependency handling
Incompatible dependency handling
Package installation
```

## 10. External installation scenario

Fluxo obrigatório:

```text
TechForge clean install

↓ Add external URL

System Information Service

↓ Inspect

↓ Install

↓ Add external URL

System Health Check

↓ Dependency recognized

↓ Install

↓ Open

↓ Run Health Check
```

## 11. Update scenario

Publicar:

```text
Service v1.0.0
Application v1.0.0
```

Depois:

```text
Service v1.1.0
```

Validar:

```text
Update discovery
Compatibility remains valid
Application continues working
```

## 12. Critérios de conclusão

O exemplo estará concluído quando:

1. Existir em repositório independente.
2. Não exigir alteração no Core.
3. Declarar Application + Passive.
4. Declarar dependência explícita.
5. Consumir apenas contrato público.
6. Abrir dentro do TechForge.
7. Resolver dependência corretamente.
8. Tratar dependência ausente.
9. Tratar incompatibilidade.
10. Passar documentação e validação.
11. Ser instalável por URL.
12. Funcionar após instalação limpa.
13. Continuar funcionando após atualização compatível do Service.

## Resultado esperado

Os dois exemplos devem provar:

```text
Independent Repository A
Service / Passive
        ↓ public contract
Independent Repository B
Application / Passive
        ↓
TechForge Core
```

Sem código compartilhado entre os módulos além dos contratos públicos e SDK da plataforma.
