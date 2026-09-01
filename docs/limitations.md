---
title: Limitações Conhecidas — TechForge
category: governanca-setup
domain: [governanca-setup]
tags: [limitations, roadmap]
---

# Limitações Conhecidas

Este documento reúne o que o TechForge **não faz hoje**, dividido em duas
categorias bem diferentes: decisões conscientes de escopo (não são bugs,
não é falta de tempo — é o projeto optando por não resolver algo que não
tem caso de uso real ainda) e limitações reais candidatas a melhoria
futura. Nenhum item aqui é segredo escondido — é o inventário honesto do
estado atual da plataforma.

## Fora de escopo por decisão de design

- **Sem watchdog/restart automático do launcher.** A supervisão é
  on-demand (`techforge status`/`start`), não um processo de vigia rodando
  em background. Preferência deliberada por diagnóstico explícito em vez
  de reinício automático silencioso.
- **Endpoints genéricos de execução/cancelamento de módulo
  (`execute`/`cancel`) não existem.** O contrato de cancelamento
  (`CancellationToken`/`ProgressReport`) já existe e é testado, mas nenhum
  módulo real declara uma ação de execução hoje — um endpoint genérico
  sem consumidor seria arbitrário.
- **Diagnóstico por módulo não tem seção dedicada na própria página do
  módulo.** O backend já expõe o dado (`get_diagnostics()`); a UI
  específica fica pra quando um módulo real precisar dela.
- **`techforge logs --follow` usa polling simples (0.5s)**, não um
  mecanismo de notificação de arquivo (inotify ou equivalente).
  Suficiente para o volume de log de um desktop single-user.
- **Sem instalador Windows gráfico (GUI/MSI).** Hoje a plataforma é
  distribuída como repositório + build manual do backend
  (PyInstaller onedir). "Baixar e instalar com um clique" ainda não
  existe.
- **Update, uninstall e repair formais não são fluxos de usuário
  completos.** A separação entre diretório de instalação e diretório de
  dados do usuário já garante que reinstalar preserva dados — mas um
  fluxo guiado de update/desinstalação com opções (manter ou remover
  dados) depende do instalador que ainda não existe.
- **Sem tela de configuração de proxy corporativo.** Nada na plataforma
  hoje assume acesso direto à internet, mas configurar proxy/certificados
  explicitamente ainda não tem interface.
- **Configuração de módulo não suporta campos do tipo lista/array.** A
  Module Storage API é key-value simples, sem provisionamento de schema
  relacional por módulo. Ambas decisões conscientes — revisitar quando um
  módulo real precisar de algo mais rico.

## Limitações conhecidas, candidatas a melhoria futura

- **Hot-unload de módulo não existe.** Desativar um módulo não descarrega
  o código já montado em runtime — é preciso reiniciar a plataforma para
  o efeito ser completo.
- **Aviso de confiança (trust) na instalação nunca chega ao usuário.** A
  política de segurança já decide corretamente não bloquear instalação
  por nível de confiança isolado, e já calcula quando deveria emitir um
  aviso — mas esse aviso nunca é de fato exibido em nenhum fluxo de
  instalação ou atualização hoje. É uma peça pronta que não foi conectada
  na interface.
- **Conflito de capability entre módulos concorrentes é só reportado, sem
  política de resolução automática.** Se dois módulos oferecerem a mesma
  capability, não há uma regra de precedência definida.
- **Estado de dependência bloqueada não é recalculado automaticamente no
  boot.** Se uma dependência de um módulo é removida enquanto a
  plataforma está desligada, o estado só é reavaliado na próxima ativação
  explícita, não no próximo start.
- **Não é possível instalar ou consultar uma versão antiga específica de
  um módulo.** O armazenamento local preserva todo pacote já publicado,
  mas nada expõe rollback de versão hoje.
- **Secret Store depende do `keyring` do sistema operacional**, sem
  fallback para ambientes Linux headless sem D-Bus/Secret Service — só
  relevante para quem tentar rodar sem sessão gráfica.
- **`techforge validate-module` pode falhar no console do PowerShell no
  Windows** por incompatibilidade de encoding com os glifos usados na
  saída formatada — não reproduzido em terminais UTF-8.

## Notas técnicas (baixo impacto no uso, relevantes para quem for mexer no código)

- Um ponto do Package Manager importa a instância viva da aplicação
  (`app.main`) para montar rotas de um módulo recém-ativado sem reiniciar
  o processo — funciona, mas é uma inversão de camada que qualquer
  refatoração futura do bootstrap deve levar em conta.
- Uma rota de segurança reaproveita um handler de outra rota como se
  fosse um serviço compartilhado, em vez de ambas chamarem uma camada de
  serviço comum.
- Existem dois tipos distintos chamados `RuntimeState` no código (um para
  o estado da plataforma, outro para o estado de execução de um módulo) —
  colisão de nome, não de comportamento.
- O ciclo de vida de um módulo é modelado em três estruturas de estado
  separadas (job de instalação, estado administrativo, estado de
  runtime) em vez de uma única máquina de estados — o comportamento está
  correto, só a organização interna diverge do que a documentação de
  arquitetura descreve como exemplo.
- Uma classe de repositório remoto de módulos ficou órfã no código depois
  que a funcionalidade equivalente foi entregue por outro caminho — é
  código morto, candidato a remoção simples.
- O registro de execução de módulos silenciosamente não persiste se
  chamado de dentro de um event loop assíncrono já em execução — funciona
  hoje porque o único ponto de chamada real é síncrono, mas é frágil a um
  futuro caminho de execução assíncrono.
- O registro de jobs de instalação remota é um dicionário em memória
  amarrado ao processo que o criou — não sobreviveria a múltiplos
  processos trabalhando em paralelo, cenário que não existe hoje por
  design (a plataforma é single-process).
- A cobertura de teste do health-check de armazenamento só cobre o
  caminho saudável — nenhum teste simula disco cheio ou indisponível.
- A suíte de testes do backend ainda tem uma falha conhecida dependente
  da ordem de execução (passa isoladamente, falha ocasionalmente quando
  rodada junto com o resto da suíte) — o banco de dados usa uma conexão
  compartilhada por todo o processo de teste, mas cada teste que sobe a
  aplicação roda num loop assíncrono próprio; ocasionalmente uma conexão
  criada num loop já encerrado é reaproveitada por um teste posterior e
  a operação falha ao tentar notificar o loop antigo. Não afeta
  produção (lá a aplicação sobe uma única vez, um único loop). (Uma
  segunda causa, uma corrida real que vazava notificação de segurança
  pro banco de teste compartilhado, já foi corrigida.)
- Uma parte da validação de compliance de documentação está duplicada
  entre o CLI e o motor de documentação do Core.
- A interface do frontend nunca foi verificada visualmente em navegador
  real por uma ferramenta de automação — a build (compilação) é
  verificada, o comportamento visual não.
- A validação de empacotamento em máquina limpa nunca foi 100% real —
  só simulada num ambiente que ainda tinha o repositório presente.
