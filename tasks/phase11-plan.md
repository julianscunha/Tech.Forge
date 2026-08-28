# Plano — Fase 11: Module Marketplace & Distribution

> Spec: docs/phases/11-Fase-11-Module-Marketplace-Distribution.md
> Pré-requisito: Fase 10 (Security, Integrity & Module Trust) ✅ fechada.

## Premissas validadas (investigação de código real)

1. ✅ `RepositoryProvider` (ABC) já é praticamente o `CatalogProvider` da
   spec (§7) — `list_available/get_package/fetch_mod_path` cobrem
   `list_modules/get_module/download_package`. Estender a interface
   existente, não criar uma nova.
2. ✅ `RemoteRepositoryProvider` é stub puro — 3× `NotImplementedError`
   (`package_manager/repository.py:157-170`). Esta fase o implementa.
3. ✅ Só existem dois pontos de entrada de instalação hoje, os dois em
   `routes/marketplace.py`: `POST /install/{id}` (via
   `LocalRepositoryProvider.fetch_mod_path`) e `POST /import` (upload
   manual). Ambos convergem em `package_manager.install(mod_path: Path)`
   — único ponto real de instalação, sempre espera um `.mod` físico.
4. ✅ `PackageInfo` (`package_manager/models.py`) já cobre ~80% do
   `CatalogModule` da spec (§16): id, name, version, category, publisher,
   compatibility, trust_level, checksum. Faltam apenas: origem
   (`source`) e URL de onde veio. Não tem lista de versões — fora de
   escopo (spec permite "preparar arquitetura", não implementar
   histórico completo agora — ver §30 e decisão abaixo).
5. ✅ Categorias já são 100% dinâmicas — lidas do `category` do manifest
   via registry in-memory (confirmado nesta conversa). Critério de
   aceite §7 da spec já está coberto, nenhum código novo necessário.
6. ✅ `ModuleDetailPanel.tsx`/`ModulesPage.tsx` já têm o padrão de trust
   badge (Fase 10) e seções condicionais — Catálogo reusa os mesmos
   componentes, não recria exibição de trust.
7. ✅ `.mod` é sempre um zip lido via `zipfile.ZipFile` — nenhum reader
   remoto/range-aware existe nem será necessário (decisão abaixo).

## Decisões arquiteturais (confirmadas com o usuário antes do plano)

Resumo da discussão: o Marketplace **nunca** baixa um `.mod` inteiro só
para inventariar. Ele lê apenas metadado leve; baixar/montar o `.mod`
completo só acontece quando o usuário efetivamente clica "instalar".

1. **Duas fontes remotas, dois mecanismos de leitura, um único
   destino:**
   - **Catálogo oficial** (`Tech.Forge.Modules`, controlado por nós):
     a CI do próprio repositório (já existente, `update-modules-readme.yml`)
     ganha um passo a mais — depois do merge, empacota cada módulo em
     `.mod` e regrava um `index.json` na raiz (metadado de todo o
     catálogo). O Marketplace faz **1 fetch** de `index.json` — custo
     constante, independe do tamanho do catálogo. Contribuidor não
     muda nada no fluxo dele (continua enviando pasta solta na PR).
   - **URL custom** (repositório de terceiro, sem automação nossa):
     nenhuma automação exigida do dono. O Marketplace lista o diretório
     `modules/` via API do host (GitHub Contents API) e lê o
     `manifest.yaml` de cada módulo diretamente — N chamadas pequenas,
     sem zip, sem clone. Convenção documentada (`modules/<id>/manifest.yaml`),
     a mesma que `Tech.Forge.Modules` já usa.
   - **Instalação, nos dois casos**: o `.mod` final (pronto no índice
     oficial, ou montado on-demand a partir dos arquivos do módulo pra
     fonte custom) é entregue ao `package_manager.install()` já
     existente — **zero caminho de instalação novo**. `PackageManager`
     não precisa ser dividido em acquire/shared: a origem remota já
     entrega um `.mod`, como sempre.
