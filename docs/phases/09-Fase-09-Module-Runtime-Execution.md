# TechForge — Fase 9
## Module Runtime & Execution

> **Status:** Prompt de implementação consolidado
>
> **Objetivo:** Consolidar o Runtime responsável pelo ciclo de execução dos módulos ativos, garantindo que módulos sejam carregados, inicializados, executados, monitorados e encerrados dentro do TechForge, sem abrir novas abas ou processos desnecessários.

---

# 1. Contexto

As fases anteriores definiram:

- Core modular;
- Module System;
- Package Manager;
- Developer Center;
- Launcher;
- Service Registry;
- Dependency Governance.

Agora é necessário consolidar o Runtime de módulos.

O objetivo é responder claramente:

```text
Como um módulo instalado e ativo realmente executa dentro do TechForge?
```

A resposta deve ser:

```text
Module
  ↓
Runtime
  ↓
Lifecycle
  ↓
Execution
  ↓
Integrated TechForge UI
```

Não deve ser necessário abrir:

- nova aba do navegador;
- aplicação externa;
- terminal separado;
- processo manual para cada módulo.

---

# 2. Princípio central

O módulo é parte da plataforma enquanto estiver ativo.

A experiência deve ser:

```text
User clicks module
        ↓
TechForge resolves module
        ↓
Runtime verifies readiness
        ↓
Module executes
        ↓
Module UI opens inside TechForge
```

Para módulos com interface:

- abrir no workspace principal;
- ocupar a área disponível;
- menus do Core podem ser recolhidos;
- não abrir nova aba.

Para Service Modules:

- disponibilizar página técnica integrada;
- contratos e capacidades;
- status;
- documentação;
- não exigir uma UI complexa.

---

# 3. Responsabilidade do Module Runtime

Criar uma camada responsável por:

- resolver módulo;
- verificar estado;
- verificar dependências;
- carregar recursos;
- inicializar módulo;
- executar;
- manter contexto;
- controlar erros;
- encerrar;
- liberar recursos.

Modelo:

```text
Module Runtime
├── Module Resolver
├── Lifecycle Manager
├── Execution Context
├── Resource Manager
├── Error Boundary
├── Module Health
└── Shutdown Manager
```

Não transformar o Runtime em um segundo sistema operacional.

Manter o Core leve.

---

# 4. Module lifecycle

Definir estados claros.

Exemplo:

```text
DISCOVERED
VALIDATED
INSTALLED
DISABLED
BLOCKED
ACTIVATING
ACTIVE
INITIALIZING
READY
EXECUTING
DEGRADED
FAILED
STOPPING
STOPPED
REMOVED
```

Nem todos precisam ser persistidos permanentemente.

Separar:

```text
Administrative State
```

de:

```text
Runtime State
```

Exemplo:

```text
Administrative:
ACTIVE

Runtime:
READY
```

Evitar estados ambíguos.

---

# 5. Lifecycle transitions

Definir transições permitidas.

Exemplo:

```text
DISABLED
    ↓ activate
ACTIVATING
    ↓ dependencies OK
ACTIVE
    ↓ initialize
INITIALIZING
    ↓ success
READY
    ↓ user action
EXECUTING
    ↓ complete
READY
```

Falhas:

```text
INITIALIZING
    ↓ error
FAILED
```

Ou:

```text
READY
    ↓ runtime degradation
DEGRADED
```

As transições devem ser centralizadas.

O Frontend não deve alterar estado diretamente.

---

# 6. Runtime startup

No startup do TechForge:

```text
Launcher
    ↓
Core Ready
    ↓
Discover Modules
    ↓
Validate
    ↓
Dependency Governance
    ↓
Service Registry
    ↓
Activate eligible modules
    ↓
Runtime Ready
```

Nem todo Application Module precisa carregar todos os recursos imediatamente.

Utilizar inicialização sob demanda quando apropriado.

---

# 7. Lazy loading

Priorizar um Core leve.

Para Application Modules:

