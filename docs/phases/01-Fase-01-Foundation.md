# TechForge — Fase 1
## Foundation

> **Status:** Prompt de implementação consolidado
>
> **Objetivo:** Criar a fundação inicial do TechForge sem implementar módulos de negócio.

---

## Contexto do projeto

O TechForge é uma plataforma corporativa, inicialmente executada localmente em desktops, destinada a facilitar o trabalho de áreas técnicas e comerciais.

A plataforma será extensível por módulos e poderá crescer ao longo do tempo.

Exemplos futuros de módulos:

- sizing para Veeam Microsoft 365;
- sizing para Salesforce;
- health check de VMware;
- ferramentas de backup;
- virtualização;
- prospecção e análise de leads;
- integrações com provedores de cloud;
- outras ferramentas corporativas.

Nesta fase, **não desenvolver os módulos de negócio**.

O objetivo é criar a fundação técnica sobre a qual os módulos serão construídos posteriormente.

---

# 1. Princípios arquiteturais

O desenvolvimento deve seguir os seguintes princípios.

## Core mínimo

O Core deve permanecer pequeno, estável e independente do crescimento do ecossistema.

Adicionar módulos não deve exigir alterações frequentes no Core.

O Core não deve conter lógica específica de Veeam, VMware, AWS, Salesforce ou qualquer domínio de negócio.

## Modularidade

Toda funcionalidade de negócio deverá existir em módulos.

A plataforma deve ser preparada para receber novos módulos com o mínimo de alteração possível na infraestrutura.

## Extensibilidade

A arquitetura deve permitir crescimento futuro sem exigir reescrita da aplicação.

## Leveza

A plataforma será executada inicialmente em desktops corporativos.

Priorizar:

- baixo consumo de memória;
- baixo consumo de CPU;
- inicialização rápida;
- poucas dependências;
- arquitetura simples;
- facilidade de manutenção.

## Documentação First

A documentação é um ativo da plataforma e deverá evoluir junto com o código.

Nesta fase, preparar uma estrutura documental básica, sem implementar ainda todo o Developer Center.

## Local First, Server Ready

Inicialmente o sistema deve funcionar localmente em uma máquina.

A arquitetura não deve impedir uma futura migração para servidor Linux com múltiplos usuários.

Não implementar multiacesso nesta fase.

---

# 2. Stack tecnológica

Utilizar:

## Backend

- Python
- FastAPI

## Frontend

- React
- TypeScript

## Banco de dados

Inicialmente:

- SQLite

A camada de acesso a dados deve ser preparada para futura migração para PostgreSQL sem espalhar dependências específicas do SQLite pela aplicação.

---

# 3. Estrutura inicial do projeto

Criar uma estrutura organizada semelhante a:

```text
TechForge/
│
├── core/
│   ├── backend/
│   └── frontend/
│
├── modules/
│
├── config/
│
├── docs/
│
├── tests/
│
├── scripts/
│
└── README.md
```

A estrutura pode ser refinada se necessário, mas deve preservar separação clara entre:

- Core;
- módulos;
- configuração;
- documentação;
- testes;
- scripts.

Não criar módulos de negócio nesta fase.

---

# 4. Backend Foundation

Criar a aplicação FastAPI mínima e organizada.

Responsabilidades iniciais:

- inicialização da aplicação;
- configuração;
- logging;
- health check;
- banco de dados;
- APIs básicas da plataforma.

Criar estrutura clara de separação entre:

```text
api/
services/
models/
schemas/
core/
config/
```

Não criar estruturas artificiais ou camadas excessivas.

Reutilizar convenções idiomáticas do FastAPI.

---

# 5. API Health Check

Criar endpoint de saúde da plataforma.

Exemplo:

```text
GET /api/health
```

A resposta deve permitir identificar pelo menos:

- status;
- nome da plataforma;
- versão.

Exemplo conceitual:

```json
{
  "status": "ok",
  "platform": "TechForge",
  "version": "1.0.0"
}
```

Este endpoint será utilizado futuramente pelo Launcher.

---

# 6. Configuração centralizada

Criar mecanismo centralizado de configuração.

Utilizar variáveis de ambiente e arquivos de configuração apropriados.

Exemplo de configuração:

```text
PLATFORM_NAME=TechForge
PLATFORM_VERSION=1.0.0

HOST=127.0.0.1
PORT=8000

DATABASE_URL=sqlite+aiosqlite:///./config/techforge.db

CORS_ORIGINS=[...]
```

Não espalhar:

- URLs;
- portas;
- caminhos;
- versões;
- parâmetros de infraestrutura

pelo código.

---

# 7. Banco de dados

Implementar uma fundação mínima para persistência.

Inicialmente utilizar SQLite.

Requisitos:

- acesso assíncrono quando apropriado;
- configuração centralizada;
- sessão de banco reutilizável;
- inicialização segura;
- estrutura preparada para futura migração para PostgreSQL.

Não implementar tabelas específicas de módulos de negócio.

Criar apenas estruturas realmente necessárias ao Core.

---

# 8. Frontend Foundation

Criar uma aplicação React + TypeScript organizada.

Objetivo inicial:

- carregar a aplicação;
- consumir o backend;
- demonstrar comunicação básica;
- estabelecer estrutura de componentes e rotas.

A interface deve seguir uma linha:

- clean;
- moderna;
- corporativa;
- com baixa poluição visual;
- responsiva.

