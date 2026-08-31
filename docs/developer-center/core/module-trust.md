---
title: Module Trust
category: arquitetura-core
domain: [arquitetura-core]
tags: [core, security, integrity, trust, publisher, signature]
order: 6
---

# Module Trust

Base de confiança para módulos do TechForge — integridade por hash,
identidade de publisher, e assinatura digital real (Ed25519). Sem
transformar o sistema local numa plataforma pesada de autenticação —
sem PKI corporativa, sem HSM obrigatório.

## Integrity Manifest

Todo módulo instalado ganha um `integrity.json` — hash SHA-256 por
arquivo, gerado na instalação e regenerado a cada atualização:

```json
{
  "algorithm": "sha256",
  "files": {
    "manifest.yaml": "...",
    "backend/main.py": "..."
  }
}
```

Arquivos ignorados: `data/` (runtime do módulo), `__pycache__/`, `.pyc`,
o próprio `integrity.json`.

## Estados de integridade

| Estado | Significado |
|---|---|
| `VALID` | Todos os arquivos batem com o manifest. |
| `MODIFIED` | Um ou mais arquivos divergem do hash registrado. |
| `MISSING_FILE` | Um arquivo declarado no manifest não existe mais. |
| `UNEXPECTED_FILE` | Um arquivo existe mas não está no manifest. |
| `INVALID_MANIFEST` | `integrity.json` ausente ou corrompido. |

Reverificação é **sob demanda** (startup, update, `POST .../verify`) —
nunca polling contínuo.

## Publisher Identity

```yaml
publisher:
  id: techforge.internal
  name: TechForge Internal
```

Um Publisher tem `type` (OFFICIAL/INTERNAL/THIRD_PARTY/
LOCAL_DEVELOPMENT) e `trust_status` administrativo
(TRUSTED/UNTRUSTED/REVOKED) — mantido no Publisher Registry local
(tabela SQLite, `GET /api/v1/publishers`). A chave pública do
publisher (Ed25519, PEM) vai no campo `public_key`.

## Assinatura digital (Ed25519 real)

`Ed25519SignatureProvider` (`app/module_trust/signature.py`) é o
`default_signature_provider` — sem PKI corporativa: o publisher gera o
par de chaves localmente, a chave pública vai pro Publisher Registry, a
chave **privada nunca toca o Core em runtime**.

**Fluxo pra assinar um módulo:**

```bash
# 1. Gerar um par de chaves (uma vez, guardar a privada offline)
techforge trust generate-keypair --output-dir ./keys --name my-publisher

# 2. Assinar o manifest ANTES de empacotar
techforge sign-module ./my_module --key ./keys/my-publisher_private.pem

# 3. Empacotar — a assinatura já está no manifest.yaml, vai dentro do .mod
techforge package-module ./my_module
```

O que é assinado: `canonical_manifest_bytes(raw)` — o manifest.yaml em
JSON canônico (`sort_keys=True`), **excluindo o próprio campo
`signature`** (senão seria circular). Verificação decodifica a
assinatura de base64 e checa contra a `public_key` do publisher
declarado.

**Status possíveis** (`SignatureStatus`):

| Status | Significado |
|---|---|
| `VALID` | Assinatura confere com o conteúdo e a `public_key` do publisher. |
| `INVALID` | Assinatura presente, mas não confere (conteúdo alterado, ou chave errada). |
| `NOT_CONFIGURED` | Sem assinatura, ou publisher sem `public_key` cadastrada. |
| `UNSUPPORTED` | `public_key` malformada/não é uma chave Ed25519 válida. |

## Trust Level

Combina integridade + publisher + assinatura:

| Nível | Quando |
|---|---|
| `TRUSTED` | Publisher `TRUSTED` **e** assinatura `VALID`. |
| `VERIFIED` | Integridade válida, publisher conhecido e não revogado (assinatura `NOT_CONFIGURED`/`INVALID`/publisher `UNTRUSTED`). |
| `UNVERIFIED` | Integridade válida, publisher desconhecido — padrão de um módulo de desenvolvimento local. |
| `MODIFIED` | Integridade indica arquivo alterado ou inesperado (tem prioridade sobre a assinatura — um arquivo adulterado é `MODIFIED` mesmo que a assinatura "antiga" ainda combine com o manifest não-adulterado). |
| `INVALID` | Manifest de integridade corrompido, arquivo ausente, ou publisher revogado. |

`TRUSTED` é real e alcançável — confirmado em produção:
assinar um módulo, registrar o publisher com `trust_status=TRUSTED` e a
`public_key` correspondente, instalar, e `GET .../trust` retorna
`TRUSTED` de verdade.

## Como criar um pacote verificável

1. Declare `publisher: {id, name}` no `manifest.yaml`.
2. Registre o publisher no Publisher Registry com a `public_key` (Ed25519 PEM).
3. Assine o módulo (`techforge sign-module`) **antes** de empacotar.
4. Empacote e instale normalmente — `integrity.json` é gerado automaticamente.
5. Consulte `GET /api/v1/modules/{id}/trust` pra ver o Trust Level resolvido.

## Secrets (`context.secrets`)

`ModuleSecretStore` (`app/security/secret_store.py`) — cofre nativo do
SO via `keyring`, isolado por `module_id`:

```python
context.secrets.set("api_key", "sk-...")       # cria (primeira vez) ou sobrescreve
context.secrets.get("api_key")                  # None se ausente
context.secrets.rotate("api_key", "sk-new-...")  # troca EXPLÍCITA de um valor existente
context.secrets.delete("api_key")
```

