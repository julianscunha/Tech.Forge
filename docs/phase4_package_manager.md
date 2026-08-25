---
title: TechForge — Fase 4: Package Manager & Marketplace
category: arquitetura-core
domain: [arquitetura-core]
---

# TechForge — Fase 4: Package Manager & Marketplace

## Documentação Técnica

---

## 1. Visão Geral

A Fase 4 implementa a infraestrutura completa de gestão de pacotes da plataforma.
O **Package Manager** é o único componente autorizado a escrever em `modules/installed/`.
O **Marketplace** é a interface de usuário que delega todas as operações ao Package Manager.

Nenhuma linha do Core foi modificada para adicionar estas funcionalidades.

---

## 2. Estrutura de Diretórios

```
modules/
├── repository/    ← .mod files disponíveis para instalar
├── installed/     ← módulos ativos (único destino de escrita do PackageManager)
└── cache/         ← arquivos temporários de extração, backups de versão anterior
```

| Diretório | Quem escreve | Quem lê |
|-----------|-------------|---------|
| `repository/` | Usuário (manual) / Marketplace (Fase 5) | LocalRepositoryProvider |
| `installed/`  | PackageManager (exclusivo) | ModuleLoader |
| `cache/`      | PackageManager (temporário) | PackageManager |

---

## 3. Formato do Arquivo .mod

O `.mod` é um ZIP estruturado com a seguinte árvore interna:

```
<module_id>-<version>.mod
├── manifest.yaml              ← obrigatório na raiz
├── backend/
│   └── main.py                ← entry_backend declarado no manifest
├── frontend/
│   └── index.tsx              ← entry_frontend declarado no manifest
├── assets/                    ← opcional
├── docs/                      ← opcional
├── tests/                     ← opcional
└── META-INF/
    ├── TECHFORGE              ← marcador de formato + versão mínima
    └── BUILD                  ← metadados de build (module_id, version, built_at)
```

**Geração:** `techforge package-module <path>` (CLI Fase 3)

**Sidecar de checksum:** `<filename>.mod.sha256` — SHA-256 do arquivo ZIP completo.

**Fase 5 — assinatura digital:**
`META-INF/SIGNATURE` será adicionado pelo serviço de signing.
Os campos `signature`, `checksum`, `publisher`, `trust_level` já estão presentes
em `PackageInfo` e `ModuleEntryRead` aguardando implementação.

---

## 4. Fluxo de Instalação

```
PackageManager.install(mod_path)
  │
  ├─► 1. Verificar existência do arquivo
  ├─► 2. Validar que é um ZIP válido
  ├─► 3. Extrair e parsear manifest.yaml
  ├─► 4. Verificar compatibilidade de versão
  │       INCOMPATIBLE → rejeitar, logar, retornar InstallStatus.INCOMPATIBLE
  ├─► 5. Verificar instalação duplicada
  │       já instalado → retornar InstallStatus.ALREADY_INSTALLED
  ├─► 6. Extrair para cache/_extract_<module_id>/ (temporário)
  ├─► 7. Mover atomicamente para modules/installed/<module_id>/
  ├─► 8. Hot-reload: ModuleLoader.scan_installed() → registry atualizado
  └─► 9. Logar operação → OperationLog
```

---

## 5. Fluxo de Remoção

```
PackageManager.remove(module_id)
  │
  ├─► 1. Verificar que o módulo está em modules/installed/
  ├─► 2. Ler versão atual do manifest.yaml
  ├─► 3. Deregistrar do registry imediatamente (consistência durante deleção)
  ├─► 4. Deletar modules/installed/<module_id>/
  ├─► 5. Hot-reload registry
  └─► 6. Logar operação → OperationLog
```

---

## 6. Fluxo de Atualização

```
PackageManager.update(module_id, mod_path)
  │
  ├─► 1. Verificar que o módulo está instalado
  ├─► 2. Ler versão instalada atual
  ├─► 3. Parsear manifest da nova versão
  ├─► 4. Verificar que nova versão > versão instalada
  │       não mais nova → retornar UpdateStatus.UP_TO_DATE
  ├─► 5. Verificar compatibilidade da nova versão
  │       incompatível → bloquear, retornar UpdateStatus.INCOMPATIBLE
  ├─► 6. Backup: copiar installed/<id> → cache/<id>-<old_version>.bak
  ├─► 7. Extrair nova versão para cache/_update_<id>/
  ├─► 8. Substituir installed/<id> pela nova versão
  │       falha → rollback automático do backup
  ├─► 9. Hot-reload registry
  └─► 10. Logar operação → OperationLog
```

