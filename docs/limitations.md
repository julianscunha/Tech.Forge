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
  dados) depende do instalador que ainda não existe. `techforge update`
  (`git pull` + deps + build + migrations) cobre o caso de quem já roda
  a partir de um clone git — não é esse fluxo guiado, e não serve pra
  quem no futuro instalar via um `.exe`/instalador.
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

- **`sdk.services.invoke()` é síncrono e bloqueante, e nada detecta o uso
  incorreto.** Chamado de dentro de uma rota `async def`, trava o único
  event loop do uvicorn tentando servir sua própria requisição de
  loopback — deadlock silencioso, sem exceção nem log, só descoberto
  testando ao vivo. Achado no desenvolvimento do `system_health_check`
  (Fase System Health). Revisitar: `invoke()` detectar que está rodando
  dentro de um loop async e falhar alto, em vez de travar.
- **`ServicesSDK.http_timeout` tem default de 2.0s, curto para chamadas
  reais de sistema, e não tem override por chamada.** Uma leitura de
  drivers via `Get-CimInstance` sozinha já leva ~2.3s no host de
  referência — forçou setar o atributo mutável antes de cada rota que
  precisava de mais tempo, em vez de passar um timeout explícito no
  próprio `invoke()`. Achado no `system_health_check`.
- **Import relativo (`from . import x`) não funciona em módulo carregado
  via `importlib.spec_from_file_location`**, e o workaround
  (`sys.path.insert(0, Path(__file__).parent)`) não está documentado em
  lugar nenhum — só descoberto por tentativa e erro. Achado no
  desenvolvimento de ambos os módulos da Fase System Health.
- **`node_modules/` esquecido num módulo instalado trava o boot inteiro
  da plataforma, sem pista da causa real.** O scanner de integridade
  (`app/module_trust/integrity.py`) faz hash recursivo de todo arquivo de
  todo módulo instalado, sem excluir `node_modules/` — esquecer de apagar
  após o build do frontend estoura o timeout de readiness (60s) com um
  erro genérico, não algo que aponte pra causa. Contorno atual (não é
  fix do Core): apagar `node_modules/` depois de cada build, convenção só
  informal hoje (`lead_tracker`, `system_health_check`).
- **`techforge validate-module` confirma "export default" por busca
  textual literal, não análise real do bundle.** Bundlers como Rollup em
  lib mode emitem `export { X as default }`, não a string literal — isso
  forçou um plugin Rollup só pra injetar um comentário `// export default`
  fake e aninhar `render`+`moduleConfig` num único objeto default, só
  pra passar no validador. É acoplamento a um detalhe textual, não a uma
  garantia real do contrato.
- **~~Notificação de evento crítico agendada no startup podia vazar entre
  testes.~~ Corrigido.** `notifications_bridge.py` agenda a criação de
  notificações de segurança (`security.integrity_failure` etc.) via
  `loop.create_task()` fire-and-forget quando publicadas dentro de um
  loop já rodando (ex: verificação de integridade no startup do
  `TestClient`) — a task só termina quando alguma requisição HTTP
  seguinte dá oportunidade ao loop, não necessariamente antes do
  `_clean()` de isolamento do teste. Resultado: falha intermitente em
  `test_phase2_notifications.py` (a notificação de segurança materializa
  entre o clean e a asserção). Corrigido drenando `_pending_tasks` via
  `c.portal.call(drain_pending_notifications)` antes do clean, no mesmo
  loop da task — determinístico, 40+ execuções seguidas sem flake.
- **Suíte de testes de dois módulos instalados pode colidir por nome de
  arquivo.** Pytest em modo rootless usa o primeiro `tests/_loader.py`
  (ou qualquer nome de arquivo repetido) importado num processo e
  ignora silenciosamente os demais — quebra a descoberta de testes do
  segundo módulo sem erro nenhum. Contorno: prefixar o nome do loader por
  módulo (`_si_loader.py`, `_shc_loader.py`); não documentado no
  CONTRIBUTING do repo de módulos.
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

- **~~CI travava ~6h no step "CLI test suite".~~ Corrigido — causa raiz era
  um bug real de `techforge_sdk.database.DatabaseSDK`.** `_get_lock()`
  detecta corretamente quando o event loop mudou (ex: chamador fazendo
  `asyncio.run()` por chamada em vez de um loop só pro processo todo) e
  descarta a conexão antiga pra abrir uma nova no loop atual — mas
  descartava sem fechar. Cada conexão aiosqlite roda o driver sqlite3
  síncrono numa `Thread` dedicada não-daemon; sem `close()`, essa thread
  fica presa pra sempre em `self._tx.get()` esperando trabalho que nunca
  chega — e uma thread não-daemon viva impede o processo Python de sair
  de verdade, mesmo com o pytest já tendo impresso "N passed". Achado com
  uma sonda temporária (`aiosqlite.connect()` interceptado +
  `sys._current_frames()` nas threads vivas no fim da sessão) — não
  reproduzia de forma confiável no Windows local (RAM instável na máquina
  de dev), mas era 100% reproduzível no runner Linux do CI. Testado por
  `test_database_insert_fetch_across_separate_event_loops`
  (`cli/tests/test_phase3.py`), que já existia justamente pra essa
  regressão de troca de loop, mas nunca fechava a última conexão no fim.
  Corrigido em duas frentes: `_get_lock()` agora fecha a conexão obsoleta
  antes de descartá-la, e o teste fecha a conexão final explicitamente.
  `timeout-minutes` no `ci.yml` (15 no job, 5 no step de CLI) continua
  como teto de segurança independente da causa raiz.

O item abaixo fica só neste documento porque depende de um fluxo
de update/instalador ainda inexistente, mesma lógica das decisões de
escopo acima:

- `uvicorn --reload` (modo dev) costuma deixar um processo worker órfão
  vivo mesmo depois de matar o PID do reloader — é comportamento do
  watcher, não do Core, mas atrapalha quem repete o ciclo de teste
  manual local sem saber que precisa localizar o PID real via
  `netstat`/`tasklist`.
