---
title: Module Trust
category: arquitetura-core
domain: [arquitetura-core]
tags: [core, security, integrity, trust, publisher]
order: 6
---

# Module Trust

Base de confiança para módulos do TechForge — integridade por hash,
identidade de publisher, e preparação para assinatura digital. Sem
transformar o sistema local numa plataforma pesada de autenticação
(Fase 10).

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
nunca polling contínuo (§28).

## Publisher Identity

```yaml
publisher:
  id: techforge.internal
  name: TechForge Internal
```

Um Publisher tem `type` (OFFICIAL/INTERNAL/THIRD_PARTY/
LOCAL_DEVELOPMENT) e `trust_status` administrativo
(TRUSTED/UNTRUSTED/REVOKED) — mantido no Publisher Registry local
(tabela SQLite, `GET /api/v1/publishers`).

## Trust Level

Combina integridade + publisher + assinatura:

| Nível | Quando |
|---|---|
| `TRUSTED` | Publisher confiável **e** assinatura válida. |
| `VERIFIED` | Integridade válida, publisher conhecido e não revogado. |
| `UNVERIFIED` | Integridade válida, publisher desconhecido — padrão de um módulo de desenvolvimento local. |
| `MODIFIED` | Integridade indica arquivo alterado ou inesperado. |
| `INVALID` | Manifest de integridade corrompido, arquivo ausente, ou publisher revogado. |

**Limitação conhecida desta fase**: `TRUSTED` é estruturalmente
inalcançável — não há implementação real de assinatura digital ainda
(ver abaixo). Isso é esperado, não um bug.

## Assinatura digital (abstração, sem Ed25519 real)

`SignatureProvider` (`sign()`/`verify()`/`identify_algorithm()`) é uma
interface pronta, desacoplada do Package Manager. A implementação
default, `NoOpSignatureProvider`, nunca finge validar uma assinatura
que não pode verificar — sempre retorna `NOT_CONFIGURED` (sem
assinatura) ou `UNSUPPORTED` (assinatura presente, mas sem algoritmo
real implementado). `sign()` levanta `NotImplementedError`
deliberadamente. `techforge sign-module`/`verify-signature` não
existem ainda — dependem de uma implementação real futura.

## Como criar um pacote verificável

1. Declare `publisher: {id, name}` no `manifest.yaml`.
2. Registre o publisher no Publisher Registry (`techforge publishers
   list`/`show` consultam; o registro em si é interno/CLI nesta fase).
3. Instale o módulo normalmente — `integrity.json` é gerado
   automaticamente.
4. Consulte `GET /api/v1/modules/{id}/trust` (ou `techforge integrity
   check <id>`) pra ver o Trust Level resolvido.

## API

```bash
GET  /api/v1/modules/{id}/integrity   # leitura, sem efeito colateral
GET  /api/v1/modules/{id}/trust       # resolucao completa (publisher real)
GET  /api/v1/modules/trust            # todos os modulos instalados, uma chamada
POST /api/v1/modules/{id}/verify      # reverifica e notifica se alterado
GET  /api/v1/publishers               # publishers conhecidos
GET  /api/v1/publishers/{id}
```

## CLI

```bash
techforge validate-module <path>       # inclui Integrity/Signature/Trust (§19)
techforge verify-module <id>
techforge integrity check <id>
techforge publishers list
techforge publishers show <id>
```

## Fora de escopo desta fase

Assinatura Ed25519 real, quarentena física de pacotes (mover pra
diretório separado — a spec marca como opcional, sem caso de uso real
ainda), autenticação corporativa, RBAC, SSO, MFA, sandbox completo,
análise de malware, marketplace remoto.
