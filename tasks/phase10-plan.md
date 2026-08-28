# Plano — Fase 10: Security, Integrity & Module Trust

> Spec: docs/phases/10-Fase-10-Security-Integrity-Module-Trust.md
> Pré-requisito: Fase 9 (Module Runtime & Execution) ✅ fechada.

## Premissas validadas (investigação de código real)

1. ✅ Checksum SHA-256 **já existe**, mas é hash de todo o `.mod` (zip
   inteiro) — `package_manager/repository.py:132-134`, calculado só em
   `list_available()` (repositório, nem chega a ser instalado), guardado
   em `PackageInfo.checksum` (dataclass transiente). `Module.checksum`
   (DB) sempre `NULL` na prática — `registry_sync.py` nunca escreve.
   Nunca verificado depois de instalado.
2. ✅ `TrustLevel` (`package_manager/enums.py:26-34`) já existe —
   `VERIFIED/COMMUNITY/UNSIGNED/UNTRUSTED` — mas é sempre hardcoded
   `UNSIGNED` em `PackageInfo.trust_level`, nunca calculado de verdade.
   Nomes diferentes dos da spec (TRUSTED/VERIFIED/UNVERIFIED/MODIFIED/
   INVALID) — decisão do usuário: substituir pelos valores da spec.
3. ✅ `manifest.yaml`: `vendor`/`author` são strings de exibição, sem
   identidade/confiança por trás — não é o mesmo conceito de Publisher.
   `ParsedManifest.signature`/`checksum` já existem (Optional, sempre
   `None` na prática). `ParsedManifest.source_type`/`source_location`
   já existem (`local|catalog|development`) — ~70% do conceito de
   Package Provenance da spec, só nunca sincronizado pro DB.
4. ✅ Pacote `.mod` é zip (`zipfile.ZipFile`) — `manifest.yaml` +
   `backend/`/`frontend/` + `META-INF/TECHFORGE`+`META-INF/BUILD`.
   Nenhum `integrity.json` hoje.
5. ✅ `ValidationReport`/`CheckResult` (`cli/.../module_validator.py`)
   já suporta encaixar mais uma seção (`_check_integrity`/`_check_trust`)
   exatamente como `_check_dependency_governance` (Fase 8.1) fez.
6. ✅ `NotificationService.create()` (Fase 2) reusável direto, mesmo
   padrão de dedupe manual (query antes de criar) já usado 2x no projeto.
7. ✅ Projeto é 100% SQLite-first pra estado runtime — nenhum precedente
   de config escrita em arquivo pelo Core (YAML só é lido, nunca
   escrito em runtime). Decisão do usuário: Publisher Registry vira
   tabela SQLite nova, não arquivo (diverge da sugestão literal da spec,
   mas consistente com o padrão dominante do projeto).
8. ✅ `hello_world`/`veeam_m365` não têm publisher/signature reais —
   não serão usados como "publisher trusted" fictício (mesma cautela da
   Fase 8.1 com Provider/Consumer).
9. ✅ `ModuleDetailPanel.tsx` já tem o padrão de seções condicionais
   (`Section` helper) — encaixa "Trust & Integrity" sem reescrever nada.
10. ✅ `make_mod_file()` (`test_phase4.py`) é o helper de teste certo pra
    adaptar (gerar múltiplos arquivos com conteúdo variável, pra hash
    por-arquivo).

## Decisões arquiteturais (confirmadas com o usuário antes do plano)

1. **Publisher Registry**: tabela SQLite nova (`publishers`), não
   arquivo — consistente com `app/models/`+`app/db/`.
2. **Assinatura Ed25519**: só a abstração `SignatureProvider`
   (`sign()`/`verify()`/`identify_algorithm()`) com implementação
   `NoOpSignatureProvider` retornando `NOT_CONFIGURED`. Sem chave
   privada real, sem fluxo de assinatura ponta a ponta nesta fase —
   a própria spec permite ("se não madura, deixar a abstração pronta").
   **Consequência direta**: sem assinatura real, o Trust Level
   `TRUSTED` (spec: "publisher conhecido **e assinatura válida**")
   fica estruturalmente inalcançável nesta fase — documentado como
   Known Issue, não um bug.