`rotate()` levanta `SecretStoreError` se a key nunca foi criada — não é
um "criar silencioso". `set()` audita `SECRET_CREATED` só na primeira
vez; `rotate()` audita `SECRET_ROTATED`; `delete()` audita
`SECRET_DELETED` (só quando a key existia). Nenhum evento de auditoria
carrega o valor do segredo — só `module_id`/`key`.

**Redação em log**: todo valor gravado via `SecretStore`, mais qualquer
campo com nome sensível (`password`, `token`, `api_key`, `secret`,
`private_key`, `credentials`, **`authorization`**) — incluindo o header
`Authorization: Bearer xxx` inteiro, não só a palavra "Bearer" — vira
`***REDACTED***` em qualquer log.

## Auditoria (Security Audit Events)

Eventos publicados no `EventBus` (`app/observability/events.py`),
prefixo `security.`:

| Evento | Quando |
|---|---|
| `security.package_verified` | Reverificação de integridade (`POST .../verify`) confirma `VALID`. |
| `security.integrity_failure` | Reverificação encontra qualquer estado diferente de `VALID`. |
| `security.signature_valid` / `security.signature_invalid` | `GET .../trust` resolve a assinatura. |
| `security.module_trust_changed` | Trust Level de um módulo muda entre duas chamadas de `GET .../trust` na mesma sessão do processo. |
| `security.module_blocked` | Pacote rejeitado por exceder limites de tamanho/contagem de arquivos (zip bomb). |
| `security.secret_created` / `security.secret_rotated` / `security.secret_deleted` | Lifecycle de um segredo via `context.secrets`. |

Nenhum payload carrega segredo/chave/assinatura crua — só
`module_id`/metadados. `security.signature_invalid`,
`security.integrity_failure` e `security.module_blocked` viram
Notification (nível `error`) automaticamente — os demais são "operação
normal", não notificam.

## Security Policy (Desktop vs Server)

`SecurityPolicy` (`app/module_trust/security_policy.py`) formaliza a
política de "o que fazer com um Trust Level" por ambiente — sem
hardcodar. `DesktopSecurityPolicy` (default) nunca bloqueia instalação
por Trust Level isolado (`allows_install` sempre `True` — bloqueio real
é via integridade/limites de recursos), mas sinaliza aviso
(`requires_warning`) pra qualquer coisa abaixo de `VERIFIED`.
`ServerSecurityPolicy` não está implementada — levanta
`NotImplementedError` deliberadamente (modo servidor multiusuário
continua fora de escopo, ver [`docs/roadmap.md`](../../roadmap.md)).

## Resource limits na extração de pacotes (defesa contra zip bomb)

`MAX_PACKAGE_UNCOMPRESSED_SIZE` (200MB) e `MAX_PACKAGE_FILE_COUNT`
(5.000), configuráveis em `settings.py`. Checados via
`ZipFile.infolist()` (lê só o índice central, nunca descomprime nada)
**antes** de extrair qualquer arquivo do `.mod` — um pacote que excede
qualquer um dos dois limites é rejeitado sem tocar disco.

## API

```bash
GET  /api/v1/modules/{id}/integrity   # leitura, sem efeito colateral
GET  /api/v1/modules/{id}/trust       # resolucao completa (publisher + assinatura real)
GET  /api/v1/modules/trust            # todos os modulos instalados, uma chamada
GET  /api/v1/modules/{id}/sbom        # SBOM minimo: dependencias + publisher + checksum + signature_status
POST /api/v1/modules/{id}/verify      # reverifica e notifica se alterado
GET  /api/v1/publishers               # publishers conhecidos
GET  /api/v1/publishers/{id}
GET  /api/v1/security/status          # agregado: contagem por trust level, nao assinados, publishers revogados
GET  /api/v1/security/publishers      # alias de /publishers
```

## CLI

```bash
techforge trust generate-keypair --output-dir <dir> --name <prefix>
techforge sign-module <module_path> --key <private_key.pem>
techforge validate-module <path>       # inclui Integrity/Signature/Trust
techforge verify-module <id>
techforge integrity check <id>
techforge publishers list              # == techforge trust publishers
techforge publishers show <id>
techforge security status              # == techforge diagnostics security
```

## Secure Module Development Checklist

- [ ] Nunca colocar segredos (API keys, tokens, senhas) no `manifest.yaml` ou no código-fonte do módulo — use `context.secrets`.
- [ ] Nunca logar o valor de um segredo, mesmo em debug — confie na redação, mas não dependa só dela: não construa strings de log com o valor cru.
- [ ] Gere o par de chaves Ed25519 **fora** do Core e mantenha a chave privada offline — nunca commite, nunca envie pro Runtime.
- [ ] Assine o módulo (`techforge sign-module`) **antes** de empacotar, não depois.
- [ ] Valide todo path recebido de fora (upload, catálogo remoto) — nunca confie em `..`/paths absolutos (o `zipfile.extract()` do stdlib já sanitiza isso, mas não reintroduza esse risco em código customizado).
- [ ] Não tente contornar a resolução de Trust Level — se um módulo precisa de `TRUSTED`, assine-o e registre o publisher de verdade; não force o status manualmente.
- [ ] Trate `SecretStoreError` — o cofre pode falhar (SO sem keyring configurado); nunca capture e ignore silenciosamente um erro de segurança.

## Fora de escopo (decisão explícita, spec §47)

Autenticação corporativa complexa, IAM completo, sandbox de containers
por módulo, firewall próprio, SIEM, PKI corporativa obrigatória, HSM
obrigatório, RBAC, SSO, MFA, análise de malware, marketplace remoto.
Infraestrutura central de revogação (CRL/OCSP-like) — revogação hoje é
uma flag manual no Publisher Registry, decisão consciente dado o foco
single-user/local-first. Conflito de capability entre providers
continua só reportado, não resolvido (ver [`docs/limitations.md`](../../limitations.md)).
