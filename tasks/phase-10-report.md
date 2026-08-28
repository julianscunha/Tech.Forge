# Phase 10 Report — Security, Integrity & Module Trust

## Slice 1 — Integrity Manifest (hash por-arquivo)
- `app/module_trust/integrity.py`: `generate_integrity_manifest()` (SHA-256
  por arquivo, exclui `data/`, `__pycache__`, `.pyc`, `integrity.json`
  em si), `write_integrity_manifest()`, `verify_integrity()` com os 5
  estados da spec (VALID/MODIFIED/MISSING_FILE/UNEXPECTED_FILE/
  INVALID_MANIFEST — prioridade documentada quando há múltiplos
  problemas: INVALID_MANIFEST > MISSING_FILE > MODIFIED >
  UNEXPECTED_FILE > VALID).
- Diferente do checksum de `.mod` inteiro já existente desde a Fase 4
  (identidade do pacote no repositório) — este é por-arquivo, dos
  arquivos já instalados em disco (Fase 10 §5/§6).
- `PackageManager.install()` grava `integrity.json` logo após extrair o
  pacote.

## Slice 2 — Publisher model + Registry (SQLite)
- `app/models/publisher.py::Publisher` — tabela SQLite nova
  (`publishers`), não arquivo, consistente com o padrão 100%
  SQLite-first do projeto (decisão do usuário, diverge da sugestão
  literal da spec de `core/config/publishers/`).
- `app/module_trust/publisher.py::PublisherType`
  (OFFICIAL/INTERNAL/THIRD_PARTY/LOCAL_DEVELOPMENT) e
  `PublisherTrustStatus` (TRUSTED/UNTRUSTED/REVOKED — status
  administrativo do publisher, distinto do `TrustLevel` de um módulo).
- `PublisherService` (register idempotente, get_by_id, set_trust_status,
  revoke) + `GET /api/v1/publishers`, `/publishers/{id}` (somente
  leitura nesta fase — registro é interno/CLI).

## Slice 3 — TrustResolver (5 estados de TrustLevel)
- `app/module_trust/trust.py::TrustLevel` (TRUSTED/VERIFIED/UNVERIFIED/
  MODIFIED/INVALID) **substitui** o `TrustLevel` antigo de
  `package_manager/enums.py` (Fase 4, minúsculo — `verified/community/
  unsigned/untrusted` — nunca calculado de verdade, sempre hardcoded
  `UNSIGNED`). Decisão do usuário: um só conceito de trust level no
  projeto, não dois coexistindo.
- `TrustResolver.resolve(integrity_status, publisher, signature_status)`
  combina as três dimensões. `UNEXPECTED_FILE` mapeado pra `MODIFIED`
  (decisão de implementação: arquivo não declarado também conta como
  alteração de conteúdo).
- Frontend: `TrustBadge.tsx`/`types/index.ts` (Marketplace) migrados
  pros novos valores — o badge de trust do Marketplace usava os
  valores antigos e teria quebrado silenciosamente.

## Slice 4 — SignatureProvider (abstração, sem Ed25519 real)
- `app/module_trust/signature.py::SignatureStatus`
  (NOT_CONFIGURED/VALID/INVALID/UNSUPPORTED), `SignatureProvider`
  (ABC: `sign()`/`verify()`/`identify_algorithm()`) desacoplado do
  Package Manager (spec §11), `NoOpSignatureProvider` default — nunca
  finge validar uma assinatura que não pode verificar.
- Decisão do usuário: só a abstração nesta fase — sem par de chaves
  real, sem fluxo de assinatura ponta a ponta. Consequência direta:
  `TRUSTED` ("publisher conhecido **e** assinatura válida") fica
  estruturalmente inalcançável nesta fase.

## Slice 5 — Verification Pipeline (no Module Validator) + Provenance
- **Revisão de desenho feita durante a própria slice**: descartada a
  ideia original de uma classe `PackageVerifier` separada — seria uma
  abstração paralela redundante com o `ModuleCLIValidator`, que desde a
  Fase 3 já É o pipeline consolidado. Os checks entram direto nele
  (`_check_integrity`/`_check_signature`/`_check_trust`), mesmo padrão
  de `_check_dependency_governance` (Fase 8.1).
- Integridade só é avaliada (e só bloqueia) quando `integrity.json` já
  existe — diretório-fonte ainda não instalado não tem esse arquivo, e
  isso é esperado (`warning`, não `error`). Assinatura ausente nunca
  bloqueia. Trust Level só roda com integridade avaliada; publisher
  sempre `None` neste validador síncrono (sem sessão de banco) —
  resolução completa com publisher real fica pra `GET
  /modules/{id}/trust` (Slice 7), documentado como limitação conhecida.