---

## 7. Hot Reload

Após qualquer install/update/remove, o Package Manager chama:

```python
loader = ModuleLoader()
result = await loader.scan_installed()
loader_journal.store(result)
```

Isso reconstrói o registry in-memory sem reiniciar o processo.
A nova lista de módulos fica imediatamente disponível via
`GET /api/v1/registry/modules`.

O frontend reage fazendo refetch dos dados depois de cada operação,
atualizando as abas Instalados, Disponíveis e Atualizações sem reload de página.

---

## 8. Repository Provider

A abstração `RepositoryProvider` separa o Package Manager de qualquer fonte específica.

```python
class RepositoryProvider(ABC):
    async def list_available(self, platform_version: str) -> list[PackageInfo]: ...
    async def get_package(self, module_id: str, ...) -> Optional[PackageInfo]: ...
    async def fetch_mod_path(self, module_id: str) -> Optional[Path]: ...
```

| Implementação | Estado | Descrição |
|---|---|---|
| `LocalRepositoryProvider` | ✅ Fase 4 | Lê .mod de `modules/repository/` |
| `RemoteRepositoryProvider` | 🔲 Fase 5 | Chama API REST do servidor Marketplace |

---

## 9. API REST do Marketplace

| Método | Caminho | Descrição |
|--------|---------|-----------|
| GET    | `/api/v1/marketplace/installed`        | Módulos instalados |
| GET    | `/api/v1/marketplace/available`        | Pacotes no repositório |
| GET    | `/api/v1/marketplace/updates`          | Atualizações disponíveis |
| POST   | `/api/v1/marketplace/install/{id}`     | Instalar do repositório |
| DELETE | `/api/v1/marketplace/remove/{id}`      | Remover módulo |
| POST   | `/api/v1/marketplace/update/{id}`      | Atualizar módulo |
| POST   | `/api/v1/marketplace/import`           | Importar arquivo .mod |
| POST   | `/api/v1/marketplace/compatibility`    | Verificar compatibilidade |
| GET    | `/api/v1/marketplace/log`              | Log de operações |

---

## 10. Campos de Segurança (Phase 5 preparados)

Todo `PackageInfo` e `ModuleEntryRead` já carrega:

| Campo | Tipo | Fase |
|---|---|---|
| `signature`   | `Optional[str]`  | 5 — assinatura criptográfica do publisher |
| `checksum`    | `Optional[str]`  | 4 — SHA-256 do .mod, calculado ao ler |
| `publisher`   | `Optional[str]`  | 5 — identidade do publicador |
| `trust_level` | `TrustLevel` enum | 5 — `verified/community/unsigned/untrusted` |

---

## 11. Operation Log

Todas as operações são registradas em `OperationLog` (singleton in-process).

```python
operation_log.record("install", "my_module", "1.0.0", "success", "Installed OK")
```

Campos por entrada: `timestamp`, `operation`, `module_id`, `version`, `status`, `message`, `details`.

Acessível via: `GET /api/v1/marketplace/log`

Fase 5: persiste em tabela SQLite para auditoria e Central de Notificações.

---

## 12. Fluxo Completo — do CLI ao Marketplace

```
1. techforge create-module          → scaffold em qualquer diretório
2. techforge validate-module .      → 20 checks de conformidade
3. techforge package-module .       → gera <id>-<version>.mod
4. Copiar .mod → modules/repository/
   — ou — usar "Import .mod" no Marketplace
5. Marketplace → aba Disponíveis → botão Install
6. PackageManager.install()         → extrai para modules/installed/
7. Hot-reload → ModuleRegistry atualizado
8. Tela Módulos → status INSTALLED
9. Marketplace → aba Instalados
```

Nenhuma linha do Core alterada em nenhum passo.
