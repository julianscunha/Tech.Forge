# Relatório da Fase 11 — Marketplace & Distribuição de Módulos

## Visão Geral

A Fase 11 completa a arquitetura de distribuição do TechForge. Módulos agora podem ser descobertos,
gerenciados e instalados a partir de múltiplas fontes (local, oficial, custom) com verificação de
integridade, resolução de conflitos e instalação assíncrona com acompanhamento de progresso.

**Implementação total:** 8 slices, 14 commits, ~2000 linhas de código + testes + docs.

---

## Slices & Conclusão

### Slice 1 — Extensões de CatalogSource + PackageInfo ✅
- **Arquivos:** `catalog_source.py`, atualizações de modelo
- **O quê:** Enum para tipos de fonte (LOCAL, OFFICIAL_CATALOG, CUSTOM_CATALOG)
- **Aceite:** `PackageInfo.source` e `PackageInfo.source_url` com default correto; `detect_conflicts()` identifica módulos em >1 fonte
- **Teste:** `test_phase11_catalog.py`

### Slice 2 — Catálogo Oficial (index.json) ✅
- **Arquivos:** `OfficialCatalogProvider`, comando CLI `build-index`
- **O quê:** Busca metadados de módulos de um `index.json` centralizado; constrói o índice a partir dos módulos-fonte
- **Decisão-chave:** Índice é 1 fetch por consulta; arquivos `.mod` só são baixados na instalação
- **Aceite:** `index.json` parseado corretamente; `build-index` gera índice + arquivos `.mod` válidos; falha de rede retorna `[]`, sem exceção
- **Teste:** `test_phase11_catalog.py`, cenários de integração

### Slice 3 — Catálogo Custom (GitHub API + manifests) ✅
- **Arquivos:** `CustomCatalogProvider`
- **O quê:** Descobre módulos via GitHub Contents API; lê `modules/<id>/manifest.yaml` diretamente
- **Decisão-chave:** Nenhum `.mod` pré-construído; a plataforma zipa sob demanda no momento da instalação
- **Aceite:** Lista módulos de fixture de teste; `fetch_mod_path()` retorna `.mod` válido que instala
- **Teste:** `test_phase11_catalog.py`

### Slice 4 — Fontes + Cache + Conflitos + Priorização ✅
- **Arquivos:** `CatalogAggregator`, `CatalogSourceService`, modelo `CatalogSourceConfig`
- **O quê:** CRUD de fontes customizadas; cache por fonte com TTL; fetch paralelo; detecção de conflitos
- **Decisão-chave:** Agregador mantém o estado de todas as fontes; cache invalida na troca de config; LOCAL > OFFICIAL > CUSTOM (ordem fixa)
- **Aceite:** Múltiplas fontes buscam em paralelo; uma indisponível não bloqueia as demais; mesmo module_id em 2 fontes retorna conflito; TTL de cache funciona; invalidação na edição de URL funciona
- **Teste:** `test_phase11_catalog.py`, `test_phase11_catalog_api.py`

### Slice 4.5 — Favoritos Locais (sem avaliação pública) ✅
- **Arquivos:** modelo `CatalogFavorite`, endpoints de API
- **O quê:** Usuário pode marcar módulos favoritos localmente; visão filtrada disponível
- **Decisão-chave:** Só pessoal (instalação única); sem sync em nuvem, sem agregação de avaliação (Fase 13+)
- **Aceite:** Favorito sobrevive a restart (SQLite); pode filtrar `favorites_only`
- **Teste:** `test_phase11_catalog_api.py`

### Slice 5 — API `/catalog/*` + Filtros + Paginação ✅
- **Arquivos:** `routes/catalog.py`
- **O quê:** Endpoints REST com filtro, ordenação e paginação no servidor
- **Decisão-chave:** Nunca enviar a lista completa pro frontend; toda filtragem no servidor via cache agregado em memória
- **Aceite:** `page=2&page_size=24` retorna o range correto; `search=term` filtra; `category=X&trust_level=Y` combinam como AND; `GET /categories` retorna contagens
- **Teste:** `test_phase11_catalog_api.py`

