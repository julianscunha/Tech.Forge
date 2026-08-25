# TechForge — Fase 6
## Launcher & Runtime

> **Status:** Prompt de implementação consolidado
>
> **Objetivo:** Criar uma experiência de execução simples para usuários corporativos, eliminando a necessidade de iniciar manualmente Backend e Frontend em dois terminais, mantendo a arquitetura interna desacoplada e preparada para evolução.

---

# 1. Contexto

O TechForge possui dois componentes principais:

- Backend Python/FastAPI;
- Frontend React/TypeScript.

Durante o desenvolvimento, é normal que cada componente possua seu próprio processo.

Isso oferece vantagens técnicas:

- desenvolvimento independente;
- Hot Reload separado;
- isolamento de falhas;
- build e deploy independentes;
- possibilidade futura de escalar componentes separadamente.

Entretanto, para o usuário final corporativo, abrir dois PowerShells e executar comandos manualmente não é aceitável.

O usuário deve conseguir iniciar o TechForge de forma simples.

Objetivo de experiência:

```text
Double Click
    ↓
TechForge starts
    ↓
Services become ready
    ↓
Browser/UI opens
```

---

# 2. Decisão arquitetural

Não unir artificialmente Frontend e Backend durante o desenvolvimento.

Eles continuam sendo componentes separados.

O que será criado é uma camada de inicialização/orquestração.

Modelo:

```text
                TechForge Launcher
                        │
          ┌─────────────┴─────────────┐
          │                           │
       Backend                    Frontend
      FastAPI                     React
          │                           │
          └─────────────┬─────────────┘
                        │
                     Runtime
                        │
                      User
```

O Launcher controla os processos.

Não duplicar lógica de inicialização dentro do Frontend.

---

# 3. Modos de execução

Implementar modos claros.

## Development

Utilizado por desenvolvedores.

Pode manter:

- Backend com reload;
- Frontend com dev server;
- logs detalhados.

## Desktop

Utilizado por usuários finais.

Preferir:

```text
Launcher
    ↓
Backend
    ↓
Static Frontend
    ↓
Browser/App
```

Evitar depender de um servidor de desenvolvimento React no ambiente final.

## Server

Preparar conceitualmente para futuro.

```text
Linux
↓
Backend
↓
Frontend static assets
↓
Multiple users
```

Não implementar multiusuário nesta fase.

---

# 4. Launcher

Criar um Launcher oficial do TechForge.

Ele deve:

1. localizar a instalação;
2. carregar configuração;
3. verificar pré-requisitos;
4. iniciar o Backend;
5. aguardar Health Check;
6. iniciar/servir o Frontend conforme o modo;
7. abrir a interface;
8. monitorar processos;
9. encerrar de forma organizada.

O Launcher deve ser a forma recomendada de iniciar a plataforma fora do desenvolvimento.

---

# 5. Ordem de inicialização

A ordem deve ser explícita.

```text
Launcher Start
    ↓
Load Configuration
    ↓
Validate Environment
    ↓
Start Backend
    ↓
Wait Health Check
    ↓
Backend Ready?
    ├── No → Fail with diagnostics
    └── Yes
          ↓
      Prepare Frontend
          ↓
      Start/Serve UI
          ↓
      Open TechForge
```

Não abrir a interface antes do Backend estar operacional.

---

# 6. Health-based readiness

Não utilizar apenas:

```text
sleep 5
```

para determinar se o Backend está pronto.

Utilizar Health Check real.

Exemplo:

```text
GET /api/health
```

O Launcher deve:

- aguardar resposta válida;
- possuir timeout configurável;
- registrar tentativas;
- falhar de forma clara se necessário.

---

# 7. Processo único para o usuário

O usuário não deve precisar saber que existem:

- FastAPI;
- Uvicorn;
- React;
- Node;
- Vite;
- dois serviços internos.

A experiência deve ser:

```text
Start TechForge
```

A implementação pode ser:

- script;
- executável;
- comando CLI;
- atalho.