2. **`.mod` continua reservado para**: upload manual/comunidade
   (inalterado) e como formato final de entrega do catálogo oficial —
   nunca é o formato de edição/PR (isso continua sendo pasta solta,
   revisável no GitHub).
3. **Sem versionamento completo (`CatalogModule.versions`) nesta fase**:
   `PackageInfo.version` (disponível) + `installed_version` (instalado)
   já cobrem `UPDATE_AVAILABLE` (§13, reusa `PackageInfo.has_update`
   existente). Histórico de múltiplas versões/rollback fica só como
   ponto de extensão documentado (§15/§30 da spec permitem isso
   explicitamente — "preparar arquitetura", não implementar agora).
4. **Nome interno**: mantém `marketplace`/`MarketplacePage` no código
   (rotas, módulos, providers) — a spec só pede que a **UI não sugira
   comércio** (§8: "Catálogo de Módulos" em vez de "Marketplace" como
   rótulo visível). Renomear símbolos internos seria só custo de
   diff sem ganho — ajusta-se o texto exibido, não a arquitetura.
5. **Prioridade de fontes (§19)**: ordem fixa e explícita —
   `Internal (local repository/) > Official Catalog > Custom Catalog(s)`.
   Mesmo `module_id` em mais de uma fonte = conflito exibido (§20), não
   substituição silenciosa.

## Novo pacote / arquivos

```
core/backend/app/package_manager/
  catalog_source.py    # CatalogSource enum (LOCAL/OFFICIAL/CUSTOM) + CatalogSourceConfig
  repository.py         # + OfficialCatalogProvider (index.json), CustomCatalogProvider (manifest per-folder)
                         # RemoteRepositoryProvider (stub) removido, substituído pelos dois acima
  models.py              # PackageInfo.source: CatalogSource, PackageInfo.source_url: Optional[str]
  conflicts.py           # detect_conflicts(list[PackageInfo]) -> lista de module_id em >1 fonte
app/models/catalog_source.py   # tabela SQLite p/ fontes custom configuradas pelo usuário (persistente)
app/services/catalog_source.py # CRUD de fontes
app/models/catalog_favorite.py  # favorito local (module_id, source, added_at) — só desta instalação
app/api/routes/catalog.py      # GET /catalog/modules|modules/{id}|sources|updates|favorites
cli/techforge_cli/commands/catalog.py       # techforge catalog list/search/show/sources/build-index
```

## Slices

### Slice 1 — CatalogSource + extensão de PackageInfo (TDD)
- `CatalogSource` enum: `LOCAL` (repository/ hoje), `OFFICIAL_CATALOG`,
  `CUSTOM_CATALOG`.
- `PackageInfo.source: CatalogSource` (default `LOCAL`, preserva
  comportamento atual) + `PackageInfo.source_url: Optional[str]`.
- `conflicts.py::detect_conflicts(packages: list[PackageInfo]) -> dict[str, list[PackageInfo]]`
  — agrupa por `module_id`, retorna só os que aparecem em >1 fonte.

**Aceite:** `LocalRepositoryProvider` continua funcionando sem mudança
de comportamento (source=LOCAL implícito); `detect_conflicts` com dois
`PackageInfo` do mesmo `module_id` e fontes diferentes retorna o
conflito; com fontes iguais ou ids diferentes, não retorna nada.

### Slice 2 — Catálogo oficial: `index.json` (TDD) — §6/§7/§12
- `OfficialCatalogProvider(RepositoryProvider)`: `list_available()` faz
  1 HTTP GET no `index.json` remoto, parseia pra `list[PackageInfo]`
  (`source=OFFICIAL_CATALOG`). `get_package()` filtra em memória.
  `fetch_mod_path()` baixa o `.mod` específico apontado pelo índice
  pra `modules/cache/` (download único, sob demanda, só neste passo).
- Falha de rede/host indisponível → não derruba o Core, retorna lista
  vazia + status "fonte indisponível" (§17), nunca exceção não tratada.
