# Relatório — Fase 17: Platform Security & Trust Hardening

Status: EM ANDAMENTO.
Plano: `tasks/phase17-plan.md`.

## Slices

### Slice 1 — Resource limits na extração de pacotes

**Arquivos**
- `core/backend/app/core/settings.py` — `MAX_PACKAGE_UNCOMPRESSED_SIZE` (200MB), `MAX_PACKAGE_FILE_COUNT` (5.000)
- `core/backend/app/package_manager/archive_safety.py` (novo) — `safe_extract()`, `PackageTooLargeError`
- `core/backend/app/package_manager/manager.py` — `install()` e `update()` passam a usar `safe_extract()` em vez do loop de extração manual duplicado
- `core/backend/tests/test_phase17_archive_safety.py` (novo, 4 testes unitários)
- `core/backend/tests/test_phase17_package_extraction.py` (novo, 2 testes de integração contra `PackageManager.install()` real)

**O quê**
Defesa contra zip bomb (DoS — spec §16/§18): antes de extrair qualquer membro do `.mod`, `safe_extract()` lê `ZipFile.infolist()` (só o índice central, não descomprime nada) e valida contagem de arquivos e soma do tamanho descomprimido contra os limites configurados. Se exceder, levanta `PackageTooLargeError` antes de tocar o disco.

**Decisão-chave**
Path traversal (`..`, paths absolutos, drive letters) não precisou de tratamento adicional — `zipfile.extract()` do stdlib já sanitiza isso desde Python 3.6.4 (confirmado na investigação prévia). Guard único em `safe_extract()`, reusado por `install()` e `update()`, em vez de duplicar a checagem em cada chamador.

**Aceite**
- Pacote que declara tamanho descomprimido ou contagem de arquivos acima do limite é rejeitado antes da extração; nada é escrito em disco.
- Pacotes dentro do limite continuam instalando normalmente.

**Teste**
- Unitários: `pytest tests/test_phase17_archive_safety.py -q` — 4 passed.
- Integração (via `PackageManager.install()` real): `pytest tests/test_phase17_package_extraction.py -q` — 2 passed.
- Suíte completa: `pytest tests -q` — 892 passed, 3 skipped, sem regressão.
- `ruff check core/backend/app cli sdk` — all checks passed.
- Verificação manual ao vivo: backend real subido (`run.py`), `.mod` real de ~292KB no disco declarando ~300MB descomprimido enviado via `POST /api/v1/marketplace/import` → rejeitado com `"Extraction failed: Package uncompressed size 300000134 bytes exceeds limit of 200000000 bytes"`, diretório do módulo nunca criado. Um `.mod` normal enviado ao mesmo endpoint instalou com sucesso.

**Commit**: `182ecc0`

### Slice 2 — Assinatura Ed25519 real

**Arquivos**
- `core/backend/requirements.txt` — `cryptography==50.0.1`
- `core/backend/app/module_trust/signature.py` — `Ed25519SignatureProvider`, `generate_ed25519_keypair()`, `canonical_manifest_bytes()`; `default_signature_provider` passa a ser `Ed25519SignatureProvider()` (era `NoOpSignatureProvider()`)
- `core/backend/app/module_trust/__init__.py` — exporta os novos símbolos
- `core/backend/app/api/routes/module_verification.py` — `get_module_trust()` corrigido: assinava contra `data=b""` (bug pré-existente, nunca importava porque nunca havia crypto real); agora assina/verifica contra `canonical_manifest_bytes(raw)` e decodifica a assinatura de base64 antes de verificar
- `core/backend/app/doc_engine/__init__.py` — mesmo fix de `data=b""`/decode base64 no AI Context exporter (público-chave continua `None` aqui — gap conhecido, fica pro Slice 3)
- `core/backend/tests/test_phase10_module_trust.py` — `test_default_signature_provider_is_noop_instance` → `test_default_signature_provider_is_ed25519_instance` (decisão consciente desta fase, documentada no teste)
- `cli/techforge_cli/commands/module_trust.py` — `techforge trust generate-keypair`, `techforge sign-module`
- `cli/techforge_cli/main.py` — registra os dois comandos novos
- `core/backend/tests/test_phase17_ed25519_signature.py` (novo, 11 testes unitários)
- `core/backend/tests/test_phase17_signature_integration.py` (novo, 2 testes de integração contra `GET /modules/{id}/trust` real)
- `cli/tests/test_phase17_sign_module_cli.py` (novo, 6 testes)

**O quê**
Assinatura digital real via Ed25519 (`cryptography.hazmat`), sem PKI corporativa: o publisher gera o par de chaves localmente (`techforge trust generate-keypair`), assina o `manifest.yaml` antes de empacotar (`techforge sign-module <dir> --key <private.pem>`), e a chave pública vai pro campo `public_key` já existente no Publisher Registry. `Ed25519SignatureProvider` substitui `NoOpSignatureProvider` como `default_signature_provider`.

**Decisão-chave**
O dado assinado é `canonical_manifest_bytes(raw)` — o dict do manifesto serializado em JSON com `sort_keys=True`, **excluindo o próprio campo `signature`** (senão seria circular: o manifesto muda ao receber a assinatura, invalidando-a). Isso corrigiu de quebra um bug pré-existente da Fase 10 que nunca importava até agora: os dois call-sites de verificação assinavam/verificavam sempre contra `data=b""` — um placeholder que nunca teria detectado adulteração de conteúdo, mesmo com um provider real.

**Aceite**
- Assinatura válida contra a `public_key` do publisher → `SignatureStatus.VALID`.
- Conteúdo alterado depois de assinado, ou assinatura verificada contra chave pública errada → `INVALID`.
- Sem assinatura ou sem chave pública cadastrada → `NOT_CONFIGURED` (comportamento anterior preservado).

**Teste**
- Unitários (`Ed25519SignatureProvider` isolado): `pytest tests/test_phase17_ed25519_signature.py -q` — 11 passed.
- Integração (via `GET /modules/{id}/trust` real, HTTP + DB real): `pytest tests/test_phase17_signature_integration.py -q` — 2 passed, incluindo prova de `TRUSTED` alcançado de verdade e `INVALID` por manifesto adulterado.
- CLI: `pytest tests/test_phase17_sign_module_cli.py -q` (em `cli/`) — 6 passed.
- Suíte completa backend: `pytest tests -q` — 905 passed, 3 skipped (1 teste da Fase 10 atualizado para refletir a troca intencional de default).
- Suíte completa CLI: `pytest tests -q` (em `cli/`) — 124 passed.
- `ruff check core/backend/app cli sdk` — all checks passed.
- **Verificação manual ao vivo, ponta a ponta, com chaves e módulo reais**: `techforge trust generate-keypair` gerou um par Ed25519 real; `techforge sign-module` assinou um módulo real; `techforge package-module` empacotou o `.mod` com a assinatura embutida; publisher real registrado com `trust_status=TRUSTED` e a chave pública real; módulo instalado via `POST /marketplace/import` real → `GET /modules/{id}/trust` retornou `"trust_level":"TRUSTED","signature_status":"VALID"` — **primeira vez que `TRUSTED` é alcançado de verdade na plataforma**. Em seguida, o `manifest.yaml` já instalado foi adulterado em disco e o endpoint `/verify` reexecutado: o integrity check (hash por arquivo) capturou a divergência antes mesmo da assinatura entrar em jogo, e o trust level caiu para `MODIFIED` — as duas camadas de defesa (integridade de arquivo + assinatura de manifesto) atuando corretamente em conjunto.

**Commit**: _(pendente)_