Priorizar simplicidade e portabilidade inicialmente.

---

# 8. Evitar múltiplas instâncias

O Launcher deve detectar uma instância já ativa.

Fluxo:

```text
Start requested
    ↓
Existing instance?
    ├── Yes → focus/open existing UI
    └── No → start new instance
```

Não iniciar múltiplos Backends acidentalmente na mesma porta.

Implementar mecanismo simples e confiável, como:

- verificação de Health Check;
- lock file quando apropriado;
- PID controlado.

Não criar IPC complexo sem necessidade.

---

# 9. Port management

Centralizar portas.

O Launcher deve conhecer a configuração oficial.

Não permitir que:

- Backend use porta diferente sem registro;
- Frontend abra apontando para Backend errado.

Preparar possibilidade de:

- porta configurável;
- fallback controlado;
- conflito de porta diagnosticado.

---

# 10. Frontend em produção

Para modo Desktop e futuro Server:

- gerar build estático do React;
- servir os assets de forma controlada;
- evitar depender do Vite dev server.

A arquitetura pode escolher entre:

1. Backend servir os assets estáticos;
2. Launcher iniciar um servidor estático controlado;
3. outro mecanismo simples e documentado.

Preferir a solução com menor quantidade de processos e menor consumo de recursos, desde que preserve manutenção e futura implantação em servidor.

Documentar a decisão.

---

# 11. Shutdown ordenado

O encerramento deve seguir fluxo controlado.

```text
User closes TechForge
    ↓
Stop accepting new work
    ↓
Shutdown modules/runtime when applicable
    ↓
Stop services
    ↓
Cleanup
    ↓
Exit
```

Não matar processos indiscriminadamente pelo nome.

O Launcher deve controlar apenas processos que iniciou.

---

# 12. Logging do Launcher

Criar logs específicos.

Registrar:

- início;
- configuração;
- PID;
- Backend start;
- Health Check;
- Frontend/UI start;
- falhas;
- shutdown.

Os logs devem permitir diagnóstico sem poluir a interface do usuário.

---

# 13. Falhas de inicialização

Tratar cenários como:

- porta ocupada;
- Backend não inicia;
- banco indisponível;
- Health Check não responde;
- assets do Frontend ausentes;
- configuração inválida;
- processo encerra inesperadamente.

Apresentar mensagem objetiva.

Exemplo:

```text
TechForge could not start.

Backend failed health check.
Port: 8000
Timeout: 30 seconds

See launcher logs for details.
```

Não exibir stack traces extensos para usuários finais por padrão.

---

# 14. Runtime status

Implementar uma visão mínima de Runtime.

O Core deverá poder informar:

- platform status;
- backend status;
- frontend/UI status quando aplicável;
- uptime;
- versão;
- módulos ativos futuramente.

Exemplo:

```text
RUNNING
DEGRADED
STARTING
STOPPING
STOPPED
FAILED
```

O Dashboard pode consumir essas informações.

---

# 15. Runtime supervision

O Launcher deve detectar falhas dos processos que iniciou.

Exemplo:

```text
Backend exited unexpectedly
    ↓
Runtime status = DEGRADED/FAILED
    ↓
Log event
    ↓
Notify user
```

Não implementar um supervisor complexo de alta disponibilidade.

Inicialmente, diagnosticar corretamente é mais importante que reiniciar automaticamente em loops.

---

# 16. CLI

Criar comandos oficiais.

Exemplos:

```bash
techforge start
techforge stop
techforge status
techforge logs
```

`techforge start` deve reutilizar o Launcher.

Não criar um fluxo de inicialização diferente entre CLI e aplicação.

---

# 17. Development workflow

Preservar uma experiência eficiente para desenvolvimento.

Exemplo:

```bash
techforge dev
```

Ou scripts equivalentes.

O modo desenvolvimento pode iniciar:

```text
Backend reload
+
Frontend dev server
```

Isso não deve afetar o modo Desktop.

Documentar claramente:

```text
Development Mode
vs
Desktop Runtime
```

---

# 18. Instalação Desktop

Preparar uma estrutura de distribuição simples.

Nesta fase, não é obrigatório criar um instalador MSI completo.

Mas o projeto deve permitir evolução para:

```text
TechForge Installer
    ↓
Application Files
    ↓
Configuration
    ↓
Modules Directory
    ↓
Launcher
    ↓
Shortcut
```

O usuário final não deve precisar instalar dependências de desenvolvimento para usar a aplicação final.

---

# 19. Diretórios de runtime

Definir diretórios previsíveis.

Exemplo conceitual:

```text
TechForge/
├── app/
├── config/
├── modules/
├── data/
├── logs/
└── runtime/
```

Separar:

- arquivos da aplicação;
- dados;
- configuração;
- logs;
- estado temporário.

Não armazenar arquivos temporários arbitrariamente no diretório do projeto.

---

# 20. Preparação para servidor Linux

A arquitetura do Launcher não deve bloquear futuro deployment em Linux.

Preparar abstração para modos:

```text
desktop
server
development
```

No futuro:

```text
System Service
↓
Backend
↓
Static Frontend
↓
Reverse Proxy optional
```

Não implementar Kubernetes, Docker obrigatório ou HA nesta fase.

---

# 21. Documentação

Criar documentação oficial:

```text
docs/operations/
├── runtime.md
├── launcher.md
├── desktop-mode.md
├── development-mode.md
├── server-mode.md
├── troubleshooting.md
└── shutdown.md
```

Documentar claramente:

- por que existem componentes separados;
- por que isso é tecnicamente útil;
- como o Launcher abstrai essa complexidade;
- como iniciar;
- como diagnosticar problemas;
- diferenças entre modos.

---

# 22. Testes

Criar testes para:

- ordem de inicialização;
- Health Check readiness;
- timeout;
- Backend já ativo;
- múltipla instância;
- porta ocupada;
- shutdown;
- falha inesperada;
- status do Runtime;
- CLI.

Criar teste integrado:

```text
Launcher
↓
Backend Start
↓
Health Check Ready
↓
UI Ready
↓
Runtime Running
↓
Shutdown
```

---

# 23. O que não implementar

Não implementar nesta fase:

- multiusuário;
- autenticação;
- Service Registry;
- Dependency Governance;
- assinatura digital;
- auto-update completo;
- Marketplace remoto;
- HA;
- Kubernetes;
- containers obrigatórios.

---

# 24. Critérios de aceitação

A fase estará concluída quando:

1. O usuário puder iniciar o TechForge por uma única ação.
2. Não for necessário abrir dois PowerShells.
3. O Backend iniciar antes da UI.
4. A prontidão for baseada em Health Check real.
5. O Frontend de produção não depender obrigatoriamente do dev server.
6. Múltiplas instâncias acidentais forem evitadas.
7. Falhas de inicialização forem diagnosticáveis.
8. Shutdown for ordenado.
9. Logs do Launcher existirem.
10. CLI utilizar o mesmo fluxo.
11. O modo desenvolvimento continuar funcional.
12. A arquitetura continuar preparada para Linux.
13. O Core permanecer leve.
14. Nenhuma funcionalidade anterior for quebrada.

---

# Regra final

Antes de finalizar:

- testar Development Mode;
- testar Desktop Mode;
- iniciar via Launcher;
- confirmar Health Check;
- confirmar abertura automática da UI;
- tentar iniciar segunda instância;
- testar porta ocupada;
- testar Backend com falha;
- testar timeout;
- testar shutdown;
- executar todos os testes;
- executar build do Frontend.

Apresentar:

```text
Launcher:
Startup Order:
Health Check:
Single Instance:
Runtime Status:
Frontend Production:
CLI:
Development Mode:
Shutdown:
Tests:
Build:
Known Issues:
```

Não avançar para Documentation Compliance Checker, Service Registry ou Dependency Governance nesta fase.