- `cli/techforge_cli/commands/catalog.py::build_index` (lado
  gerador, roda no repositório de módulos, não no Core em runtime):
  varre `modules/*/manifest.yaml`, zipa cada pasta em `.mod`, escreve
  `index.json`. Reusado pelo workflow do `Tech.Forge.Modules` — não é
  uma feature do GitHub Actions, é um comando de CLI plugável em
  qualquer automação.

**Aceite:** `index.json` de teste (fixture local servida por
`httpx`/servidor de teste) → `list_available()` retorna os módulos
corretos; `fetch_mod_path()` baixa e cacheia; índice indisponível não
lança exceção; `build_index` sobre uma pasta de módulos de teste gera
`.mod`s + `index.json` corretos (round-trip: gerar → `list_available`
local lê certo).

### Slice 3 — Catálogo custom: leitura direta de manifest (TDD) — §3/§7
- `CustomCatalogProvider(RepositoryProvider)`: recebe uma URL de
  repositório git (GitHub). `list_available()` lista o diretório
  `modules/` via GitHub Contents API (1 chamada), depois lê
  `manifest.yaml` de cada subpasta (N chamadas pequenas) → `PackageInfo`
  (`source=CUSTOM_CATALOG`, sem checksum ainda — não existe `.mod`).
  `fetch_mod_path()` só é chamado no clique de instalar: baixa os
  arquivos do módulo específico (backend/frontend/docs + manifest) e
  monta um `.mod` local (zip) na hora — único lugar onde a fonte
  custom vira zip, e só acontece por ação explícita do usuário.
- Sem automação exigida do dono do repositório custom — documentar a
  convenção de pasta (igual à do `Tech.Forge.Modules`) como único
  requisito.

**Aceite:** repositório de teste (fixture local simulando a API do
GitHub) com 2-3 módulos → `list_available()` retorna metadado correto
sem baixar nenhum `.mod`; `fetch_mod_path()` de um módulo específico
produz um `.mod` válido que passa pelo `package_manager.install()` sem
diferença de tratamento vs. um `.mod` local.

### Slice 4 — Configuração de fontes + prioridade + conflitos + cache (TDD) — §18/§19/§20
- `app/models/catalog_source.py::CatalogSourceConfig` (SQLAlchemy):
  id, name, url, type (`OFFICIAL_CATALOG`/`CUSTOM_CATALOG`), enabled.
  Mesmo padrão de `app/models/publisher.py` (Fase 10).
- `app/services/catalog_source.py`: CRUD (add/list/remove/toggle) —
  **múltiplas fontes custom simultâneas, sem limite** (é uma lista, não
  um slot único); o catálogo oficial fica sempre habilitado por padrão
  e convive com quantas fontes custom o usuário cadastrar. Ordem de
  leitura fixa: `LOCAL → OFFICIAL_CATALOG → CUSTOM_CATALOG` (ordem de
  inserção entre múltiplos custom = ordem de cadastro).
- **Invalidação de cache no CRUD** (evita servir dado de uma fonte que
  já não existe/mudou): editar a URL de uma `CatalogSourceConfig`
  invalida o cache daquela fonte imediatamente (força fetch na próxima
  leitura, não espera o TTL); remover uma fonte apaga o cache dela na
  hora; adicionar uma fonte não tem cache prévio, busca normal na
  primeira leitura.
- Agregador `CatalogService.list_all_available(force_refresh: bool = False)`:
  consulta todas as fontes habilitadas em paralelo (`asyncio.gather`,
  cada uma isolada — uma fonte indisponível não derruba as outras),
  aplica `detect_conflicts` (Slice 1) e retorna módulos + conflitos
  separadamente.
- **Cache em memória, por fonte, com TTL (§18)** — nem "só no boot"
  (catálogo fica velho em instâncias de longa duração) nem "toda
  chamada" (o próprio problema de escala que motivou o índice único no
  catálogo oficial): guarda `list[PackageInfo]` + `fetched_at` por
  `CatalogSourceConfig.id`; uma leitura dentro do TTL (default 15 min,
  configurável) devolve o cache sem tocar rede; fora do TTL, refaz o
  fetch e renova o timestamp. `force_refresh=True` (botão "Atualizar"
  na UI, §18 "atualização manual") ignora o TTL. Instalar um módulo
  (`fetch_mod_path`) **nunca** passa pelo cache — sempre busca direto
  na fonte, só sob clique explícito do usuário.

