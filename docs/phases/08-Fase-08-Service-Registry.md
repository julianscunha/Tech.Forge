---
title: TechForge — Fase 8
category: fases
domain: [fases]
---

# TechForge — Fase 8
## Service Registry

> **Status:** Prompt de implementação consolidado
>
> **Objetivo:** Implementar o registro e a descoberta oficial de capacidades fornecidas por Service Modules, permitindo que Application Modules consumam serviços por contratos públicos, sem acoplamento direto à implementação interna.

---

# 1. Contexto

O TechForge possui dois tipos principais de módulos:

```text
Application Module
Service Module
```

A regra conceitual é:

```text
Service Module
    ↓ fornece capacidades
Application Module
    ↓ consome capacidades
```

Exemplo:

```text
AWS Cost Service
    ↓
fornece custos e dados da AWS
    ↓
AWS Sizing Application
    ↓
consome os dados para executar cálculos
```

O objetivo não é que um módulo conheça internamente a estrutura de arquivos do outro.

A integração deve ocorrer por meio de capacidades e contratos públicos.

---

# 2. Objetivo do Service Registry

Criar um mecanismo central para:

- descobrir Service Modules ativos;
- registrar serviços;
- registrar capacidades públicas;
- expor contratos;
- localizar serviços;
- permitir consumo controlado;
- manter metadados de versão e compatibilidade.

O Registry não deve executar lógica de negócio.

Ele deve responder:

```text
Qual serviço fornece esta capacidade?
```

e:

```text
Como esse serviço pode ser consumido?
```

---

# 3. Arquitetura

Modelo:

```text
Service Module
      │
      │ declares
      ▼
Service Contract
      │
      │ registered
      ▼
Service Registry
      │
      │ discover / resolve
      ▼
Application Module
```

A dependência deve ser lógica e contratual.

Evitar:

```text
Application
    ↓
import service/internal/file.py
```

Preferir:

```text
Application
    ↓
Service Registry
    ↓
Public Contract
    ↓
Service Capability
```

---

# 4. Regra de dependência

A regra arquitetural deve ser formalizada:

```text
Service Module
    X
    depende de Application Module
```

e:

```text
Application Module
    ✓
    pode consumir Service Module
```

A validação completa do grafo será aprofundada na Fase 8.1.

Nesta fase, garantir que o Registry não incentive relações inválidas.

---

# 5. Declaração de serviço

Todo Service Module deve declarar claramente:

- module id;
- service id;
- versão;
- capacidades;
- exports;
- contrato;
- compatibilidade.

Exemplo conceitual:

```yaml
module:
  id: aws_cost_service
  type: service

service:
  id: aws.costs
  version: 1.0.0
```

O formato deve se integrar ao manifest e ao contrato já existentes.

Não criar dois sistemas concorrentes de metadados.

---

# 6. Capacidades

Uma capacidade representa algo que o serviço fornece.

Exemplos:

```text
aws.cost.read
aws.cost.summary
aws.inventory.read
veeam.m365.calculate
vmware.health.collect
```

A nomenclatura deve ser:

- estável;
- legível;
- hierárquica;
- documentável.

O Registry deve permitir descobrir capacidades sem conhecer previamente o módulo.

---

# 7. Registro

O ciclo deve ser:

```text
Module Installed
      ↓
Module Validated
      ↓
Module Activated
      ↓
Service Contract Loaded
      ↓
Service Registered
      ↓
Capabilities Available
```

Ao desativar:

```text
Service Module Deactivated
      ↓
Capabilities Unavailable
      ↓
Registry Updated
```

Ao remover:

```text
Service Module Removed
      ↓
Registry Entry Removed
      ↓
Capabilities Removed
```

Não manter serviços removidos ou desativados como disponíveis.

---

# 8. Estado do serviço

Definir estados claros.

Exemplo:

```text
REGISTERED
ACTIVE
UNAVAILABLE
DISABLED
FAILED
REMOVED
```

Separar:

```text
Module State
```

de:

```text
Service Availability
```

Um módulo pode estar ativo, mas um serviço específico pode estar indisponível devido a falha de inicialização.

---

# 9. Service discovery

Criar APIs internas para localizar serviços.

Exemplos conceituais:

```text
find_service(service_id)
find_capability(capability)
list_services()
list_capabilities()
```

A implementação deve retornar:

- identificador;
- módulo fornecedor;
- versão;
- contrato;
- estado;
- disponibilidade.

Não retornar referências à implementação privada.

---

# 10. Service contract

O contrato público deve ser a fonte oficial para consumidores.