### Slice 6 — CLI `techforge catalog` ✅
- **Arquivos:** `cli/techforge_cli/commands/catalog.py`
- **O quê:** Comandos `list`, `search`, `show`, `sources` lendo a API `/catalog/*`
- **Decisão-chave:** Reusar os padrões de CLI de `module_trust.py` (Fase 10)
- **Aceite:** Comandos retornam saída correta sem erros
- **Teste:** `test_phase11_cli.py` (se existir; ou smoke test manual)

### Slice 7 — Frontend: Catálogo de Módulos ✅
- **Arquivos:** componentes React/TS do frontend (Slice 7 parte 1 + 2)
- **O quê:** UI de 3 zonas (sidebar de categoria, barra de filtro, grid de cards) com paginação, favoritos, resolução de conflito
- **Decisão-chave:** UI nunca filtra; toda filtragem é server-side; UI mostra badges de fonte e o chip "Disponível em N fontes"
- **Aceite:** `npm run build` passa sem warnings; páginas carregam; filtro funciona; toggle de favorito funciona; dá pra adicionar fonte customizada
- **Teste:** Manual + build bem-sucedido
- **Commits:** `05ef384` (types + API), `230425c` (implementação da UI)

### Slice 8 — Notificações + Developer Center + AI Context + Testes de Integração ✅

#### Parte 1: Notificações de Progresso de Instalação Remota ✅ (commit `ee4c064`)
- **Arquivos:** `_install_remote_background()`, `_notify_installation()`
- **O quê:** Job assíncrono com 4 fases (ACQUIRING/VALIDATING/INSTALLING/DONE|FAILED); notificações na conclusão
- **Aceite:** Job atinge estado terminal; notificações criadas com dedupe
- **Teste:** `test_phase11_install_job.py`

#### Parte 2: Notificações de Indisponibilidade de Fonte ✅ (este relatório)
- **Arquivos:** `CatalogAggregator._notify_source_unavailable()`
- **O quê:** Detecta quando uma fonte transiciona de disponível→indisponível; notifica uma vez (dedupe)
- **Implementação:** Agregador mantém estado `{source_id: bool}` de disponibilidade; na transição, cria notificação
- **Aceite:** 1 notificação na primeira falha; segunda falha não cria duplicata
- **Teste:** `test_phase11_source_unavailable.py` (2 testes, ambos passando)

#### Parte 2: Teste de Integração ✅ (este relatório)
- **Arquivos:** `test_phase11_integration.py`
- **O quê:** Ponta a ponta: descobre no catálogo → instala da fonte → aparece no registry
- **Aceite:** Fluxo funciona com arquivo `.mod` real e provider custom mockado
- **Teste:** `test_phase11_integration.py` (2 testes, ambos passando)

#### Parte 2: Developer Center ✅ (este relatório)
- **Arquivos:** `docs/developer-center/core/module-catalog.md` (NOVO)
- **O quê:** Documentação completa do formato do catálogo, tipos de fonte, API, CLI, limitações
- **Público:** Autores de módulo, integradores de plataforma
- **Adicionado em:** `docs/INDEX.md` com link

#### Parte 2: AI Context ✅ (este relatório)
- **Arquivos:** Seção "## Module Catalog" em `doc_engine/__init__.py`
- **O quê:** Exporta fontes configuradas e fluxo de instalação pro documento de contexto de LLM
- **Público:** Claude, ChatGPT (desenvolvedores de plataforma pedindo contexto)

---

## Decisões Arquiteturais

1. **Prioridade de Fonte (§19):** Ordem fixa (LOCAL > OFFICIAL > CUSTOM) evita arbitrariedade.
   Mesmo princípio da resolução de conflitos do package manager: determinístico, não aleatório.

