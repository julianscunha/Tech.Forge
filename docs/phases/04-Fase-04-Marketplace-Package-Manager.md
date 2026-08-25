---
title: TechForge — Fase 4
category: fases
domain: [fases]
---

# TechForge — Fase 4
## Marketplace & Package Manager

> **Status:** Prompt de implementação consolidado
>
> **Objetivo:** Implementar o gerenciamento oficial de módulos, incluindo catálogo, instalação, ativação, desativação e remoção física, mantendo o Core leve e sem antecipar Service Registry ou Dependency Governance completos.

---

# 1. Contexto

A Fase 3 implementou a base do sistema de módulos:

- descoberta;
- manifest;
- validação;
- Registry;
- Loader;
- tipos `application` e `service`;
- integração visual interna;
- APIs e CLI básicas.

Nesta fase, implementar o gerenciamento do ciclo físico dos módulos.

O usuário deverá conseguir:

```text
descobrir
↓
instalar
↓
utilizar
↓
desativar
↓
reinstalar/reativar
↓
remover permanentemente
```

A regra de UX é crítica:

> **Desativar não é remover.**

Um módulo desativado continua instalado e disponível para reativação.

A remoção é uma ação explícita e remove o módulo fisicamente.

---

# 2. Conceitos oficiais

Definir claramente:

## Disponível

Módulo conhecido pelo catálogo, mas não instalado.

## Instalado

Módulo presente localmente e registrado.

## Ativo

Módulo instalado e disponível para uso.

## Desativado

Módulo instalado localmente, mas não disponível para execução ou interação.

## Removido

Módulo apagado fisicamente da instalação local.

Fluxo:

```text
AVAILABLE
    ↓ install
INSTALLED
    ↓ activate
ACTIVE
    ↓ deactivate
DISABLED
    ↓ activate
ACTIVE
    ↓ remove
REMOVED
```

Um módulo só pode ser removido permanentemente de forma explícita.

---

# 3. Marketplace

Implementar uma página simples de módulos disponíveis.

Nesta fase, o Marketplace não precisa depender de um serviço externo.

Pode utilizar:

- catálogo local;
- repositório configurado;
- fonte local de pacotes.

A arquitetura deve permitir fonte remota futuramente.

Exibir:

- nome;
- descrição;
- versão;
- categoria;
- vendor;
- module type;
- compatibilidade;
- status.

A interface deve ser:

- clean;
- moderna;
- objetiva;
- sem excesso de informações.

---

# 4. Separação entre catálogo e instalação

Não confundir:

```text
Marketplace Catalog
```

com:

```text
Installed Modules
```

Um módulo pode existir no catálogo e não estar instalado.

Um módulo instalado pode ter origem em:

- catálogo;
- pacote local;
- instalação manual de desenvolvimento.

Preparar um modelo que preserve a origem do módulo.

Exemplo conceitual:

```text
source:
  type: catalog | local | development
  location: ...
```

---

# 5. Package format

Definir formato oficial de pacote.

Preferir um formato simples.

Exemplo:

```text
.tfmodule
```

Internamente poderá ser um arquivo ZIP estruturado.

Exemplo:

```text
module.tfmodule
│
├── manifest.yaml
├── backend/
├── frontend/
├── docs/
├── tests/
└── assets/
```

Não criar um formato binário proprietário desnecessário.

O pacote deve ser inspecionável.

---

# 6. Instalação

O fluxo de instalação deverá ser:

```text
Package/Catalog Entry
        ↓
Read Manifest
        ↓
Validate Package
        ↓
Validate Compatibility
        ↓
Validate Integrity (foundation)
        ↓
Extract/Install
        ↓
Module Discovery
        ↓
Register
        ↓
Installed
```

Se qualquer etapa falhar:

- não deixar instalação parcial;
- registrar erro;
- realizar rollback/cleanup quando necessário.

Não implementar ainda assinatura digital completa; preparar ponto de integração para fase futura.

---

# 7. Instalação por arquivo local

Permitir que um pacote local seja selecionado para instalação.

A interface poderá futuramente possuir:

```text
Install Module
```

e permitir:

```text
Select .tfmodule
```

Não permitir que arquivos sejam extraídos diretamente sem validação.

---

# 8. Diretório observado de instalação

Preparar uma área controlada para pacotes locais.

Exemplo:

```text
modules/packages/
```

ou:

```text
modules/incoming/
```

Não implementar auto-extração irrestrita apenas porque um ZIP apareceu na pasta.

Se houver suporte a diretório observado, o fluxo deve ser seguro:

```text
Package detected
    ↓
Validate
    ↓
Notify
    ↓
Explicit install
```

