---
title: TechForge — Fase 16
category: fases
domain: [fases]
---

# TechForge — Fase 16
## Desktop Distribution & User Experience

> **Status:** Prompt de implementação consolidado
>
> **Objetivo:** Transformar o TechForge em uma aplicação corporativa de fácil instalação e uso no Desktop, eliminando a necessidade de abrir múltiplos terminais ou conhecer comandos técnicos, sem comprometer a arquitetura modular e mantendo o caminho aberto para futura execução centralizada em servidor.

---

# 1. Contexto

Hoje o ambiente de desenvolvimento pode possuir:

```text
PowerShell
├── Backend
└── Frontend
```

Isso é aceitável para desenvolvimento.

Não é aceitável como experiência padrão para usuários corporativos.

O usuário final deve perceber:

```text
TechForge
```

como uma única aplicação.

Fluxo desejado:

```text
Click TechForge
      ↓
Core starts
      ↓
Required services start
      ↓
Health check
      ↓
Application opens
      ↓
User works
```

---

# 2. Princípio central

Separar:

```text
Development Experience
```

de:

```text
End User Experience
```

Desenvolvedores podem continuar usando serviços separados.

Usuários finais não devem precisar conhecer:

- Python;
- Node.js;
- npm;
- Uvicorn;
- PowerShell;
- portas;
- processos internos.

---

# 3. Distribution model

Definir dois modos.

## Development

```text
Frontend Dev Server
+
Backend Dev Server
```

## Desktop Distribution

```text
TechForge Launcher
+
Packaged Frontend
+
Backend Runtime
+
Local Data
```

Não obrigar o usuário final a instalar dependências de desenvolvimento.

---

# 4. Single launcher

Criar um componente oficial:

```text
TechForge Launcher
```

Responsabilidades:

```text
Start
↓
Validate Environment
↓
Initialize Data
↓
Start Backend
↓
Wait for Ready
↓
Serve/Open Frontend
↓
Monitor Runtime
↓
Graceful Shutdown
```

O Launcher é a experiência principal do usuário.

---

# 5. Startup sequence

Fluxo obrigatório:

```text
User starts TechForge
        ↓
Check existing instance
        ↓
Initialize paths
        ↓
Validate local environment
        ↓
Start backend
        ↓
Wait /ready
        ↓
Start frontend if required
        ↓
Open application
```

Não abrir a interface antes do backend estar pronto.

---

# 6. Single instance behavior

Por padrão:

```text
One TechForge instance per user session
```

Ao tentar abrir novamente:

```text
Existing instance found
        ↓
Focus existing application
```

Não iniciar múltiplos Backends acidentalmente.

---

# 7. Application window

Avaliar e implementar a opção mais leve entre:

```text
System Browser
```

e:

```text
Desktop WebView Shell
```

Critérios:

- facilidade de distribuição;
- consumo de memória;
- manutenção;
- integração com o sistema operacional;
- experiência corporativa.

Não escolher um framework pesado apenas para esconder o navegador.

A decisão deve ser documentada.

---

# 8. Recommended initial approach

Preferir inicialmente:

```text
Local application
+
Default browser / controlled application window
```

quando isso mantiver a distribuição significativamente mais leve.

Caso um WebView Shell seja escolhido, justificar tecnicamente:

- ganho de UX;
- impacto de memória;
- impacto de distribuição;
- manutenção.

---

# 9. Frontend production mode

No Desktop:

```text
React Build
```

não deve exigir:

```text
npm run dev
```

O Frontend deve ser empacotado como artefato de produção.

Configuração de API:

```text
runtime configurable
```

Não depender de `localhost:5173`.

---

# 10. Backend packaging

O Backend deve ser distribuído com os componentes necessários.

O usuário não deve precisar executar:

```bash
pip install
```

na instalação normal.

Definir estratégia compatível com Windows inicialmente.

Exemplos possíveis:

```text
Python bundled runtime
packaged executable
application installer
```

A implementação deve priorizar confiabilidade.

---

# 11. Installation

O processo deve ser simples:

```text
Download Installer
        ↓
Install
        ↓
Desktop/Start Menu Shortcut
        ↓
Open TechForge
```

O instalador deve criar ou preparar:

```text
Application Files
User Data
Logs
Modules
Exports
Cache
```