**Aceite:** duas fontes custom cadastradas, uma delas indisponível
(mock levanta erro) → `list_all_available()` retorna os módulos da
fonte disponível normalmente + marca a indisponível como
"unavailable", não propaga exceção; mesmo `module_id` em duas fontes →
aparece em `conflicts`, não duplicado silenciosamente na lista
principal; duas chamadas seguidas dentro do TTL → provider mockado é
chamado só 1 vez (cache hit na segunda); `force_refresh=True` chama o
provider de novo mesmo dentro do TTL; após o TTL expirar (mock de
tempo), nova chamada sem `force_refresh` já busca de novo; editar a
URL de uma fonte cadastrada e ler de novo (mesmo dentro do TTL antigo)
retorna dado da URL nova, não do cache velho; remover uma fonte e
listar de novo não traz mais os módulos dela, mesmo que o TTL do
cache antigo ainda não tivesse expirado.

### Slice 4.5 — Favorito local (TDD)
- Sem número agregado, sem "N pessoas favoritaram" — é uma marca
  **pessoal, só desta instalação**, sem servidor central nem conta de
  usuário (não existe nenhum dos dois ainda — Fase 13). Resolve a
  necessidade sem prometer um "de 100 pessoas, 4,5 estrelas" que o
  sistema hoje não tem como sustentar de verdade (a spec da Fase 11
  também exclui avaliação pública/ranking no §30, explícito).
- `app/models/catalog_favorite.py::CatalogFavorite` (module_id,
  favorited_at) — tabela local simples, mesmo padrão de
  `CatalogSourceConfig`.
- `POST /catalog/favorites/{module_id}` / `DELETE /catalog/favorites/{module_id}`
  / `GET /catalog/favorites` (lista de ids). `GET /catalog/modules`
  ganha `favorite: bool` por item (Slice 5) e filtro `favorites_only`.

**Aceite:** favoritar um módulo e listar com `favorites_only=true`
retorna só ele; desfavoritar remove da lista; favorito sobrevive a
reiniciar o backend (é tabela SQLite, não estado em memória).

### Slice 5 — API `/catalog/*` com busca/filtro/paginação no servidor (TDD) — §27
Catálogo é o "coração do sistema" e precisa se comportar bem com
milhares de módulos — isso significa nunca mandar a lista inteira pro
frontend filtrar. Todo filtro/ordenação/paginação acontece no backend,
sobre o agregado já em cache (Slice 4) — sem motor de busca externo,
é só `filter`/`sorted`/slice de Python sobre uma lista que já está em
memória (nem em escala de milhares isso pesa: `index.json` é só
metadado, não o conteúdo do módulo).

- `GET /api/v1/catalog/modules` com query params:
  `search` (nome/descrição, case-insensitive), `category`, `source`
  (`local|official_catalog|custom_catalog`), `trust_level`,
  `compatible_only: bool`, `installed_only: bool`,
  `favorites_only: bool` (Slice 4.5),
  `sort: name|recent` (default `name`), `page` (default 1),
  `page_size` (default 24, máx 100). Resposta inclui `total`,
  `page`, `page_size` — paginação real, nunca "traz tudo e corta no
  frontend".
- `GET /api/v1/catalog/categories` — nome + contagem de cada categoria
  presente no agregado atual (barata: computada sobre o mesmo cache da
  Slice 4, sem tabela nova) — alimenta a sidebar sem precisar paginar
  por todos os módulos só pra montar o menu.
- `GET /catalog/modules/{id}`, `GET /catalog/sources` (status de cada
  fonte: disponível/indisponível), `GET /catalog/updates` (reusa
  `PackageInfo.has_update` já existente).
- `POST /catalog/sources` / `DELETE /catalog/sources/{id}` — CRUD de
  fontes custom (Slice 4) exposto via API.