3. **Granularidade do hash**: por-arquivo, `integrity.json` novo dentro
   do pacote instalado — permite os estados MODIFIED/MISSING_FILE/
   UNEXPECTED_FILE exigidos pela spec (o checksum de arquivo único
   existente não permite saber QUAL arquivo mudou). Os dois hashes
   coexistem: checksum do `.mod` (identidade do pacote como um todo,
   Fase 4) e `integrity.json` (arquivos individuais, Fase 10) — propósitos
   diferentes, sem duplicação de conceito.
4. **`TrustLevel`**: substituído pelos valores da spec
   (`TRUSTED/VERIFIED/UNVERIFIED/MODIFIED/INVALID`), finalmente
   calculado de verdade — um só conceito de trust level no projeto.

## Regras de resolução de Trust Level (derivadas da spec §8, não perguntadas)

```text
INVALID     — formato de pacote inválido, OU integrity = INVALID_MANIFEST/MISSING_FILE,
              OU publisher revogado (trust_status = REVOKED)
MODIFIED    — integrity = MODIFIED (arquivo instalado diverge do integrity.json)
TRUSTED     — publisher conhecido E trust_status confiável E assinatura VALID
              (estruturalmente inalcançável nesta fase — sem SignatureProvider real)
VERIFIED    — integrity = VALID E publisher registrado e não revogado
UNVERIFIED  — integrity = VALID E publisher desconhecido/não registrado
              (default de módulo de desenvolvimento local sem publisher)
```

## Novo pacote

```
core/backend/app/module_trust/
  integrity.py   # IntegrityManifest (gera/verifica), IntegrityStatus (§6)
  signature.py   # SignatureProvider (abstrato) + NoOpSignatureProvider, SignatureStatus (§11)
  trust.py       # TrustLevel (§8, valores da spec) + TrustResolver (combina integrity+publisher+signature)
  provenance.py  # InstallSource (§14) + resolve() a partir de ParsedManifest.source_type
  verifier.py    # PackageVerifier — pipeline consolidado (§7/§19)
```

`app/models/publisher.py` (novo, SQLAlchemy) + `app/schemas/publisher.py`
+ `app/services/publisher.py` (CRUD) — mesmo padrão de `models/registry.py`.

## Slices

### Slice 1 — Integrity Manifest (TDD) — §5/§6
- `module_trust/integrity.py::IntegrityStatus` (VALID/MODIFIED/
  MISSING_FILE/UNEXPECTED_FILE/INVALID_MANIFEST).
- `generate_integrity_manifest(package_dir) -> dict`: SHA-256 por
  arquivo relevante (ignora `data/`, `__pycache__`, `.pyc`, arquivos
  temporários — mesma lista de exclusão já usada implicitamente pelo
  Package Manager pra não empacotar `data/`).
- `verify_integrity(package_dir, manifest) -> IntegrityStatus` (+ lista
  de arquivos divergentes/ausentes/inesperados, não só o status agregado).
- `integrity.json` escrito no diretório instalado do módulo na
  instalação (`package_manager/manager.py::install`).

**Aceite:** pacote de teste (`make_mod_file` adaptado) gera integrity
manifest correto; modificar um arquivo depois de instalado → `MODIFIED`
com o path do arquivo; remover um arquivo → `MISSING_FILE`; adicionar um
arquivo não declarado → `UNEXPECTED_FILE`; `integrity.json` corrompido/
ausente → `INVALID_MANIFEST`.

### Slice 2 — Publisher model + Registry (TDD) — §10/§13
- `app/models/publisher.py::Publisher` (id, name, type, public_key,
  trust_status, metadata, created_at). `PublisherType`
  (OFFICIAL/INTERNAL/THIRD_PARTY/LOCAL_DEVELOPMENT). `TrustStatus`
  (TRUSTED/UNTRUSTED/REVOKED — status administrativo do publisher, não
  confundir com o `TrustLevel` do módulo).
- `app/services/publisher.py::PublisherService` (register/get/list/
  set_trust_status/revoke) — CRUD simples, mesmo padrão de
  `services/registry.py`.