A instalação explícita é preferível à execução automática de código.

---

# 9. Ativação

Quando um módulo estiver instalado, ele poderá ser ativado.

Ativação deve:

- tornar o módulo disponível;
- permitir integração com o Runtime;
- disponibilizar navegação quando aplicável;
- tornar funcionalidades acessíveis.

Não permitir que um módulo desativado continue:

- aparecendo como utilizável;
- respondendo normalmente;
- sendo carregado como ativo.

---

# 10. Desativação

Quando o usuário escolher:

```text
Deactivate
```

o sistema deverá:

- remover o módulo da navegação ativa;
- impedir interação normal;
- impedir novas execuções;
- preservar os arquivos;
- preservar metadados necessários;
- permitir reativação.

O módulo não deve ser apagado.

Após desativação, ele deve aparecer claramente como:

```text
DISABLED
```

---

# 11. Remoção permanente

A remoção física deve ser uma ação distinta.

Fluxo:

```text
Active
↓
Deactivate
↓
Disabled
↓
Remove
↓
Confirm
↓
Physical deletion
↓
Registry cleanup
```

Não permitir que o botão de desativação apague arquivos.

Ao remover:

- apagar arquivos do módulo;
- remover registro ativo;
- remover contribuições de navegação;
- remover informações de runtime aplicáveis;
- atualizar interface.

Se a remoção falhar parcialmente:

- não reportar sucesso incorretamente;
- registrar detalhes;
- manter estado consistente;
- permitir recuperação.

---

# 12. UX dos módulos

Na página de módulos, separar claramente:

## Ativos

Módulos utilizáveis.

## Instalados / Desativados

Módulos presentes, mas não em uso.

## Disponíveis

Módulos que podem ser instalados.

Evitar uma única lista confusa.

A interface deve permitir entender imediatamente:

```text
Install
Activate
Deactivate
Remove
```

Não utilizar o mesmo botão para ações semanticamente diferentes.

---

# 13. Package Manager

Implementar o Package Manager funcional.

Responsabilidades:

- localizar pacotes;
- validar;
- instalar;
- registrar;
- ativar;
- desativar;
- remover;
- atualizar metadados.

Não permitir que o Frontend execute operações físicas diretamente.

Fluxo:

```text
Frontend
    ↓
Core API
    ↓
Package Manager
    ↓
Filesystem / Registry
```

---

# 14. Compatibilidade

Antes da instalação, validar compatibilidade com o Core.

Exemplo:

```yaml
compatibility:
  techforge: ">=1.0.0,<2.0.0"
```

Se incompatível:

```text
INCOMPATIBLE
```

Não instalar automaticamente.

Exibir:

- versão atual do TechForge;
- requisito do módulo;
- motivo da incompatibilidade.

---

# 15. Dependências — preparação

O manifest pode declarar dependências.

Exemplo conceitual:

```yaml
dependencies:
  - aws_connector >=1.0.0
```

Nesta fase:

- armazenar a declaração;
- exibir a informação;
- impedir instalação claramente impossível, quando a informação já estiver disponível.

Não implementar o resolvedor completo.

A governança completa será implementada na Fase 8.1.

Regra futura já estabelecida:

> Service Modules não podem depender de Application Modules.

> Application Modules podem depender de Service Modules.

Não implementar ainda todo o grafo de dependências nesta fase.

---

# 16. Atualização

Preparar o fluxo de atualização.

Nesta fase, pode ser uma implementação inicial.

Fluxo conceitual:

```text
Installed Module
    ↓
New Package
    ↓
Validate
    ↓
Compatibility
    ↓
Backup/Rollback Point
    ↓
Replace
    ↓
Registry Refresh
```

Não sobrescrever silenciosamente uma instalação sem validação.

Preservar possibilidade de rollback futuro.

---

# 17. Integrity foundation

Preparar metadados para futura validação de integridade.

Exemplo:

```text
package_hash
signature
publisher
```

Nesta fase:

- não implementar assinatura completa;
- não criar criptografia própria;
- preparar os pontos de extensão.

A Fase 10 implementará governança de segurança e assinaturas.

---

# 18. APIs

Adicionar APIs coerentes.

Exemplos:

```text
GET    /api/v1/marketplace/modules
GET    /api/v1/modules
GET    /api/v1/modules/{id}

POST   /api/v1/modules/install
POST   /api/v1/modules/{id}/activate
POST   /api/v1/modules/{id}/deactivate
DELETE /api/v1/modules/{id}
```

Os nomes podem ser ajustados à arquitetura existente.

As operações devem retornar estados claros.

---