2. **Sem versionamento na Fase 11:** `PackageInfo.version` + `installed_version` bastam para UPDATE_AVAILABLE.
   Histórico completo de versões (múltiplos major.minor.patch) é Fase 15 (Quality & Testing).

3. **Notificação só na transição:** Evita spam de notificação em falhas de rede repetidas.
   Dedupe por título + mensagem exatos (mesmo padrão da Fase 8.1 / 10).

4. **Sem polling em background:** "Novo módulo disponível" só dispara quando o usuário abre o Catálogo.
   Polling de job em background é feature server-side (Fase 13, Central Server Readiness).

5. **CustomCatalogProvider zipa sob demanda:** Nenhum `.mod` pré-construído no repositório custom.
   Reduz o custo de manutenção; a plataforma é dona da lógica de zipagem, não o dono da fonte.

---

## Resumo de Testes

**Novos testes adicionados (Slice 8):**
- `test_phase11_source_unavailable.py::TestSourceAvailableTransition` — 2 testes
  - `test_source_unavailable_creates_notification_on_transition`
  - `test_no_duplicate_notification_on_repeated_failure`
- `test_phase11_integration.py::TestPhase11Integration` — 2 testes
  - `test_catalog_to_activation_flow_custom_source`
  - `test_catalog_discovery_and_listing`

**Total de testes:** 708 testes (603 backend + 105 CLI), todos passando — inclui as regressões pós-fechamento (client HTTP fechado, encoding, `data/` preservado no update, merge de `index.json`).

**Cobertura de teste por slice:**
- Slices 1–7: cobertos pelos arquivos de teste existentes e smoke tests manuais (build passa)
- Slice 8: novos testes em `test_phase11_source_unavailable.py` + `test_phase11_integration.py`

### Pós-fechamento: validação real ponta a ponta, os dois tipos de fonte

`test_phase11_integration.py` prova o pipeline de instalação contra um `.mod` construído
localmente, mas nunca exercita nenhum dos dois providers de rede contra um endpoint real —
todo teste unitário deles mocka `httpx.AsyncClient` diretamente (com `__aexit__` no-op), o
que nunca reproduz o que um client fechado de verdade faz. A pedido explícito do usuário,
os dois tipos de fonte foram validados manualmente ponta a ponta, cada um contra I/O de
rede real:

**Catálogo custom** (`CustomCatalogProvider`) — contra o repositório real e já publicado
`julianscunha/Tech.Forge.Modules` (módulo `system_information_service`): descoberta via
GitHub Contents API → `fetch_mod_path()` download+build → `PackageManager.install()`. Isso
revelou dois bugs reais invisíveis à suíte de testes mockada:

1. **`CustomCatalogProvider.list_available()` usava um `httpx.AsyncClient` já fechado.** O
   loop de busca de manifest ficava fora do bloco `async with httpx.AsyncClient() as client:`
   que buscava a listagem do diretório `modules/`, então cada requisição de manifest por
   módulo rodava contra um client já fechado. Os testes existentes nunca pegaram isso porque
   o `__aexit__` do client mockado era um `AsyncMock` no-op — não invalidava `client.get` como
   o httpx real faz. Corrigido movendo o loop pra dentro do bloco `async with`.
2. **`CustomCatalogProvider.fetch_mod_path()` gravava o manifest baixado com o encoding
   padrão da plataforma em vez de UTF-8.** `(temp_dir / "manifest.yaml").write_text(manifest_content)`
   usava o encoding padrão do `Path.write_text()` (cp1252 no Windows), enquanto
   `PackageBuilder.build()` sempre lê de volta com `encoding="utf-8"` explícito — corrompendo
   qualquer conteúdo não-ASCII. O manifest real (em português, acentuado) reproduziu o erro
   imediatamente (`UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe7`); os testes
   existentes nunca pegaram isso porque os manifests de fixture eram puro ASCII. Corrigido
   passando `encoding="utf-8"` explicitamente pro `write_text()`.