Separar arquivos da aplicação dos dados do usuário.

---

# 12. User data preservation

Atualizar ou reinstalar o TechForge não deve apagar automaticamente:

- módulos;
- configurações;
- dados;
- exports;
- histórico relevante.

Fluxo:

```text
Application Update
        ↓
Preserve User Data
        ↓
Run Required Migrations
        ↓
Start
```

---

# 13. Desktop paths

Definir paths oficiais por sistema operacional.

Exemplo conceitual:

```text
Application Install
User Data
Logs
Cache
Temp
Modules
Exports
```

Nunca depender de caminhos hardcoded.

A abstração da Fase 12 deve ser reutilizada.

---

# 14. First startup

No primeiro uso:

```text
Launcher
↓
Create Data Directories
↓
Initialize Database
↓
Run Core Migrations
↓
Discover Bundled Modules
↓
Validate
↓
Open Dashboard
```

Mostrar progresso apenas quando necessário.

Não transformar a primeira execução em um wizard longo.

---

# 15. Startup failures

Se o Core não iniciar:

```text
Startup Failed
```

Mostrar:

- mensagem clara;
- diagnostic code;
- ação recomendada;
- opção de abrir diagnóstico.

Não mostrar apenas:

```text
Connection refused
```

ao usuário final.

---

# 16. Startup recovery

Preparar opções:

```text
Retry
Start Diagnostics
Safe Mode
```

Safe Mode pode inicialmente:

- iniciar Core;
- desativar carregamento automático de módulos problemáticos;
- permitir diagnóstico.

Não implementar mecanismos destrutivos automáticos.

---

# 17. Module-safe startup

Um módulo com falha não deve impedir o Core inteiro de iniciar.

Fluxo:

```text
Module Load
    ↓
Success → Active
Failure → Blocked
    ↓
Core continues
```

Mostrar no Dashboard/Diagnostics:

```text
Module blocked during startup
```

---

# 18. Safe mode

Criar um modo oficial:

```text
TechForge Safe Mode
```

Objetivo:

- iniciar com Core mínimo;
- impedir módulos problemáticos de quebrar o sistema;
- acessar Diagnostics;
- permitir desativar/remover módulos.

Não desativar permanentemente módulos sem informar o usuário.

---

# 19. Shutdown

Ao fechar:

```text
Close Request
↓
Stop accepting new operations
↓
Warn if critical execution active
↓
Shutdown modules
↓
Persist state
↓
Stop backend
↓
Close application
```

O usuário não deve precisar encerrar processos manualmente.

---

# 20. Background behavior

Definir explicitamente se o TechForge pode continuar:

```text
running in background
```

ou:

```text
fully exit when closed
```

Inicialmente preferir:

```text
fully exit when closed
```

para reduzir consumo de recursos.

Futuras funções podem justificar tray mode.

---

# 21. Resource efficiency

O Core Desktop deve ter metas qualitativas:

- baixo consumo em idle;
- sem processos duplicados;
- frontend production build;
- módulos carregados sob demanda quando possível;
- logs com rotação;
- cache limitado.

Não definir números arbitrários sem medição.

---

# 22. Module loading UX

Quando o usuário abrir um módulo:

```text
Menu
↓
Load Module
↓
Initialize if needed
↓
Render inside TechForge
```

O módulo não deve abrir uma nova aba como comportamento padrão.

Menus podem permanecer:

```text
collapsed / auto-hidden
```

para maximizar a área útil.

---

# 23. Full module workspace

Ao abrir um módulo:

```text
Navigation minimized
        ↓
Module workspace
```

O usuário deve conseguir recuperar a navegação facilmente.

Sugestão:

```text
toggle navigation
keyboard shortcut optional
```

Não esconder controles críticos.

---

# 24. Dashboard

Manter o Dashboard simples:

```text
Platform Status
Active Services
Installed Modules
Module Versions
Updates / Warnings
```

Não criar gráficos desnecessários.

O Dashboard não é o produto principal.

Os módulos são.

---

# 25. Notifications

Notificações devem informar:

- módulo instalado;
- atualização disponível;
- módulo bloqueado;
- validação falhou;
- operação concluída;
- erro relevante.

Evitar notificações decorativas.

---

# 26. Updates of Core

Preparar um fluxo:

```text
Check Update
↓
Download/Acquire
↓
Validate
↓
Backup/Prepare
↓
Install
↓
Restart
↓
Migration
↓
Validate
```

Não implementar atualização silenciosa sem política explícita.

---

# 27. Update channels

Preparar:

```text
stable
beta
development
```

Para o Core.

O padrão corporativo deve ser:

```text
stable
```

Não misturar canais sem indicação.

---

# 28. Offline behavior

O Desktop deve funcionar sem Internet após instalado.

Internet pode ser necessária para:

- baixar módulos;
- buscar atualizações;
- módulos que usam APIs externas.

A ausência de Internet não deve impedir:

```text
Core startup
Local modules
Local documentation
```

---

# 29. Proxy and corporate network readiness

Preparar configurações futuras para:

```text
HTTP proxy
HTTPS proxy
corporate certificates
```

Não implementar uma tela complexa agora.

Mas evitar bibliotecas que assumam acesso direto à Internet.

---

# 30. Desktop diagnostics

Integrar:

```text
Diagnostics
```

da Fase 14 ao Launcher.

Ao ocorrer falha de startup, permitir gerar:

```text
Desktop Diagnostic Report
```

com:

- versão;
- paths sanitizados quando necessário;
- status;
- módulos;
- erro;
- logs recentes.

---

# 31. Uninstall

Fluxo deve ser explícito:

```text
Uninstall Application
```

Perguntar ou oferecer opções para:

```text
Keep User Data
Remove User Data
```

Nunca apagar dados de módulos sem informação clara.

---

# 32. Module uninstall integration

Reutilizar o lifecycle:

```text
Deactivate
↓
Available
↓
Remove
↓
Delete Package/Data according to policy
```

Não confundir desinstalação do TechForge com remoção de módulo.

---

# 33. Repair installation

Preparar opção futura:

```text
Repair TechForge
```

Capaz de:

- verificar arquivos do Core;
- validar instalação;
- restaurar componentes;
- preservar dados.

Não implementar reparo agressivo sem integridade verificada.

---

# 34. Desktop logging

Logs do Launcher e Core devem ser correlacionados.

Exemplo:

```text
startup_id
process_id
platform_version
```

A Fase 14 deve ser reutilizada.

---

# 35. User-facing errors

Separar:

```text
User Message
```

de:

```text
Technical Detail
```

Exemplo:

```text
Could not start TechForge.

Diagnostic Code:
TF-STARTUP-001

Open Diagnostics
```

Não exibir stack traces por padrão.

---

# 36. Accessibility

Aplicar princípios básicos:

- navegação por teclado;
- foco visível;
- contraste adequado;
- textos claros;
- controles identificáveis.

Não exigir redesign completo nesta fase.

---

# 37. Localization readiness

Como o uso inicial é corporativo e local, preparar:

```text
pt-BR
```

como idioma principal.

Não hardcodar textos de forma que impeçam:

```text
en-US
```

futuramente.

Não implementar internacionalização completa se não houver necessidade.

---

# 38. Developer mode

Separar explicitamente:

```text
User Mode
```

de:

```text
Developer Mode
```

Developer Mode pode mostrar:

- paths;
- module source;
- logs;
- reload;
- diagnostics técnicos.

Não expor ferramentas de desenvolvimento por padrão ao usuário comum.

---

# 39. Developer workflow

O desenvolvedor deve continuar podendo:

```text
Start Backend
Start Frontend
Hot Reload
Use Local Module Source
```

A distribuição Desktop não deve prejudicar produtividade de desenvolvimento.

---

# 40. Documentation

Documentar:

## User Guide

- instalar;
- iniciar;
- usar Dashboard;
- abrir módulos;
- instalar módulos;
- ativar/desativar;
- atualizar;
- diagnosticar;
- desinstalar.

## IT / Deployment Guide

- requisitos;
- paths;
- instalação;
- proxy;
- logs;
- backup;
- atualização;
- troubleshooting.

## Developer Guide

- Development Mode;
- Launcher;
- local modules;
- debugging;
- packaging.

---

# 41. Developer Center

Adicionar seções:

```text
Desktop Application Architecture
Launcher Lifecycle
Desktop Paths
Safe Mode
Startup Troubleshooting
Development vs Distribution
```

O AI Context deve incluir diferenças entre:

```text
development environment
```

e:

```text
production desktop distribution
```

---

# 42. API

O Desktop Launcher pode utilizar APIs internas:

```text
GET /health
GET /ready
GET /version
GET /diagnostics
```

Não expor APIs de administração de processo ao navegador sem necessidade.

---

# 43. CLI

A CLI continua sendo ferramenta técnica.

Adicionar ou consolidar:

```bash
techforge start
techforge stop
techforge status
techforge safe-mode
techforge diagnostics
techforge repair-check
```

O usuário final não deve depender da CLI.

---

# 44. Packaging validation

Antes da distribuição:

```text
Clean Machine / Clean Environment
↓
Install
↓
Start
↓
Health
↓
Open UI
↓
Install Module
↓
Activate
↓
Use
↓
Close
↓
Restart
```

O teste não pode depender do ambiente de desenvolvimento já configurado.

---

# 45. Upgrade validation

Testar:

```text
Old Version
+
User Data
+
Installed Modules
↓
Upgrade
↓
Migration
↓
Restart
↓
Data Preserved
```

---

# 46. Failure recovery tests

Testar:

```text
Backend startup failure
Module startup failure
Port conflict
Corrupted config
Interrupted update
Failed migration
```

Cada cenário deve possuir comportamento definido.

---

# 47. O que não implementar

Não implementar nesta fase:

- aplicação mobile;
- sincronização obrigatória em nuvem;
- auto-update silencioso;
- tray complexa;
- background service permanente;
- navegador embutido pesado sem justificativa;
- autenticação completa.

O foco é:

```text
Simple Corporate Desktop Experience
```

---

# 48. Critérios de aceitação

A fase estará concluída quando:

1. Usuário final não precisar abrir PowerShell.
2. Um Launcher oficial existir.
3. Backend iniciar automaticamente.
4. Frontend de produção iniciar/servir corretamente.
5. Health e Ready forem verificados.
6. Uma segunda instância não duplicar serviços.
7. Startup failures forem compreensíveis.
8. Diagnostics estiverem integrados.
9. Safe Mode existir ou estar funcionalmente implementado.
10. Módulo com falha não impedir Core.
11. Shutdown for graceful.
12. Application e User Data forem separados.
13. Instalação não exigir Python/Node manualmente.
14. Primeiro startup funcionar.
15. Offline-first for preservado.
16. Módulos abrirem dentro do TechForge.
17. Navegação puder ser minimizada.
18. Dashboard permanecer simples.
19. Updates estiverem arquiteturalmente previstos.
20. User Data for preservado em update.
21. Uninstall não apagar dados silenciosamente.
22. Developer Mode estiver separado.
23. Development workflow continuar funcionando.
24. Documentação de usuário e TI existir.
25. AI Context incluir distribuição.
26. Packaging validation passar.
27. Upgrade validation passar.
28. Failure recovery tests passarem.
29. Todos os testes passarem.
30. Core permanecer leve.

---

# Regra final

Antes de finalizar:

- testar ambiente limpo;
- instalar TechForge;
- iniciar pelo atalho;
- confirmar backend;
- confirmar ready;
- abrir interface;
- abrir módulo;
- minimizar menu;
- fechar aplicação;
- confirmar shutdown;
- iniciar novamente;
- testar segunda instância;
- testar Safe Mode;
- provocar falha de módulo;
- confirmar Core disponível;
- testar offline;
- testar upgrade com dados;
- testar uninstall preservando dados;
- gerar diagnóstico;
- executar todos os testes;
- validar artefato final.

Apresentar:

```text
Distribution Model:
Launcher:
Startup Sequence:
Single Instance:
Application Window Decision:
Frontend Production:
Backend Packaging:
Installation:
User Data:
First Startup:
Failure Handling:
Recovery:
Safe Mode:
Module-Safe Startup:
Shutdown:
Background Behavior:
Resource Efficiency:
Module Workspace:
Dashboard:
Notifications:
Core Updates:
Offline:
Corporate Network:
Diagnostics:
Uninstall:
Repair:
Accessibility:
Localization:
Developer Mode:
Developer Workflow:
Documentation:
Developer Center:
AI Context:
CLI:
Packaging Validation:
Upgrade Validation:
Failure Recovery:
Tests:
Build:
Known Issues:
```