# 19. CLI

Adicionar comandos equivalentes.

Exemplo:

```bash
techforge modules available
techforge modules installed
techforge modules install <package>
techforge modules activate <module_id>
techforge modules deactivate <module_id>
techforge modules remove <module_id>
```

A CLI deve reutilizar o Package Manager.

Não duplicar lógica de instalação.

---

# 20. Notificações

> **Nota de implementação (2026-08-25):** a Notification Foundation já está
> implementada (Fase 2 fechada): tabela `notifications`, `NotificationService`
> e API `/api/v1/notifications` com suporte a `module_id`. Incluir neste fase a
> integração do canal dos módulos: `NotificationsSDK.push()` (sdk/python) deve
> entregar as notificações no Core via `POST /api/v1/notifications`, para que os
> eventos abaixo apareçam no bell da UI — sem criar um segundo sistema.

Utilizar a Notification Foundation para informar:

- instalação concluída;
- instalação falhou;
- incompatibilidade;
- módulo ativado;
- módulo desativado;
- remoção concluída;
- atualização disponível futuramente.

Não criar um segundo sistema de notificações.

---

# 21. Dashboard

Manter o Dashboard simples.

Nesta fase pode apresentar:

- módulos ativos;
- módulos instalados;
- módulos com erro;
- versão.

Não transformar o Dashboard em um centro de administração complexo.

---

# 22. Documentação

Criar documentação oficial.

Estrutura sugerida:

```text
docs/developer-center/modules/
├── packaging.md
├── installation.md
├── activation.md
├── deactivation.md
├── removal.md
├── compatibility.md
└── package-format.md
```

Documentar:

- formato do pacote;
- instalação;
- estados;
- ativação;
- desativação;
- remoção;
- compatibilidade;
- origem dos módulos.

A documentação deve ser suficientemente clara para desenvolvedores humanos e futuras ferramentas de IA.

---

# 23. Testes

Criar testes para:

- pacote válido;
- pacote inválido;
- manifest inválido;
- instalação;
- rollback de instalação;
- módulo incompatível;
- ativação;
- desativação;
- remoção física;
- remoção da navegação;
- Registry refresh;
- instalação duplicada;
- origem local;
- CLI;
- APIs.

Criar teste de fluxo completo:

```text
Available
↓
Install
↓
Installed
↓
Activate
↓
Active
↓
Deactivate
↓
Disabled
↓
Remove
↓
Physically Removed
```

Também validar especificamente o bug arquitetural:

> Um módulo removido/desativado não pode continuar clicável ou disponível para interação como se estivesse ativo.

---

# 24. O que não implementar

Não implementar nesta fase:

- Marketplace público;
- autenticação no Marketplace;
- pagamento;
- monetização;
- Service Registry;
- resolvedor completo de dependências;
- Dependency Governance;
- assinatura digital completa;
- Launcher;
- Runtime avançado;
- sandbox;
- multiusuário.

---

# 25. Critérios de aceitação

A fase estará concluída quando:

1. O catálogo de módulos existir.
2. Módulos disponíveis puderem ser diferenciados de instalados.
3. Pacotes locais puderem ser validados.
4. Instalações inválidas não deixarem arquivos parciais.
5. Compatibilidade com o Core for validada.
6. Módulos puderem ser ativados.
7. Módulos puderem ser desativados sem serem apagados.
8. Módulos desativados não puderem ser utilizados.
9. Módulos desativados puderem ser reativados.
10. Remoção apagar fisicamente o módulo.
11. Remoção atualizar Registry e interface.
12. Módulos removidos não permanecerem nos menus.
13. CLI e API reutilizarem o mesmo Package Manager.
14. Dependências puderem ser declaradas, mesmo que ainda não totalmente resolvidas.
15. A arquitetura estiver preparada para integridade e assinaturas futuras.
16. Nenhuma funcionalidade anterior for quebrada.
17. O Core continuar leve.

---

# Regra final

Antes de finalizar:

- executar todos os testes existentes;
- executar novos testes;
- instalar um módulo válido;
- testar módulo incompatível;
- testar pacote inválido;
- testar rollback;
- ativar;
- desativar;
- confirmar que desapareceu da navegação ativa;
- reativar;
- remover;
- confirmar exclusão física;
- confirmar que não permanece clicável;
- executar build do Frontend.

Apresentar:

```text
Catalog:
Install:
Activation:
Deactivation:
Removal:
Filesystem Cleanup:
Registry:
Navigation:
Compatibility:
CLI:
API:
Tests:
Build:
Known Issues:
```

Não avançar para Service Registry ou Dependency Governance nesta fase.
