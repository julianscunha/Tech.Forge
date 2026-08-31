# Plano — Fase 17: Platform Security & Trust Hardening

> Spec: docs/phases/17-Fase-17-Platform-Security-Trust-Hardening.md
> Pré-requisito: Fase 16 (Desktop Distribution) ✅ fechada.
> Skill aplicada: `security-and-hardening` — threat model por boundary antes
> de codar cada slice (STRIDE resumido abaixo por slice).

## Premissas validadas (investigação de código real)

1. `app/module_trust/` (Fase 10) já implementa integrity manifest,
   Publisher Registry (SQLite, coluna `public_key` existente mas nunca
   lida), `TrustResolver` (lógica correta) e `SignatureProvider` — mas
   a única implementação é `NoOpSignatureProvider`: `sign()` levanta
   `NotImplementedError`, `verify()` só retorna `NOT_CONFIGURED`.
   `TRUSTED` é matematicamente inalcançável hoje.
2. `techforge sign-module`/`verify-signature` não existem em CLI nem API.
3. Extração de `.mod` (`app/package_manager/manager.py`, install/update):
   `zipfile.extract()` já sanitiza path traversal (stdlib desde Python
   3.6.4) — não é vulnerabilidade aberta hoje. Staging + atomic move já
   existem. **Sem limite de tamanho/contagem de arquivo** — zip bomb é
   o gap de risco real (§18).
4. `ModuleSecretStore` (Fase 12) já é o `SecretProvider` do spec, com
   outro nome, isolado por `module_id`. Redação de log já cobre
   password/token/api_key/secret — falta "authorization" no padrão.
   Falta `rotate()` nomeado e eventos de auditoria.
5. `EventBus.publish(event_type: str, **payload)` (Fase 14) é genérico
   por string — registrar eventos de segurança não exige infra nova.
6. `dependency_engine` (Fase 8.1) já tem módulo+deps+versões — base
   pronta pra SBOM mínimo.
7. `/api/v1/security/*` e `techforge security status`/`diagnostics
   security` não existem hoje — capacidade existe espalhada em
   `/modules/*`/`/publishers*`.
8. `ModuleCLIValidator`/`AIContextExporter` (gap já conhecido do
   phase-audit.md) não consultam o Publisher Registry real — só o ID
   declarado no manifest.

## Decisões arquiteturais (confirmadas com o usuário antes do plano)

1. **Assinatura digital real: Ed25519, sem PKI.** Lib `cryptography`
   (padrão de facto, sem inventar cripto). Publisher gera par de chaves
   localmente (fora do Core); chave pública vai pro campo `public_key`
   já existente no Publisher Registry; chave privada nunca toca o
   Runtime (spec §12). `Ed25519SignatureProvider` real substitui
   `NoOpSignatureProvider` como default.
2. **Zip bomb / resource limits: prioridade 1**, antes de qualquer item
   de "preparação arquitetural" — é o único risco real e explorável
   hoje. Checar `zf.infolist()` (tamanho total descomprimido, contagem
   de membros) antes de extrair, limites configuráveis em `settings.py`.
3. **Desktop vs Server: abstração mínima.** `SecurityPolicy` com 1
   implementação real (`DesktopSecurityPolicy` — política já em vigor:
   UNVERIFIED = warning, não block), interface documentada pra Server
   futuro. Mesmo racional da Fase 13 (adiada) — não construir Server
   hipotético.
4. **SBOM/Supply Chain: mínimo honesto.** Endpoint de leitura sobre
   `dependency_engine` — `{module, version, dependencies[], publisher,
   checksum, signature_status}`. Sem SPDX/CycloneDX, sem lib nova.
5. **Fora de escopo — decisão explícita (spec §47)**: autenticação
   corporativa complexa, IAM completo, sandbox de containers por
   módulo, firewall próprio, SIEM, PKI corporativa obrigatória, HSM
   obrigatório.

## Slices

### Slice 1 — Resource limits na extração de pacotes (TDD) — §16/§18
**Threat model**: DoS (zip bomb) — um `.mod` de poucos KB pode
descomprimir pra gigabytes e travar a instalação. Boundary: qualquer
`.mod` recebido (catálogo remoto ou upload local) antes de extrair.
- `MAX_PACKAGE_UNCOMPRESSED_SIZE` / `MAX_PACKAGE_FILE_COUNT` em
  `settings.py` (defaults sensatos, configuráveis).
- Checagem via `zf.infolist()` (soma de `file_size`, contagem de
  membros) ANTES de extrair qualquer arquivo — bloqueia com erro
  explícito + evento de auditoria (`SECURITY.PACKAGE_BLOCKED`).

**Aceite**: pacote dentro do limite instala normal; pacote sintético
que excede tamanho ou contagem é bloqueado antes de tocar disco, com
mensagem clara (não trava o processo).

### Slice 2 — Assinatura Ed25519 real (TDD) — §7/§12
**Threat model**: Spoofing/Tampering — pacote de publisher não
verificado sendo tratado como confiável. Boundary: instalação de
módulo com `signature` declarada no manifest.
- `cryptography` como dependência nova (Ed25519 via `cryptography.hazmat`).
- `Ed25519SignatureProvider(SignatureProvider)`: `verify(package_bytes,
  signature, public_key_pem) -> SignatureStatus.VALID/INVALID`.