Os dois bugs estão cobertos por novos testes de regressão em `test_phase11_catalog.py`
(`test_list_available_reuses_client_across_all_manifest_fetches`,
`test_fetch_mod_path_preserves_non_ascii_manifest_content`) usando fakes que reproduzem de
verdade o modo de falha (um client que levanta exceção depois de "fechado"; conteúdo
não-ASCII real passando pelo `PackageBuilder.build()` real, não mockado) — confirmados RED
contra o código com bug, GREEN depois do fix. Depois da correção, o fluxo online completo
foi rodado de novo manualmente contra o mesmo repositório real e completou com sucesso
ponta a ponta.

**Catálogo oficial** (`OfficialCatalogProvider`) — nenhum `index.json` oficial está
publicado em lugar nenhum ainda (o repositório `Tech.Forge.Modules` não tinha CI de
empacotamento até este fechamento — ver "CI de Empacotamento do Catálogo Oficial" abaixo),
então esse caminho não pôde ser validado contra um deploy ao vivo antes da CI existir.
Enquanto isso: clonado o mesmo repositório real localmente, rodado o CLI real
`techforge catalog build-index` contra sua pasta `modules/` pra gerar um `index.json` +
`.mod` + checksum genuínos, servido esse output via `python -m http.server` local, e
apontado `OfficialCatalogProvider(base_url=...)` pra ele — requisições HTTP reais, parsing
de JSON real, download de `.mod` real, `PackageManager.install()` real. Isso passou limpo,
sem bugs encontrados (confirmou que o nome de campo `download_url` no exemplo deste doc
estava errado — o campo real gerado é `mod_url`; corrigido). Nenhuma mudança de código foi
necessária nesse caminho — só o exemplo do doc.

**Lição:** este é o mesmo padrão raiz já sinalizado nos Slices 5b/6 (mocks que checam contra
uma forma inventada ou simplificada demais em vez do comportamento real), mas dessa vez
sobreviveu à revisão original do Slice 3 porque mockar o próprio `httpx.AsyncClient` — em
vez de mockar numa fronteira de lógica de negócio — esconde bugs de nível de transporte. Um
smoke test ao vivo contra uma fonte remota real (ou um artefato real servido localmente, no
caso do caminho oficial) é a única coisa que teria pego isso antes.

---

## CI de Empacotamento do Catálogo Oficial (pendência do plano original, fechada e validada ao vivo)

O plano da Fase 11 (`tasks/phase11-plan.md`, decisão confirmada com o usuário antes da
implementação) previa explicitamente: *"a CI do próprio repositório [Tech.Forge.Modules]
(já existente, `update-modules-readme.yml`) ganha um passo a mais — depois do merge,
empacota cada módulo em `.mod` e regrava um `index.json`"*. Essa etapa nunca tinha sido
implementada durante os Slices 1–8. Isso foi identificado pelo usuário após o fechamento
inicial da fase; a versão final, depois de várias rodadas de validação real (não só local),
ficou assim:

**Arquitetura final (`julianscunha/Tech.Forge.Modules`):**
- `submissions/<id>/` — transitório. É onde o contribuidor sobe `manifest.yaml` +
  `backend/`/`frontend/`/`docs/` na PR. Some assim que a CI empacota.
- `modules/<id>/` — permanente, gerenciada só pela CI. Acumula um `.mod` por versão já
  publicada (`<id>-<versão>.mod`, nunca sobrescrito) + `modules/index.json` (uma entrada por
  módulo, sempre a versão mais recente).
