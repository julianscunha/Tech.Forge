# TechForge — Exemplo 01
## System Information Service

> Primeiro módulo de referência externo do TechForge.
>
> **Objetivo:** validar a criação de um Service Module independente, distribuído por repositório próprio e consumível por outros módulos.

## 1. Identidade

Repository sugerido:

```text
techforge-system-information-service
```

Classificação:

```text
Type: Service
Mode: Passive
```

O módulo não possui UI obrigatória para usuários finais. Sua função principal é fornecer informações reutilizáveis da máquina onde o TechForge está executando.

## 2. Funcionalidades

Fornecer inicialmente:

```text
get_system_info()
get_cpu_info()
get_memory_info()
get_runtime_info()
```

Informações mínimas:

```text
Operating System
OS Version
Hostname
Architecture
CPU logical cores
Total memory
Available memory
Runtime / platform information
```

## 3. Contrato público

Exemplo conceitual:

```yaml
exports:
  - name: get_system_info
    description: Returns general system information.
    parameters: []
    returns:
      type: SystemInfo

  - name: get_memory_info
    description: Returns memory information.
    parameters: []
    returns:
      type: MemoryInfo
```

Os tipos retornados devem ser documentados explicitamente.

## 4. Manifest

Adaptar à especificação oficial existente:

```yaml
module:
  id: com.techforge.examples.system-information-service
  name: System Information Service
  version: 1.0.0

classification:
  type: service
  mode: passive

platform:
  min_version: "1.0.0"

dependencies:
  modules: []

capabilities:
  provides:
    - system-information
    - memory-information
    - runtime-information
  consumes: []
```

## 5. Regra de independência

O módulo deve funcionar sem depender de:

```text
System Health Check
Qualquer Application Module
Código interno privado do TechForge
```

Ele pode depender apenas de APIs públicas da plataforma e de dependências externas permitidas.

## 6. Estrutura sugerida

```text
techforge-system-information-service/
├── manifest.yaml
├── README.md
├── src/
├── docs/
│   ├── overview.md
│   └── examples/
│       ├── basic.md
│       ├── advanced.md
│       └── integration.md
├── tests/
└── packaging/
```

Usar a estrutura oficial gerada pelo SDK/CLI quando disponível.

## 7. Documentação obrigatória

Por ser um Service Module:

```text
overview.md
api.yaml / contract
basic.md
advanced.md
integration.md
```

O exemplo de integração deve demonstrar como outro módulo chama o serviço.

## 8. Testes

Validar:

```text
Module loads
Manifest validates
Contract validates
get_system_info works
get_memory_info works
Documentation matches behavior
Package validates
```

## 9. Release

Fluxo:

```text
Implement
↓
Test
↓
Validate
↓
Package .tforge
↓
Create GitHub Release
```

O repositório deve permitir que o TechForge descubra uma release estável.

## 10. Critérios de conclusão

O exemplo estará concluído quando:

1. For criado em repositório independente.
2. Não exigir alteração no Core.
3. Declarar Service + Passive.
4. Possuir contrato público.
5. Passar no Documentation Compliance Checker.
6. Passar na validação de módulo.
7. Gerar pacote válido.
8. Puder ser adicionado ao TechForge por URL.
9. Puder ser instalado.
10. Puder ser chamado por outro módulo.