```text
Platform starts
    ↓
Module metadata available
    ↓
User opens module
    ↓
Module resources loaded
```

Não carregar todos os módulos pesados durante startup.

Para Service Modules, inicializar conforme:

- necessidade;
- dependências;
- declaração de startup;
- capability requerida.

---

# 8. Execution context

Criar um contexto de execução oficial.

Exemplo conceitual:

```text
ModuleExecutionContext
├── module_id
├── module_version
├── runtime_id
├── configuration
├── services
├── logger
├── paths
├── cancellation
└── metadata
```

O contexto deve ser a forma oficial de um módulo acessar recursos permitidos.

Evitar que módulos dependam diretamente de estruturas internas do Core.

---

# 9. Module API / Runtime SDK

Definir uma API mínima para módulos interagirem com o Runtime.

Exemplo conceitual:

```text
context.services
context.logger
context.config
context.paths
context.runtime
```

O SDK deve ser:

- pequeno;
- estável;
- documentado;
- versionado.

Não expor todo o Core ao módulo.

---

# 10. Backend execution

Para módulos Python/backend:

- carregar de forma controlada;
- localizar entrypoint oficial;
- fornecer Execution Context;
- capturar exceções;
- registrar logs;
- retornar resultado estruturado.

Definir convenção de entrypoint.

Exemplo conceitual:

```text
backend/
└── main.py
```

com uma interface declarada pelo módulo.

Não executar arquivos arbitrários apenas por existirem na pasta.

---

# 11. Frontend integration

Para módulos React/TypeScript:

- registrar entrypoint;
- carregar componente sob demanda;
- renderizar no workspace principal;
- fornecer contexto controlado;
- aplicar Error Boundary.

Fluxo:

```text
Module Selected
      ↓
Module Registry
      ↓
Resolve Frontend Entry
      ↓
Lazy Load
      ↓
Render inside Workspace
```

O módulo deve parecer parte nativa do TechForge.

---

# 12. Workspace

Consolidar uma área principal de trabalho.

Exemplo:

```text
┌───────────────────────────────────────────────┐
│ Top Bar                                      │
├──────┬────────────────────────────────────────┤
│ Menu │                                        │
│      │            MODULE WORKSPACE            │
│      │                                        │
└──────┴────────────────────────────────────────┘
```

Quando necessário:

```text
Focus Mode
```

permite recolher menus e maximizar o espaço.

A mudança deve ocorrer sem abrir nova aba.

---

# 13. Module navigation

A navegação deve ser derivada do estado real.

Somente módulos:

```text
INSTALLED
+
ACTIVE
+
READY/AVAILABLE
```

devem aparecer como utilizáveis.

Módulos:

- desativados;
- bloqueados;
- removidos;

não podem continuar como itens funcionais do menu.

A Runtime deve fornecer estado consistente ao Navigation Registry.

---

# 14. Runtime isolation

Não implementar containers ou VMs obrigatoriamente.

Inicialmente, isolamento significa:

- interfaces públicas;
- Execution Context;
- Error Boundary;
- lifecycle controlado;
- logs separados;
- não compartilhar estado global desnecessariamente.

O objetivo é reduzir acoplamento e impedir que uma falha simples quebre toda a UI.

---

# 15. Error boundaries

Para Frontend:

```text
Module UI Error
    ↓
Catch
    ↓
Show module error screen
    ↓
Core remains operational
```

Para Backend:

```text
Module execution error
    ↓
Catch
    ↓
Structured error
    ↓
Log
    ↓
Runtime status updated
```

Não permitir que uma falha isolada derrube todo o TechForge sem necessidade.

---

# 16. Cancellation

Operações longas devem poder ser canceladas quando aplicável.

O Execution Context pode fornecer:

```text
CancellationToken
```

ou mecanismo equivalente.

Fluxo:

```text
User cancels
    ↓
Runtime signals cancellation
    ↓
Module cleans up
    ↓
Runtime returns to READY
```

Não matar processos de forma indiscriminada.

---

# 17. Resource management