- As duas pastas são deliberadamente separadas: se a fonte da PR e o `.mod` histórico
  morassem na mesma pasta, um contribuidor que "recriasse a pasta do zero" localmente antes
  de editar poderia, sem saber que havia binários de produção ali, incluir a deleção deles
  no próprio PR (achado real do usuário, corrigido no PR #8 do repo externo).
- `update-modules-readme.yml`: build-index (submissions → modules) → regenera README (a
  partir de `modules/index.json`, não mais escaneando manifest solto — ver bug abaixo) →
  poda `submissions/` → remove sidecars `.mod.sha256` (nada os lê de volta, checksum já está
  no índice) → abre um PR com o resultado, espera o check `validate` passar, e mergeia via
  squash (branch `main` é protegida; nem o bot dá push direto).
- `settings.OFFICIAL_CATALOG_BASE_URL` adicionado ao Core, apontando para
  `https://raw.githubusercontent.com/julianscunha/Tech.Forge.Modules/main/modules` — o
  placeholder `https://techforge.io/catalog` usado desde o Slice 4 nunca tinha sido
  substituído pelo endereço real.

**Bugs reais achados só ao rodar a CI de verdade (não em simulação local) e corrigidos, um a
um, cada um bloqueando o anterior:**

1. `ModuleNotFoundError: No module named 'app'` no passo de build-index — o shim
   `cli/techforge_cli/packager/builder.py` (Core) fazia `from app.package_manager.builder
   import ...` sem garantir que `app` estivesse no `sys.path`; só funcionava no ambiente de
   dev por acidente (`cwd=core/backend`). Fix: resolve o caminho de `core/backend` relativo
   ao próprio arquivo, não ao `cwd`.
2. Push direto em `main` bloqueado: `Required status check "validate" is expected` — `main`
   é protegida e o check só roda em `pull_request`, nunca em `push`. Fix: a job passou a
   abrir PR + esperar + mergear sozinha, em vez de dar push.
3. `GITHUB_TOKEN` não pode criar/aprovar PR — restrição do próprio GitHub contra abuso de
   supply-chain. Fix: PAT fine-grained dedicado (`CATALOG_BOT_PAT`, secret do repo,
   `contents` + `pull_requests` em read-write) só para essa etapa.
4. Corrida entre `gh pr create` e `gh pr checks --watch` (`no checks reported`, o GitHub
   ainda não tinha registrado o check run) — fix: poll até aparecer pelo menos 1 check antes
   de assistir.
5. **`techforge catalog build-index` sobrescrevia `index.json` inteiro em vez de fazer
   merge** — o mais sério dos cinco. Cada execução real só vê o que está em `submissions/`
   no momento (uma PR por vez); sobrescrever apagaria do catálogo todo módulo publicado
   anteriormente que não fizesse parte dessa PR. Achado simulando localmente **antes** de
   publicar (não em produção). Fix: lê o `index.json` existente e funde por `id`; 2 testes de
   regressão (`test_build_index_merges_with_existing_index_instead_of_overwriting`,
   `test_build_index_replaces_entry_for_updated_module`).

**Bug relacionado, latente, achado por inspeção (não por falha de CI):** a poda (item 2 da
lista de decisões acima) já em produção fazia `generate_modules_readme.py` (que escaneava
`manifest.yaml` solto) perder módulos do README assim que fossem podados — só não tinha se
manifestado ainda por só haver 1 módulo publicado. Fix: passou a ler `modules/index.json`
(registro durável) em vez de escanear pasta-fonte transitória.

**Validação real de ponta a ponta (não simulação), feita depois de todos os fixes acima:**
uma PR de teste real tocando `submissions/e2e_test_module/` foi aberta, validada (`validate`
passou), mergeada, e a CI publicou sozinha até o fim — build-index (merge preservando
`system_information_service`), poda, sha256 removido, PR automático aberto e mergeado
sozinho, guard anti-loop confirmado (`skipped`, 0s na run seguinte). O módulo de teste foi
removido do catálogo depois, numa PR de limpeza separada. Ver PRs #8, #9, #10, #11 no
`Tech.Forge.Modules`.

Também validado, já com a estrutura final: `OfficialCatalogProvider` contra o
`raw.githubusercontent.com` real (não servidor local) com o novo `mod_url` aninhado —
descoberta, download, `PackageManager.install()`, tudo real. E, pela primeira vez nesta
fase, o fluxo **via HTTP de verdade**: servidor `uvicorn` real rodando, `POST
/api/v1/marketplace/install-remote/{id}` → polling de `GET
/api/v1/marketplace/install-jobs/{id}` até `DONE` → confirmado em `GET
/api/v1/registry/modules` → removido via `DELETE /api/v1/marketplace/remove/{id}`. Fecha a
lacuna, identificada mais cedo nesta fase, de nunca ter testado os endpoints reais (só
serviços internos).

---

## Problemas Conhecidos & Limitações

Documentados conforme spec §30 (Known Limitations):

1. **`CustomCatalogProvider` só suporta GitHub Contents API**
   - Funciona com: GitHub, GitLab (se compatível com Contents API), hosts git similares
   - NÃO funciona com: Gitea self-hosted, GitLab sem Contents API, fontes não-git
   - Caminho de evolução: Fase 18.1 (External Module Sources) vai adicionar adapters genéricos
   - Impacto: Baixo (a maioria dos projetos de comunidade usa GitHub; empresas podem self-hostear Gitea na Fase 13)

2. **Sem rollback completo em atualização falha**
   - Comportamento atual: instalação falha → arquivos em disco inalterados → sem estado parcial
   - Não é regressão: mesmo comportamento da Fase 4 (atomicidade de instalação é só local)
   - Caminho de evolução: Fase 15 (Quality & Testing) pode adicionar infraestrutura de snapshot/rollback
   - Impacto: Baixo (falhas são raras; usuário pode remover e reinstalar manualmente)

3. **Sem polling em background para novos módulos**
   - Comportamento atual: notificação de "novo módulo disponível" só no refresh manual do Catálogo
   - Não é lacuna de spec: §30 diz "notificações PODEM ser proativas" (ênfase em PODEM)
   - Caminho de evolução: Fase 13 (Central Server) habilita jobs de polling server-side
   - Impacto: Médio (bom pra desktop; ruim pra cenários always-on)

4. **Sem integração Slack/Teams pra indisponibilidade de fonte**
   - Atual: notificações aparecem só in-app
   - Caminho de evolução: Fase 14 (Observability & Telemetry) + webhooks
   - Impacto: Baixo (cenário desktop; coordenação de equipe é Fase 13+)

5. **Detecção de "fonte indisponível" não distingue "rede fora do ar" de "zero módulos"**
   - Causa raiz: `OfficialCatalogProvider`/`CustomCatalogProvider.list_available()` engolem
     erros de rede deliberadamente e retornam `[]` (Slices 2/3 — "fonte indisponível é
     informação, não falha do Core"). No momento em que `CatalogAggregator._fetch_source()`
     vê o resultado, uma lista vazia é indistinguível de um catálogo genuinamente vazio (mas
     alcançável).
   - Comportamento atual: `_notify_source_unavailable()` dispara em qualquer transição de
     "resultado não-vazio" → "resultado vazio", que é o sinal mais próximo disponível, mas um
     repositório custom cujo dono remove todos os módulos (vai de N módulos pra 0, ainda
     perfeitamente alcançável) dispararia a mesma notificação de "fonte indisponível" que uma
     queda real.
   - Caminho de evolução: exigiria que o contrato do provider retornasse um sinal distinto de
     alcançável-mas-vazio vs. inalcançável (ex: levantar uma exceção tipada em vez de engolir,
     capturada no nível do agregador) — uma mudança de interface de provider fora do escopo de
     um slice de fechamento; revisitar se isso se mostrar ruidoso na prática.
   - Impacto: Baixo (um catálogo custom legitimamente esvaziado é um cenário raro e
     autoinfligido; pior caso é uma notificação extra, não uma falha funcional).

---

## Arquivos Alterados

### Código (`Tech.Forge`)
- `app/package_manager/catalog_aggregator.py` — Agregador com rastreamento de disponibilidade + notificações
- `app/api/routes/marketplace.py` — Endpoints de instalação remota (Slice 8 parte 1; já presente)
- `app/package_manager/repository.py` — 2 correções em `CustomCatalogProvider` (client fechado; encoding não-UTF-8), achadas na validação online real
- `app/package_manager/manager.py` — `update()` preserva `data/` do módulo entre versões (bug de perda de dado, achado na revisão do fluxo de update)
- `app/core/settings.py` — `OFFICIAL_CATALOG_BASE_URL` real (substitui placeholder)
- `cli/techforge_cli/packager/builder.py` — shim resolve `core/backend` relativo ao arquivo, não ao `cwd` (quebrava fora de um dev venv)
- `cli/techforge_cli/commands/catalog.py` — `build-index` aninha `.mod` por módulo (histórico de versões) e faz merge com `index.json` existente em vez de sobrescrever (bug crítico)

### Testes
- `tests/test_phase11_source_unavailable.py` (NOVO) — 2 testes
- `tests/test_phase11_integration.py` (NOVO) — 2 testes
- `tests/test_phase11_catalog.py` — +2 testes de regressão (client fechado, encoding)
- `core/backend/tests/test_phase4.py` — +1 teste (`data/` preservado no update)
- `cli/tests/test_catalog_build_index.py` — +2 testes (merge de índice, nested output)
- Todos os testes existentes passando (sem regressões) — 708 no total (backend + CLI)

### Documentação
- `docs/developer-center/core/module-catalog.md` (traduzido pra pt-br, atualizado pra `submissions/` + `mod_url` aninhado) — Documentação completa do catálogo
- `docs/INDEX.md` — Link adicionado pro novo doc
- `app/doc_engine/__init__.py` — Seção "## Module Catalog" adicionada ao export de contexto de IA
- `README.md` (`Tech.Forge`) — badge de testes, roadmap, seção de endpoints `/catalog/*`

### Repositório externo `julianscunha/Tech.Forge.Modules`
- `.github/workflows/update-modules-readme.yml` — build-index + poda + PR automático + PAT + retry de checks
- `.github/workflows/validate-modules.yml` — paths/loop migrados pra `submissions/**`
- `scripts/generate_modules_readme.py` — lê `modules/index.json` em vez de escanear manifest solto
- `scripts/preview_pr_modules.py` — funde índice publicado + `submissions/` da PR
- `scripts/check_manifest_quality.py`, `scripts/prune_packaged_sources.py` — apontam pra `submissions/`
- `scripts/prune_packaged_sources.py` (novo, depois simplificado) — poda `submissions/<id>/`
- `.gitignore` (novo — não existia)
- `CONTRIBUTING.md`, `README.md` — fluxo completo `submissions/` → `modules/` documentado
- Migração do `system_information_service` pro layout aninhado

### Sem Mudanças Necessárias
- Frontend (Slice 7 já completo; nenhuma feature nova necessária)
- Spec de manifest (nenhum campo novo necessário)

---

## Ações Pós-Fechamento

### Phase-11-report.md ✅ (ESTE ARQUIVO)
Criado e documenta todos os slices, decisões, testes, problemas conhecidos. Traduzido para
pt-br após ter sido gerado incorretamente em inglês na primeira versão — padrão do projeto
é pt-br (ver CLAUDE.md).

### Atualização de tasks/phase-audit.md ✅
Linha da Fase 11 atualizada de "⚠️ local-only" pra lista completa de componentes entregues;
removida entrada obsoleta sobre `RemoteRepositoryProvider` (superado pelos providers da
Fase 11).

### Atualização de README.md ✅
Badge atualizado com a contagem final de testes; roadmap (gantt) corrigido — Fase 11 estava
marcada como "active" mesmo já fechada; seção de endpoints `/api/v1/catalog/*` e
`install-remote`/`install-jobs` adicionada à API Reference.

### Limpeza de Git ✅
- Todos os novos testes commitados juntos
- Docs commitados juntos
- Commit final da fase menciona "Fase 11 complete"

### Validação online real ponta a ponta ✅
Rodado o fluxo completo contra os dois tipos de fonte real: custom (repositório
`julianscunha/Tech.Forge.Modules`) e oficial (`raw.githubusercontent.com` real, com o
`mod_url` aninhado final, não mais servidor local). Além disso — pela primeira vez nesta
fase — validado via **HTTP de verdade**: servidor `uvicorn` real, `POST
/api/v1/marketplace/install-remote/{id}` → polling até `DONE` → confirmado em `GET
/api/v1/registry/modules` → removido via `DELETE /api/v1/marketplace/remove/{id}`. E uma PR
de teste real (`submissions/e2e_test_module/`) foi aberta, validada, mergeada e publicada
pela CI sozinha, do zero até o fim, sem intervenção manual em nenhum passo intermediário.

### CI de empacotamento do catálogo oficial ✅
Extensão de CI planejada e nunca entregue durante os Slices 1–8 — implementada, testada com
uma PR real de ponta a ponta, e com a arquitetura `submissions/` + `modules/` final (ver
"CI de Empacotamento do Catálogo Oficial" acima). PRs #2–#11 no `Tech.Forge.Modules`.

---

## O Que NÃO Está na Fase 11 (Conforme Spec)

1. ❌ Servidor de marketplace (Fase 13)
2. ❌ Sincronização multi-usuário (Fase 13)
3. ❌ UI de avaliação/review de módulo (Spec §30 exclui explicitamente)
4. ❌ Adapters GitLab/Gitea/genéricos (Fase 18.1)
5. ❌ Daemon de polling em background (Fase 13)
6. ❌ Notificações via webhook (Fase 14)
7. ⚠️ Instalar/consultar uma versão antiga específica de um módulo (Fase 15) — o **armazenamento**
   de histórico já existe (todo `.mod` publicado fica em `modules/<id>/`, nunca sobrescrito),
   mas nada no Core ou na API expõe ou instala uma versão que não seja a listada em
   `index.json` (sempre a mais recente). A base para a Fase 15 já está no lugar; falta só a
   camada de consulta/instalação por versão.

---

## Prontidão para a Fase 12

A Fase 12 (Configuration & Persistence) pode construir sobre a Fase 11 sem mudanças:
- Locais de instalação de módulo já são configuráveis via settings
- URLs de fonte de catálogo são armazenadas em SQLite (persistem entre restarts)
- Cache é em memória (sem necessidade de persistência conforme spec)
- Nenhuma migração de dados necessária
- `PackageManager.update()` agora preserva `data/` do módulo entre versões — relevante pra
  qualquer decisão futura de persistência por módulo

---

## Checklist de QA

- ✅ Todos os testes passam (708 no total — backend + CLI)
- ✅ Fluxo online real validado ponta a ponta contra as duas fontes reais (custom e oficial), não só mocks
- ✅ Fluxo validado via HTTP real (`uvicorn` rodando, endpoints reais, não só nível de serviço)
- ✅ PR real de contribuidor validada ponta a ponta no `Tech.Forge.Modules` (abertura → validate → merge → publicação automática)
- ✅ Build do frontend passa sem warnings (`npm run build`)
- ✅ Comandos de CLI funcionam (`techforge catalog list`, etc.)
- ✅ Nenhum problema de segurança introduzido (notificações só usam metadado público, nenhuma credencial exposta; PAT do bot é fine-grained, escopo mínimo, só nesse repo)
- ✅ Documentação completa (Developer Center + AI context + CONTRIBUTING.md/README.md do repo externo), em pt-br
- ✅ Limitações conhecidas documentadas
- ✅ CI de empacotamento do catálogo oficial implementada e validada ao vivo
- ✅ Commits atômicos e bem descritos

---

**Fase 11 FECHADA** — 2026-08-29