- Instalação continua em `routes/marketplace.py::install_module` — só
  passa a aceitar instalar a partir de qualquer fonte (resolve o
  `PackageInfo`/`fetch_mod_path` pela fonte correta), nenhuma segunda
  implementação de Package Manager (§27 da spec, explícito).
- **Progresso de instalação remota (§11/§12)**: instalar de fonte
  oficial/custom tem uma etapa nova que a instalação local nunca teve
  — espera de rede. `fetch_mod_path()` de fontes remotas passa a
  reportar fase (reusa o formato de `ProgressPhase`/`ProgressReport`
  já criado em `module_runtime/execution.py`, Fase 9, aplicado aqui a
  instalação em vez de execução): `ACQUIRING → VALIDATING → INSTALLING → DONE|FAILED`.
  Estado do job guardado em memória (mesmo padrão do
  `ModuleRuntimeRegistry`), chave = id do job de instalação.
  `GET /catalog/install-jobs/{job_id}` — polling simples (sem
  WebSocket/SSE, consistente com o resto do projeto).
  Download/clone sempre em `cache/` (temp); só entra em
  `modules/installed/` depois de validado — falha de rede no meio
  nunca deixa módulo pela metade instalado (mesma garantia que o
  `.mod` local já tem hoje).
- Falha de conectividade → job `FAILED` com mensagem específica
  ("Falha ao baixar módulo: sem conexão com `<fonte>`"), nunca
  exceção não tratada nem job travado num estado intermediário para
  sempre. Sem retry automático — o usuário decide tentar de novo.

**Aceite:** fixture com >100 `PackageInfo` mockados — `page=2&page_size=24`
retorna exatamente os itens 25-48 e `total=100+`; `search=veeam` retorna
só os que batem; `category=Backup` + `trust_level=VERIFIED` combinados
funcionam como AND; `GET /catalog/categories` reflete contagem correta
por categoria; teste de integração — cadastra fonte custom (fixture),
`GET /catalog/modules` retorna módulo dela junto com os locais;
`POST /marketplace/install/{id}` de um módulo vindo de fonte custom
funciona ponta a ponta (monta `.mod`, valida, instala, aparece em
`/registry/modules`).

### Slice 6 — CLI `techforge catalog` (TDD) — §26
- `techforge catalog list|search <termo>|show <id>|sources` — leem a
  API `/catalog/*`.
- `techforge modules install <source>` / `update <module>` / `updates`
  — já existem como `marketplace` no CLI atual (confirmar nome real) ou
  precisam ser adicionados seguindo o mesmo padrão de
  `commands/module_trust.py` (Fase 10).
- `build_index` (Slice 2) já implementado — só documentar aqui como
  parte da família `catalog`.

**Aceite:** `techforge catalog list` contra backend de teste rodando
retorna os módulos das fontes habilitadas; `techforge catalog sources`
mostra status disponível/indisponível.

### Slice 7 — Frontend: Catálogo de Módulos, organizado para escala
- Renomear rótulo visível "Marketplace" → "Catálogo de Módulos" (§8) —
  só texto/label, sem mudar rotas/nomes internos (decisão acima).