O Runtime deve controlar recursos básicos:

- tarefas;
- handles;
- conexões quando registradas;
- processos filhos explicitamente criados;
- recursos temporários.

Ao encerrar:

```text
Execution
    ↓
Cleanup
    ↓
Release
```

Não criar um gerenciador pesado de recursos se o módulo não precisar.

---

# 18. Module health

Definir um mecanismo leve.

Exemplo:

```text
READY
DEGRADED
FAILED
```

O Health deve considerar:

- inicialização;
- dependências;
- último erro relevante;
- disponibilidade de serviços necessários.

Não fazer polling agressivo em todos os módulos.

---

# 19. Execution results

Padronizar resultados.

Exemplo:

```text
ModuleExecutionResult
├── status
├── data
├── warnings
├── errors
├── duration
└── metadata
```

Não obrigar todos os módulos a retornar exatamente o mesmo payload de negócio.

Padronizar apenas o envelope de execução.

---

# 20. Long-running operations

Preparar suporte para tarefas que demoram.

Exemplos:

- Health Check VMware;
- coleta AWS;
- cálculos extensos;
- relatórios.

Fluxo:

```text
Module Request
    ↓
Runtime Task
    ↓
RUNNING
    ↓
Progress
    ↓
COMPLETE / FAILED / CANCELLED
```

Nesta fase, criar uma abstração simples.

Não implementar uma plataforma distribuída de jobs.

---

# 21. Progress reporting

Permitir que módulos reportem:

```text
0%
25%
50%
75%
100%
```

Ou estados:

```text
PREPARING
RUNNING
FINALIZING
```

A UI deve poder mostrar progresso sem o módulo precisar manipular diretamente o Core.

---

# 22. Logging

Cada módulo deve possuir contexto de log.

Exemplo:

```text
[module:aws_sizing]
[runtime:abc123]
```

Integrar ao logging existente.

Não criar arquivos de log aleatórios por módulo sem controle central.

---

# 23. Runtime observability

Disponibilizar informações básicas:

- módulo;
- estado;
- uptime;
- última execução;
- duração;
- último erro;
- dependências.

O Dashboard pode mostrar apenas informações resumidas.

Detalhes podem estar na página do módulo.

---

# 24. Service Modules no Runtime

Service Modules devem:

```text
register
initialize when required
provide capabilities
shutdown cleanly
```

A invocação continua integrada ao Service Registry.

O Module Runtime não deve substituir o Service Registry.

Responsabilidades:

```text
Runtime
→ lifecycle

Service Registry
→ discovery / contracts

Dependency Governance
→ dependencies
```

---

# 25. Application Modules no Runtime

Application Modules devem:

```text
load
initialize
render
invoke services
execute tasks
cleanup
```

A integração visual deve ocorrer dentro do workspace.

Não permitir que Application Modules assumam controle da navegação global arbitrariamente.

---

# 26. Runtime API

Criar APIs de observação e controle.

Exemplos:

```text
GET /api/v1/runtime/status
GET /api/v1/runtime/modules
GET /api/v1/runtime/modules/{id}
POST /api/v1/runtime/modules/{id}/initialize
POST /api/v1/runtime/modules/{id}/execute
POST /api/v1/runtime/modules/{id}/cancel
```

A exposição de execução deve respeitar o contrato do módulo.

Não criar endpoint genérico inseguro capaz de executar qualquer função privada.

---

# 27. CLI

Adicionar:

```bash
techforge runtime status
techforge runtime modules
techforge runtime module <module_id>
techforge runtime initialize <module_id>
```

Comandos de execução específicos podem depender do módulo.

A CLI deve usar o Runtime oficial.

---

# 28. Developer Center

Documentar:

- Runtime Lifecycle;
- Module SDK;
- Execution Context;
- entrypoints;
- frontend integration;
- backend execution;
- cancellation;
- progress;
- errors;
- logging.

Adicionar exemplos oficiais.

O `AIContextExporter` deve incluir:

```text
Module Runtime Context
```

---

# 29. Persistência de estado