- `app/module_trust/provenance.py::InstallSource`
  (LOCAL_FILE/LOCAL_DEVELOPMENT/INTERNAL_CATALOG/REMOTE_CATALOG) fecha
  uma lacuna real: `ParsedManifest.source_type`/`source_location` (já
  existiam desde a Fase 4) nunca chegavam a `ModuleEntry` nem ao DB
  (`Module.source_type`/`source_location`, colunas que já existiam,
  sempre no default). Sem migração nova — só wiring.
- `PackageManager.install()` ganha o bloqueio real desta slice (§7):
  dependências estruturalmente inválidas (`DependencyValidator`, Fase
  8.1) passam a impedir a instalação — gap real que existia (a
  validação de dependência só rodava em `validate-module`/activate,
  nunca no `install()` em si).

## Slice 6 — Runtime Integrity Verification + Notifications
- `app/module_trust/verification.py::verify_module_integrity()`
  reverifica um módulo instalado sob demanda (startup, update, `POST
  .../verify` manual — nunca polling contínuo, §28). Notifica (dedupe,
  mesmo padrão já usado 2x no projeto) quando o resultado não é
  `VALID`; nunca bloqueia execução por padrão (§16).
- `POST /api/v1/modules/{id}/verify` (novo router
  `module_verification.py`). Wiring no startup: todo módulo `INSTALLED`
  é reverificado uma vez no boot.
- **Bug real encontrado e corrigido nesta slice**:
  `PackageManager.update()` nunca regravava `integrity.json` depois de
  trocar os arquivos do módulo — o arquivo da versão anterior ficava
  órfão e faria a próxima verificação reportar falso `MODIFIED` mesmo
  numa atualização legítima. Corrigido chamando
  `write_integrity_manifest()` também no `update()` (já acontecia só
  no `install()`).

## Slice 7 — API + CLI (integrity, trust, publishers)
- `GET /api/v1/modules/{id}/integrity` (leitura pura, sem notificar —
  diferente do `POST .../verify`, que notifica em mudança) e `GET
  /api/v1/modules/{id}/trust` (resolução **completa** de `TrustLevel`
  com Publisher real do banco — diferente do `ModuleCLIValidator`
  síncrono da Slice 5).
- CLI: `techforge verify-module <id>`, `techforge integrity check
  <id>`, `techforge publishers list|show <id>` — mesmo padrão
  HTTP-only de `runtime.py`/`services.py`. `techforge
  sign-module`/`verify-signature` não implementados (sem assinatura
  real).
- **Achado durante a revisão manual desta slice**: o subagente que
  implementou tinha descartado o teste que provava a resolução real de
  trust com publisher do banco (`VERIFIED` via `PublisherService`),
  substituindo por um teste redundante mais fraco. Identificado,
  corrigido (a causa raiz era ordem de setup: `TestClient(app)` dispara
  o lifespan de startup que reescaneia o diretório real de módulos — o
  registro manual da entrada fake precisa acontecer *depois* que o
  client já abriu, senão o scan do boot sobrescreve a entrada fake) e
  restaurado com cobertura real.

## Slice 8 — Frontend + Developer Center + AI Context + regra final
- `GET /api/v1/modules/trust` — Trust Level de todo módulo `INSTALLED`
  numa só chamada (evita N+1 no frontend na lista de módulos, mesmo
  padrão já usado por completeness de documentação). Reusa
  `get_module_trust()` já existente, sem duplicar lógica.
- **Bug real encontrado e corrigido nesta slice**: `GET /modules/trust`
  colidia com a rota genérica `GET /modules/{module_id}` de
  `routes/modules.py`, registrada *antes* no `api/__init__.py` —
  `"trust"` era interpretado como `module_id`, sempre `404`. Corrigido
  reordenando o `include_router`: `module_verification_router` agora
  registra antes de `modules_router`.
- Frontend: `ModulesPage.tsx` busca o trust de todos os módulos numa
  chamada só (mesmo padrão de `completeness`), passa pra `ModuleCard`
  — `TrustBadge` (já existente, do Marketplace) reusado como indicador
  discreto ao lado do `ModuleStatusBadge` (§22). `ModuleDetailPanel`
  ganha seção "Trust & Integrity" (Publisher, Trust Level, Integridade,
  Assinatura — §21), mesmo padrão condicional de
  Dependências/Dependentes (Fase 8.1).