- `techforge sign-module <path> --key <private_key.pem>` (CLI,
  desenvolvedor/publisher assina localmente — chave privada nunca
  entra no Core em runtime).
- `techforge trust generate-keypair` — helper pra gerar par de chaves
  Ed25519 (conveniência, documentado, não obrigatório usar).

**Aceite**: assinatura válida contra a `public_key` do publisher →
`SignatureStatus.VALID`; assinatura alterada/pacote adulterado →
`INVALID`; sem chave pública cadastrada → `NOT_CONFIGURED` (comportamento
atual preservado).

### Slice 3 — TrustResolver atinge TRUSTED + Publisher Registry real nos validadores síncronos (TDD) — §8/§9/§11
- `TrustResolver.resolve()` já tem a lógica certa — só passa a receber
  `SignatureStatus.VALID` de verdade agora que o Slice 2 existe.
- `ModuleCLIValidator`/`AIContextExporter` (gap conhecido do
  phase-audit.md): passam a consultar o Publisher Registry real em vez
  de só o ID declarado no manifest.

**Checkpoint 1**: suíte completa + fluxo manual (assinar um módulo de
teste, instalar, ver TRUSTED de verdade pela primeira vez).

### Slice 4 — `/api/v1/security/*` + CLI de segurança (TDD) — §44/§45
- `GET /api/v1/security/status` — agregado (contagem por trust state,
  módulos não assinados, revogados).
- `GET /api/v1/security/publishers` (alias do que já existe em
  `/publishers`, sob o prefixo pedido pelo spec).
- `techforge security status`, `techforge trust publishers`,
  `techforge diagnostics security` (subcomando novo).

**Aceite**: endpoints/comandos reusam os serviços existentes (nenhuma
lógica de trust duplicada), só agregam/reexpõem.

### Slice 5 — Audit events de segurança (TDD) — §36
- `event_bus.publish("SECURITY.PACKAGE_VERIFIED"|"SIGNATURE_INVALID"|
  "MODULE_BLOCKED"|"MODULE_TRUST_CHANGED", ...)` nos call-sites já
  existentes de verificação/instalação — nenhum valor sensível no payload.

**Aceite**: cada evento do §36 tem pelo menos um call-site real
disparando-o; nenhum evento carrega segredo/token no payload (testado).

### Slice 6 — Secret lifecycle explícito + redação (TDD) — §22-26
- `ModuleSecretStore.rotate(key)` nomeado (hoje é só `set()` de novo)
  + eventos `SECRET_CREATED`/`SECRET_ROTATED`/`SECRET_DELETED`.
- Padrão de redação de log ganha `authorization`/`authorization header`
  explícito (spec §25 cita nominalmente).

**Aceite**: `rotate()` audita sem vazar o valor; teste de redação cobre
"Authorization: Bearer xxx" sendo redigido.

**Checkpoint 2**: suíte completa.

### Slice 7 — SBOM / Supply Chain metadata mínimo (TDD) — §31/§32
- `GET /api/v1/modules/{id}/sbom` (ou dentro do payload de trust) —
  `{module, version, dependencies[], publisher, checksum,
  signature_status}` reaproveitando `dependency_engine`.

**Aceite**: payload reflete dependências reais declaradas no manifest,
sem formato SPDX/CycloneDX.

### Slice 8 — Security UI (frontend) — §38/§39
- Página do módulo: Trust, Integrity, Publisher, Signature,
  Capabilities, Security Warnings — linguagem clara (ex.: "Verified —
  Package integrity confirmed. Publisher signature not configured.").
- Notificação só pra eventos relevantes (integrity failure, signature
  invalid, module revoked, secret provider unavailable) — não pra
  operação normal.

**Aceite**: `npm run lint`/`npm run build` limpos; TRUSTED/VERIFIED/
UNVERIFIED/INVALID/REVOKED nunca ambíguos na UI.

### Slice 9 — Developer Center + AI Context + fechamento — §42/§43
- Developer Center: package trust, checksums, assinaturas, publisher
  identity, key management, unsigned dev modules, capabilities,
  secrets, secure configuration, update security, revocation +
  "Secure Module Development Checklist".
- AI Context: regras explícitas (never put secrets in manifests, never
  log credentials, validate all package paths, use SecretProvider, do
  not bypass trust validation).
- `tasks/phase-audit.md` + `tasks/phase-17-report.md` consolidado.
- Auditoria final contra os 33 critérios de aceitação do spec §48.

## Known Issues esperados (documentar no report, não bloquear a fase)

- Sem infraestrutura central de revogação (§13) além de flag manual no
  Publisher Registry — sem CRL/OCSP-like real, decisão consciente dado
  o foco single-user/local-first.
- `SecurityPolicy` só tem `DesktopSecurityPolicy` real — Server fica
  documentado, não implementado (mesmo racional da Fase 13 adiada).
- Conflito de capability entre providers continua só reportado, não
  resolvido (gap pré-existente da Fase 8, fora do escopo desta fase).