Não persistir todo estado transitório.

Exemplos que podem ser transitórios:

```text
EXECUTING
INITIALIZING
PROGRESS 62%
```

Ao reiniciar:

- reconstruir estado a partir dos módulos;
- registrar encerramento inesperado quando aplicável.

Persistir somente informações úteis:

- último erro relevante;
- última execução;
- configuração;
- estado administrativo.

---

# 30. Atualização de módulos

Durante update:

```text
Module Active
    ↓
Stop new execution
    ↓
Wait/cancel active tasks
    ↓
Shutdown
    ↓
Update Package
    ↓
Validate
    ↓
Dependency Check
    ↓
Initialize new version
```

Não atualizar código de módulo em execução sem governança.

---

# 31. Testes

Criar testes para:

- lifecycle transitions;
- lazy loading;
- Application Module initialization;
- Service Module initialization;
- Execution Context;
- SDK access;
- backend entrypoint;
- frontend entrypoint;
- module error;
- error boundary;
- cancellation;
- progress;
- long-running task;
- health;
- logging context;
- cleanup;
- shutdown;
- removed module;
- disabled module;
- blocked module;
- Service Registry integration;
- Dependency Governance integration;
- API;
- CLI.

Teste integrado:

```text
Start TechForge
    ↓
Runtime Ready
    ↓
Select Module
    ↓
Lazy Load
    ↓
Initialize
    ↓
READY
    ↓
Execute
    ↓
Progress
    ↓
Complete
    ↓
Return to READY
    ↓
Close/Shutdown
```

Também testar:

```text
Module fails
    ↓
Module error captured
    ↓
Core remains running
```

---

# 32. O que não implementar

Não implementar nesta fase:

- containers obrigatórios por módulo;
- sandbox de segurança completo;
- execução distribuída;
- fila corporativa;
- multiusuário;
- autenticação;
- Marketplace remoto.

A próxima fase poderá aprofundar segurança, integridade ou distribuição conforme o roadmap.

---

# 33. Critérios de aceitação

A fase estará concluída quando:

1. Módulos ativos possuírem lifecycle controlado.
2. Runtime e estado administrativo forem separados.
3. Application Modules carregarem sob demanda.
4. Service Modules integrarem com Runtime e Registry.
5. Execution Context oficial existir.
6. Module SDK básico estiver definido.
7. Backend entrypoints forem controlados.
8. Frontend Modules abrirem dentro do TechForge.
9. Nenhuma nova aba for necessária.
10. Focus Mode ampliar o workspace.
11. Módulos inválidos/desativados/bloqueados não forem executados.
12. Erros de módulos não derrubarem desnecessariamente o Core.
13. Cancellation funcionar quando aplicável.
14. Progresso puder ser reportado.
15. Resultados tiverem envelope padronizado.
16. Logs possuírem contexto.
17. Shutdown fizer cleanup.
18. APIs funcionarem.
19. CLI funcionar.
20. Developer Center documentar o Runtime.
21. AI Context incluir Module Runtime.
22. Todos os testes passarem.
23. O Core continuar leve.

---

# Regra final

Antes de finalizar:

- iniciar o TechForge pelo Launcher;
- verificar Runtime Ready;
- abrir Application Module;
- confirmar carregamento interno;
- confirmar que não abriu nova aba;
- testar Focus Mode;
- executar operação simples;
- testar operação longa;
- testar progresso;
- testar cancelamento;
- provocar erro controlado;
- confirmar que o Core continua funcionando;
- testar Service Module;
- testar shutdown;
- executar todos os testes;
- executar build do Frontend.

Apresentar:

```text
Module Runtime:
Lifecycle:
Lazy Loading:
Execution Context:
Module SDK:
Backend Execution:
Frontend Integration:
Workspace:
Focus Mode:
Error Boundaries:
Cancellation:
Progress:
Health:
Logging:
Service Integration:
Dependency Integration:
API:
CLI:
Developer Center:
AI Context:
Tests:
Build:
Known Issues:
```