- `docs/developer-center/core/module-trust.md` (novo) + `docs/INDEX.md`
  atualizado. `AIContextExporter` ganha seção "Module Trust"
  (condicional, publisher só pelo ID declarado no manifest — sem
  lookup real no Publisher Registry, contexto síncrono sem sessão de
  banco, mesma limitação documentada no `ModuleCLIValidator`).
- Teste integrado completo (§29, tudo em `tmp_path`): instalar pacote
  real (`.mod` via `PackageManager`) → `integrity.json` gerado →
  `verify_integrity()` VALID → modificar arquivo →
  `verify_module_integrity()` MODIFIED → notificação (dedupe em
  chamada repetida). Casos de publisher desconhecido/revogado já têm
  cobertura dedicada exaustiva nas Slices 3 e 7 — não repetidos aqui.
- Validado no navegador real (Playwright headless): badge "Invalid" na
  lista de módulos (honesto — `hello_world`/`veeam_m365` nunca
  passaram pelo `install()` real, não têm `integrity.json`), seção
  "Trust & Integrity" completa no detalhe, zero erros de console.

## Decisões arquiteturais (confirmadas com o usuário antes do plano)
1. Publisher Registry: tabela SQLite nova, não arquivo.
2. Assinatura Ed25519: só a abstração `SignatureProvider`, sem
   implementação real.
3. Granularidade do hash: por-arquivo (`integrity.json`), coexistindo
   com o checksum de `.mod` inteiro já existente (propósitos
   diferentes).
4. `TrustLevel`: substituído pelos valores da spec, um só conceito.

## Decisões de implementação (não perguntadas, resolvidas durante as slices)
- `UNEXPECTED_FILE` mapeado pra `TrustLevel.MODIFIED` (Slice 3).
- `POST /modules/{id}/verify` chama `health_check`-equivalente
  (`verify_module_integrity`), não um "initialize" — a spec usa a
  palavra de forma ambígua, mas reverificar integridade é exatamente o
  que esse endpoint faz.
- Descartada a classe `PackageVerifier` separada do plano original —
  os checks entram direto no `ModuleCLIValidator` já existente (Slice 5).
- Publisher sempre `None` nos contextos síncronos sem sessão de banco
  (`ModuleCLIValidator`, `AIContextExporter`) — resolução completa fica
  restrita à API assíncrona (`GET /modules/{id}/trust`).

## Tests
503 passed, 3 skipped (suíte completa `core/backend/tests`) + 83 CLI
(`cli/tests`). Arquivo novo: `test_phase10_module_trust.py` (73 casos
cobrindo as 8 slices + o teste integrado final); `test_phase7_ai_context.py`
ganhou 1 caso para "Module Trust"; `test_phase10_module_trust_cli.py`
(novo, CLI) 4 casos.

## Backend / Frontend / API / Database
Tabela nova: `publishers`. Nenhuma migração de coluna nova — as colunas
`Module.source_type`/`source_location`/`signature`/`checksum` já
existiam desde a Fase 4, ficavam sempre no default por falta de
wiring. Frontend: `npm run build` limpo (`tsc -b && vite build`),
nenhuma dependência nova.

## Build
`npm run build` ✅. `npm run lint` continua não rodando neste ambiente
— mesmo problema pré-existente já documentado nos relatórios das Fases
8, 8.1 e 9 (`eslint` ausente como devDependency), não introduzido por
esta fase.

## Known Issues
- `TRUSTED` é estruturalmente inalcançável nesta fase — sem assinatura
  real, nenhum módulo pode satisfazer "publisher confiável **e**
  assinatura válida". Esperado, não um bug; fica pra quando houver
  implementação real de assinatura.
- `techforge sign-module`/`verify-signature` não existem — dependem de
  `SignatureProvider` real.
- Quarentena física de pacotes (mover pra diretório separado) não
  implementada — a spec marca como opcional, sem caso de uso real
  ainda (o bloqueio de instalação, já implementado, cobre o cenário
  prático de "não instalar pacote com falha grave").
- `BLOCKED`/Trust Level não são recalculados automaticamente durante a
  execução contínua da plataforma — só em startup, update, ou
  verificação explícita (`POST .../verify`), por design (§28: nunca
  polling contínuo).
- Publisher real (via banco) só é resolvido na API assíncrona (`GET
  /modules/{id}/trust`) — `ModuleCLIValidator` e `AIContextExporter`
  (contextos síncronos) sempre relatam trust level sem considerar o
  Publisher Registry de verdade, só o ID declarado no manifest.