Cada export deve fornecer:

- name;
- description;
- parameters;
- tipos;
- required;
- returns;
- exemplos.

Exemplo:

```yaml
exports:
  - name: get_cost_summary
    description: Returns AWS cost summary.
    parameters:
      - name: account_id
        type: string
        required: true
      - name: period
        type: string
        required: true
    returns:
      type: CostSummary
```

O Service Registry deve utilizar o contrato já validado pela Fase 7.

Não duplicar o `APIYamlParser`.

---

# 11. Service descriptor

Criar um modelo interno de descriptor.

Exemplo conceitual:

```text
ServiceDescriptor
├── service_id
├── module_id
├── module_version
├── service_version
├── capabilities
├── contract
├── status
└── metadata
```

O modelo deve ser serializável e independente da implementação do serviço.

---

# 12. Service Provider interface

Definir uma interface ou convenção mínima para Service Modules.

O Core deve conseguir:

- registrar;
- inicializar quando necessário;
- verificar disponibilidade;
- invocar capacidades públicas;
- desligar quando aplicável.

Exemplo conceitual:

```text
ServiceProvider
    register()
    initialize()
    health()
    invoke()
    shutdown()
```

Não obrigar todos os serviços a implementar processos complexos se forem simples.

A interface deve ser proporcional ao Core leve.

---

# 13. Invocação

A invocação deve passar por uma camada oficial.

Fluxo:

```text
Application Module
        ↓
Service Registry
        ↓
Resolve Service
        ↓
Validate Contract
        ↓
Invoke Public Capability
        ↓
Return Result
```

Não permitir que Application Modules dependam diretamente de classes privadas do Service Module.

---

# 14. Validação de argumentos

Antes da invocação, quando aplicável:

- verificar argumentos obrigatórios;
- validar tipos básicos;
- detectar parâmetros desconhecidos quando a regra exigir.

A validação deve reutilizar informações do contrato.

Não criar um sistema de schemas paralelo sem necessidade.

---

# 15. Erros

Definir erros previsíveis.

Exemplos:

```text
SERVICE_NOT_FOUND
CAPABILITY_NOT_FOUND
SERVICE_DISABLED
SERVICE_UNAVAILABLE
CONTRACT_VIOLATION
INVALID_ARGUMENTS
SERVICE_EXECUTION_FAILED
```

Os consumidores devem receber erros claros.

Não expor internamente stack traces de outros módulos como contrato público.

---

# 16. Versionamento

O Registry deve registrar versões.

Exemplo:

```text
Service:
aws.costs

Module Version:
1.2.0

Service Version:
1.0.0
```

Preparar resolução futura baseada em:

- versão;
- compatibilidade;
- ranges semânticos.

Não implementar ainda um resolvedor complexo de múltiplas versões simultâneas.

---

# 17. Conflitos

Tratar cenários:

```text
Dois módulos fornecem a mesma capability
```

Não escolher silenciosamente.

Nesta fase, detectar e reportar conflito.

Exemplo:

```text
CAPABILITY_CONFLICT
aws.cost.read
provided by:
- aws_cost_service
- alternative_aws_service
```

A política de resolução poderá ser expandida futuramente.

---

# 18. Health de serviços

Cada Service Module pode declarar uma verificação de disponibilidade.

O Registry deve permitir:

```text
Service
↓
Available / Unavailable
```

Não exigir polling contínuo para todos os serviços.

Verificações devem ser leves e acionadas de forma controlada.

---

# 19. Integração com Dashboard

O Dashboard simples pode mostrar:

- número de Service Modules ativos;
- serviços disponíveis;
- serviços indisponíveis;
- erros relevantes.

Não transformar o Dashboard em um monitoramento corporativo completo.

---

# 20. Interface de módulos de serviço

Quando o usuário abrir um Service Module, ele deve poder visualizar sua interface pública.

Exibir:

```text
Service Information
Capabilities
Exports
Arguments
Return Types
Examples
Dependencies
Status
```

Isso é importante porque desenvolvedores precisam entender como consumir o serviço.

O módulo de serviço não precisa possuir uma interface complexa.

Pode abrir uma página técnica integrada ao TechForge.

---

# 21. Developer Center integration

O Developer Center deve conseguir navegar para:

```text
Service
↓
Contract
↓
Capabilities
↓
Examples
```

A interface pública de um serviço deve ser consistente entre:

- módulo;
- Developer Center;
- Service Registry;
- AI Context.

Evitar documentação divergente.

---

# 22. AI Context

O `AIContextExporter` deve poder exportar:

```text
Installed Service Registry Context
```

Incluindo:

- serviços ativos;
- capabilities;
- contratos;
- versões;
- exemplos.

Isso permitirá que uma IA desenvolvendo um Application Module saiba quais serviços pode consumir.

---

# 23. APIs

Criar APIs administrativas/consultivas.

Exemplos:

```text
GET /api/v1/services
GET /api/v1/services/{service_id}
GET /api/v1/services/{service_id}/contract
GET /api/v1/services/capabilities
GET /api/v1/services/capabilities/{capability}
```

As rotas devem ser somente de consulta nesta fase, salvo necessidade arquitetural justificada.

Não permitir execução arbitrária de serviços por uma API genérica pública.

---

# 24. CLI

Adicionar comandos:

```bash
techforge services list
techforge services show <service_id>
techforge services capabilities
techforge services contract <service_id>
techforge services status
```

A CLI deve reutilizar o Service Registry.

---

# 25. Persistência

O Registry pode ser reconstruído a partir dos módulos ativos durante a inicialização.

Preferir:

```text
Installed Modules
    ↓
Discover Active Services
    ↓
Load Contracts
    ↓
Build Registry
```

Não tornar o banco de dados a única fonte da verdade para serviços.

O estado derivado deve poder ser reconstruído.

Persistir apenas quando houver benefício claro.

---

# 26. Inicialização

Durante o startup:

```text
Core Start
    ↓
Discover Modules
    ↓
Validate
    ↓
Activate Active Modules
    ↓
Discover Service Modules
    ↓
Register Services
    ↓
Service Registry Ready
```

Falha de um Service Module não deve necessariamente derrubar todo o Core.

Registrar:

```text
FAILED / UNAVAILABLE
```

e continuar quando seguro.

---

# 27. Shutdown

No encerramento:

```text
Stop accepting new service invocations
        ↓
Shutdown services when applicable
        ↓
Clear transient registry state
        ↓
Runtime shutdown
```

Não apagar configurações ou metadados de instalação.

---

# 28. Testes

Criar testes para:

- descoberta de Service Module;
- registro;
- capability discovery;
- contrato;
- ativação;
- desativação;
- remoção;
- invocação;
- argumentos inválidos;
- serviço indisponível;
- conflito de capability;
- versões;
- reconstrução do Registry;
- falha de um serviço;
- múltiplos serviços;
- API;
- CLI.

Teste integrado:

```text
Install Service Module
        ↓
Activate
        ↓
Registry discovers service
        ↓
Capability available
        ↓
Application resolves capability
        ↓
Invoke
        ↓
Result
        ↓
Deactivate
        ↓
Capability unavailable
```

---

# 29. O que não implementar

Não implementar nesta fase:

- Dependency Governance completo;
- resolvedor automático de grafo;
- múltiplas versões simultâneas;
- marketplace remoto;
- assinatura digital;
- multiusuário;
- autenticação;
- workflow engine complexo.

A governança de dependências será tratada na Fase 8.1.

---

# 30. Critérios de aceitação

A fase estará concluída quando:

1. Service Modules puderem ser descobertos.
2. Serviços ativos forem registrados automaticamente.
3. Capacidades forem descobertas.
4. Contratos públicos forem expostos.
5. Application Modules puderem localizar serviços oficialmente.
6. Não houver dependência de imports privados.
7. Desativação remover capacidades do Registry.
8. Remoção física remover registros.
9. Conflitos forem detectados.
10. Erros forem previsíveis.
11. Versões forem registradas.
12. A interface de Service Modules mostrar contratos e exemplos.
13. Developer Center integrar contratos.
14. AI Context puder exportar serviços instalados.
15. APIs e CLI funcionarem.
16. Falha de um serviço não derrubar desnecessariamente o Core.
17. Todos os testes passarem.

---

# Regra final

Antes de finalizar:

- criar ou utilizar um Service Module real de teste;
- ativar;
- verificar registro;
- listar capabilities;
- consultar contrato;
- consumir a capability por outro módulo de teste;
- testar argumentos inválidos;
- desativar;
- confirmar indisponibilidade;
- reativar;
- remover;
- confirmar limpeza do Registry;
- testar conflito;
- executar testes;
- executar build do Frontend.

Apresentar:

```text
Service Registry:
Service Discovery:
Capabilities:
Contracts:
Invocation:
Errors:
Lifecycle Integration:
Developer Center:
AI Context:
API:
CLI:
Tests:
Build:
Known Issues:
```

Não implementar ainda Dependency Governance completo. A próxima etapa é a Fase 8.1.
