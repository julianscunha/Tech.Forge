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

**Commit**: _(pendente)_