- Layout de 3 zonas, pensado para milhares de módulos (nunca lista
  tudo de uma vez — sempre via os query params da Slice 5):
  - **`CategorySidebar`**: árvore de categorias com contagem
    (`GET /catalog/categories`), seleção única + "Todas". Reusa
    categorias já dinâmicas — sem menu hardcoded.
  - **`FilterBar`**: busca com debounce, filtros por fonte (Local/
    Oficial/Custom), por trust level (reusa `TrustBadge` da Fase 10
    como chip clicável), toggle "somente compatíveis", toggle "somente
    instalados/com atualização", ordenação (nome/recente). Cada filtro
    altera os query params de `GET /catalog/modules` — o servidor
    filtra, o frontend só exibe a página atual. Inclui toggle
    "Favoritos" (Slice 4.5).
  - **Grid de cards** (`CatalogCard`): ícone, nome, categoria, versão
    (`tabular-nums`), `TrustBadge`, badge de fonte, descrição curta,
    estrela de favorito clicável (ação pessoal instantânea, fica no
    card — diferente do autor, que é informação de detalhe),
    ação (Instalar/Atualizar/Instalado). Quando o `module_id` está em
    `conflicts` (Slice 4), mostra chip "Disponível em N fontes" —
    usuário escolhe qual instalar, nunca é escolhido por ele. Card
    fica leve de propósito (escala) — sem autor/publisher aqui.
  - **Detalhe do módulo** (clique no card abre painel, reusa
    `ModuleDetailPanel` — Fase 10): aqui sim exibe `author` do
    manifest + `publisher` **resolvido pelo nome** (não o id cru —
    reusa `app/services/publisher.py`) junto do trust badge já
    existente.
  - **Rodapé de paginação**: `total` formatado, seletor de itens por
    página, navegação prev/next + números — nunca infinite-scroll sem
    controle (perder a posição em milhares de itens é pior UX que
    paginação explícita).
- `SourceStatus` (badge disponível/indisponível por fonte) na
  `FilterBar` ou em painel de fontes.
- **`InstallDialog`** (§28, remoto): ao clicar "Instalar" numa fonte
  oficial/custom, abre com a fase atual (`Baixando… / Validando… /
  Instalando…`), fazendo polling em `GET /catalog/install-jobs/{job_id}`.
  Em `FAILED`, mostra a mensagem de erro + botão "Tentar novamente"
  (não fecha sozinho, não retenta sozinho). Instalação local
  (`.mod` já em disco) continua síncrona, sem diálogo de progresso —
  não há espera de rede a esconder.
- Tela de gerenciar fontes custom (adicionar/remover URL) — formulário
  simples, sem duplicar validação (erros de URL inválida/indisponível
  vêm do backend).
- Reusar `TrustBadge`/`ModuleDetailPanel` (Fase 10) sem recriar exibição
  de trust.

**Aceite:** rodar `npm run build` sem warnings; testar manualmente com
fixture de >100 módulos: navegar páginas, filtrar por categoria +
trust + fonte combinados, ver contagem e paginação corretas, ver
conflito exibido quando presente, cadastrar fonte custom nova pela UI,
instalar módulo de fonte custom com sucesso.

### Slice 8 — Notificações, Developer Center, AI Context, integração final
- Notificações (§23, reusa `NotificationService` da Fase 2, mesmo
  padrão de dedupe já usado nas Fases 8.1/10): "novo módulo disponível",
  "update disponível", "instalação concluída/falhou", "fonte
  indisponível" (só ao alternar de disponível→indisponível, não a
  cada poll).
- `docs/developer-center/core/module-catalog.md`: formato do
  `index.json`, convenção de pasta pra fonte custom, como publicar no
  catálogo oficial, prioridade de fontes, `build_index`.
- `doc_engine` AI Context: seção "Module Catalog" com o formato oficial
  de distribuição (§25 da spec, explícito).
- Teste de integração completo (§29 da spec): descobre no catálogo →
  seleciona → valida → instala → aparece em Modules → ativa → aparece
  no Runtime. Rodar pra fonte oficial (fixture) e fonte custom
  (fixture).
- Fechar com `tasks/phase-11-report.md` + atualizar `tasks/phase-audit.md`
  (linha 20) + `README.md` (contagem de testes).

**Aceite:** suíte completa passando; build de frontend limpo; teste de
integração fim-a-fim citado acima passando para as duas fontes remotas.

## Known Issues esperados (documentar no report, não bloquear a fase)

- `CustomCatalogProvider` inicial só suporta hosts com API compatível
  com GitHub Contents API (GitHub, e serviços que a espelham). GitLab/
  self-hosted genérico fica como extensão futura — documentado, não
  implementado nesta fase (spec §3 permite explicitamente: "não
  implementar todas as fontes agora").
- Sem rollback completo de update (§22 da spec aceita "rollback
  limitado" nesta fase) — mantém o padrão já usado pelo
  `install()`/`update()` atual (falha = não aplica, não desfaz parcial).