Não gastar esforço excessivo em funcionalidades visuais nesta fase.

---

# 9. App Shell inicial

Criar uma fundação visual simples para o TechForge.

Estrutura conceitual:

```text
┌──────────────────────────────────────────────┐
│ TechForge                                    │
├───────────────┬──────────────────────────────┤
│               │                              │
│   Navegação   │        Conteúdo              │
│               │                              │
│               │                              │
└───────────────┴──────────────────────────────┘
```

A arquitetura visual deve permitir futuramente:

- menus dinâmicos;
- categorias;
- módulos;
- ocultação/retração da navegação;
- uso máximo da área de conteúdo.

Não implementar ainda toda a lógica de módulos.

---

# 10. Dashboard inicial

Criar um Dashboard simples.

Ele deverá futuramente apresentar:

- status dos serviços;
- módulos encontrados;
- versões dos módulos.

Nesta fase pode apresentar apenas informações disponíveis no Core.

Não transformar o Dashboard em uma central complexa de analytics.

A filosofia visual é:

> mostrar o estado da plataforma de forma simples e objetiva.

---

# 11. Navegação

Preparar estrutura de navegação.

Inicialmente incluir apenas itens essenciais do Core.

Exemplo:

```text
Dashboard
Modules
Developer Center
Settings
```

Os itens podem ser ajustados conforme a arquitetura existente.

Importante:

- a navegação não deve ser baseada em listas rígidas que impeçam crescimento;
- o conteúdo principal deve ocupar a maior área possível;
- futuramente módulos deverão poder contribuir com navegação.

Não implementar ainda a descoberta dinâmica de módulos.

---

# 12. Sem autenticação complexa

Não investir nesta fase em:

- autenticação externa;
- OAuth;
- RBAC complexo;
- permissões por módulo;
- multi-tenant.

O sistema inicialmente será corporativo e interno, sem exposição pública.

A arquitetura deve evitar tornar uma futura autenticação impossível, mas autenticação não é prioridade desta fase.

---

# 13. Logging

Implementar logging estruturado e centralizado.

Registrar pelo menos:

- startup;
- shutdown;
- erros;
- eventos importantes do Core.

Evitar:

- múltiplos sistemas de log concorrentes;
- prints espalhados como mecanismo principal de diagnóstico.

A estrutura deve ser reutilizável pelas fases futuras.

---

# 14. Tratamento de erros

Criar tratamento consistente de erros para a API.

Os erros devem:

- ser previsíveis;
- possuir mensagens úteis;
- não expor detalhes internos desnecessários;
- permitir diagnóstico através dos logs.

Não criar um framework excessivamente complexo.

---

# 15. Qualidade e testes

Criar uma base de testes desde o início.

Cobrir pelo menos:

- inicialização do Backend;
- Health Check;
- carregamento de configuração;
- conexão/inicialização do banco;
- rotas básicas.

O projeto deve possuir um comando claro para executar os testes.

---

# 16. Documentação inicial

Criar documentação inicial em Markdown.

Incluir:

```text
README.md
docs/architecture.md
docs/development.md
```

Documentar:

- objetivo do TechForge;
- stack;
- estrutura do projeto;
- como executar em desenvolvimento;
- como executar testes;
- arquitetura inicial.

Não implementar ainda o Documentation Engine completo.

---

# 17. Requisitos de compatibilidade futura

A Fase 1 deve preparar, sem implementar integralmente:

- sistema modular;
- Marketplace;
- Package Manager;
- Module Registry;
- Service Registry;
- documentação integrada;
- dependências entre módulos;
- execução local;
- execução futura em servidor;
- suporte futuro a múltiplos usuários.

Não antecipar essas funcionalidades criando implementações incompletas ou paralelas.

Apenas evitar decisões arquiteturais que impeçam sua implementação futura.

---

# 18. O que não implementar

Não implementar nesta fase:

- módulos de negócio;
- Marketplace funcional;
- instalação de módulos;
- upload de módulos;
- Service Registry;
- dependências entre módulos;
- autenticação avançada;
- permissões avançadas;
- assinaturas digitais;
- Launcher completo;
- Runtime completo;
- Developer Center completo;
- IA;
- geração automática de módulos.

---

# 19. Critérios de aceitação

A Fase 1 estará concluída quando:

1. O Backend FastAPI iniciar corretamente.
2. O Frontend React/TypeScript iniciar corretamente.
3. O Frontend conseguir comunicar com o Backend.
4. O Health Check funcionar.
5. A configuração estiver centralizada.
6. O banco SQLite estiver funcionando.
7. A arquitetura estiver organizada.
8. O Dashboard inicial estiver funcional.
9. A navegação básica estiver disponível.
10. Logs básicos existirem.
11. Testes básicos estiverem implementados.
12. A documentação inicial estiver em Markdown.
13. Nenhuma lógica de negócio de módulos estiver no Core.
14. A arquitetura permanecer leve e preparada para crescimento modular.

---

# 20. Regra final

Antes de finalizar:

- analisar a estrutura criada;
- executar testes;
- iniciar Backend;
- iniciar Frontend;
- testar comunicação entre ambos;
- validar Health Check;
- validar banco;
- executar build do Frontend.

Apresentar ao final:

```text
Tests:
Backend:
Frontend:
API:
Database:
Build:
Known Issues:
```

Não avançar para a implementação do sistema de módulos nesta fase.