- API somente-leitura básica (`GET /publishers`, `/publishers/{id}`)
  entra aqui pra já ter algo testável ponta a ponta; escrita
  (`register`) fica CLI-only/interno nesta fase (spec não pede endpoint
  de escrita pública).

**Aceite:** publisher conhecido resolvido corretamente; publisher
desconhecido retorna 404; publisher revogado sinalizado.

### Slice 3 — TrustResolver (TDD) — §8
- `module_trust/trust.py::TrustLevel` (valores da spec, substitui o
  enum antigo em `package_manager/enums.py` — usos existentes migrados).
- `TrustResolver.resolve(integrity_status, publisher, signature_status)
  -> TrustLevel` — implementa as regras documentadas acima.

**Aceite:** os 5 estados cobertos por teste unitário, incluindo o caso
"publisher revogado" → `INVALID` mesmo com integridade `VALID`.

### Slice 4 — SignatureProvider (abstração) — §11/§12
- `module_trust/signature.py::SignatureStatus`
  (NOT_CONFIGURED/VALID/INVALID/UNSUPPORTED).
- `SignatureProvider` (ABC: `sign()`/`verify()`/`identify_algorithm()`)
  + `NoOpSignatureProvider` (implementação default, sempre
  `NOT_CONFIGURED`) — desacoplado do Package Manager (spec §11: "não
  acoplar a primeira implementação a todo o Core").

**Aceite:** `NoOpSignatureProvider().verify(...)` sempre `NOT_CONFIGURED`;
interface documentada como ponto de extensão futuro (Ed25519 real fica
pra quando houver caso de uso — Known Issue documentado, não um TODO
vago).

### Slice 5 — Package Verification Pipeline + Provenance (TDD) — §7/§14/§19/§25
- `module_trust/verifier.py::PackageVerifier.verify(package_dir) ->
  PackageVerificationResult`: format → manifest → compatibility →
  integrity → signature → dependency (reusa `DependencyValidator` da
  Fase 8.1, não duplica) → `TrustLevel` consolidado.
- Integrado a `ModuleCLIValidator` (novo `_check_integrity`/
  `_check_signature`/`_check_trust`, mesmo padrão de
  `_check_dependency_governance`).
- `module_trust/provenance.py::InstallSource`
  (LOCAL_FILE/LOCAL_DEVELOPMENT/INTERNAL_CATALOG/REMOTE_CATALOG),
  `resolve(source_type)` mapeia o campo já existente do manifest.
  Fecha a lacuna real já identificada: `ParsedManifest.source_type`
  nunca chegava a ser sincronizado pro DB — `registry_sync.py` passa a
  gravar `install_source` (coluna nova em `Module`, migração leve como
  as já existentes em `app/db/`).
- `PackageManager.install()`: pacote com `PackageVerificationResult`
  contendo falha de integridade (`INVALID_MANIFEST`/`MISSING_FILE`) **não
  instala silenciosamente** — bloqueia com relatório claro (§7).

**Aceite:** instalação de pacote com integridade violada é bloqueada;
`techforge validate-module` mostra o bloco consolidado (Structure/
Compatibility/Dependencies/Documentation/Integrity/Signature/Trust,
formato do §19); provenance correto (`LOCAL_FILE` pra instalação normal
via `.mod`, `LOCAL_DEVELOPMENT` pra symlink/dev).

### Slice 6 — Runtime verification + Modified Module Policy + Notifications — §15/§16/§17/§20
- `POST /api/v1/modules/{id}/verify`: reverifica integridade sob
  demanda (event-driven — startup, install, update, verificação manual;
  **não** polling contínuo, per §28).
- Módulo alterado detectado → `RuntimeState` não muda sozinho (isso é
  território da Fase 9, não desta), mas gera notificação (dedupe) e
  marca `TrustLevel = MODIFIED` — não bloqueia execução por padrão
  (§16: política inicial não impede automaticamente).
- Quarantine (§17): falha grave de integridade na instalação já é
  coberta pelo bloqueio do Slice 5 (não instala) — mover fisicamente
  pra uma "área de quarentena" é explicitamente opcional na spec
  ("opcionalmente"); não implementado nesta fase por não haver caso de
  uso real ainda (evita infra especulativa) — documentado como Known
  Issue com o caminho de extensão claro.
- Eventos notificados: integrity changed, unknown publisher, trust
  revoked, module modified — reusa `NotificationService.create()` com
  dedupe (mesmo padrão já usado 2x no projeto).

**Aceite:** modificar um arquivo de módulo instalado e chamar
`POST .../verify` → `MODIFIED` + notificação (uma vez, dedupe em
chamada repetida); Core continua respondendo normalmente.

### Slice 7 — API + CLI — §23/§24
- `GET /api/v1/modules/{id}/integrity`, `/modules/{id}/trust`,
  `POST /modules/{id}/verify` (Slice 6), `GET /publishers` (Slice 2 já
  cobriu as rotas de publisher — aqui só o que falta).
- `techforge verify-module <module>`, `techforge integrity check
  <module>`, `techforge publishers list|show` — mesmo padrão HTTP-only
  já usado por `runtime.py`/`services.py`. `techforge validate-module`
  (Fase 3, já existente) ganha as seções novas do Slice 5 automaticamente.
- `techforge sign-module`/`verify-signature` **não implementados** —
  dependem de assinatura real (Slice 4 é só abstração); documentado
  como Known Issue.

**Aceite:** rotas e comandos testados (schema Pydantic próprio,
CliRunner-equivalente).

### Slice 8 — Frontend + Developer Center + AI Context + regra final
- `ModuleDetailPanel.tsx`: seção "Trust & Integrity" (Publisher, Trust
  Level, Integrity, Signature, Package Hash, Install Source, Last
  Verification) — mesmo padrão condicional de Dependências/Dependentes.
- Indicador discreto na lista de módulos (`ModuleCard.tsx` ou
  equivalente): `✓ Trusted / ✓ Verified / ! Modified / ! Unverified /
  ✕ Invalid` (§22).
- `docs/developer-center/core/module-trust.md` (novo): integrity
  manifest, publisher identity, trust levels, assinatura (estado atual:
  abstração), desenvolvimento local, como criar pacote verificável.
- `AIContextExporter`: seção "Module Trust" — Trust Level + Publisher de
  cada módulo instalado (condicional, só aparece com algo relevante,
  mesmo padrão de "Dependency Governance"/"Module Runtime Context").
- Teste integrado completo (§29, regra final, tudo em `tmp_path`):
  criar pacote → gerar integrity → instalar → verificar `VALID` →
  modificar arquivo → verificar `MODIFIED` → notificação (dedupe);
  publisher desconhecido → pacote válido → `UNVERIFIED`; publisher
  revogado → `INVALID`.
- `tasks/phase-10-report.md` + `phase-audit.md` + README roadmap
  atualizados.
- Validar no navegador (Playwright): badge de trust na lista de
  módulos, seção Trust & Integrity no detalhe, zero erros de console.

**Aceite:** critérios §31 aplicáveis ao escopo decidido (TRUSTED
estruturalmente inalcançável é esperado, não uma falha) + suíte
completa + `npm run build` limpos.

## Fora de escopo (spec §30, reafirmado)
Autenticação corporativa completa, RBAC, SSO, MFA, sandbox completo,
análise de malware, marketplace remoto, distribuição central.

## Fora de escopo (decisões desta fase, documentar como Known Issue)
- Assinatura Ed25519 real (Slice 4 é só abstração) — logo, `TRUSTED`
  fica inalcançável e `techforge sign-module`/`verify-signature` não
  existem ainda.
- Quarantine física (mover pacote pra diretório separado) — a spec já
  marca como opcional; sem caso de uso real, fica só o bloqueio de
  instalação (Slice 5) + notificação (Slice 6).

## Ordem
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8; rodar suíte completa
(`pytest tests -q` + `npm run build`) após cada slice; commit/push por
slice. Execução mecânica de cada slice delegada a subagente Haiku após
eu confirmar o design da slice (novo acordo de roteamento de modelo).
