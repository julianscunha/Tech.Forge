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
- **Sem runtime compartilhado (React/etc.) entre Core e módulos.** Cada
  módulo React empacota sua própria cópia do framework — duplica bytes no
  navegador se vários módulos React forem instalados juntos, mas evita
  acoplamento de versão/ABI entre módulos independentes. Revisitar só com
  medição real de múltiplos módulos React instalados simultaneamente.

## Limitações conhecidas, candidatas a melhoria futura

- **O material de referência para frontends de módulo ainda é vanilla JS.** O
  Core serve assets estáticos, mas não há um módulo de referência com
  React/TypeScript e bundle ESM (por exemplo, Vite library mode). É uma lacuna
  de documentação e exemplo, não uma limitação do runtime.
- **Hot-unload de módulo não existe.** Desativar um módulo não descarrega
  o código já montado em runtime — é preciso reiniciar a plataforma para
  o efeito ser completo.
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

## Notas técnicas (baixo impacto no uso, relevantes para quem for mexer no código)

Achados pontuais de código (inversões de camada, nomes colidentes, código
morto, lacunas de cobertura de teste, etc.) são rastreados com ID,
prioridade e motivo do adiamento em
[`docs/architecture/technical-debt-registry.md`](architecture/technical-debt-registry.md)
— não duplicados aqui.

Os dois itens abaixo ficam só neste documento porque dependem de um fluxo
de update/instalador ainda inexistente, mesma lógica das decisões de
escopo acima:

- O ciclo completo de upgrade (`upgrade(from_version)`) e desinstalação
  real a partir de um `.mod` empacotado não tem teste de integração
  ponta a ponta — só o contrato isolado e `scan_installed()` são
  cobertos hoje.
- `uvicorn --reload` (modo dev) costuma deixar um processo worker órfão
  vivo mesmo depois de matar o PID do reloader — é comportamento do
  watcher, não do Core, mas atrapalha quem repete o ciclo de teste
  manual local sem saber que precisa localizar o PID real via
  `netstat`/`tasklist`.
