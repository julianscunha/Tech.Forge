---
title: Module Catalog
category: core-architecture
domain: [core]
---

# Catálogo de Módulos — Fase 11

> Descubra, gerencie e instale módulos de múltiplas fontes com verificação de integridade,
> detecção de conflitos e acompanhamento de progresso.

## Visão Geral

O Catálogo de Módulos é a camada de distribuição do TechForge. Ele agrega módulos de múltiplas fontes
(repositório local, catálogo oficial, repositórios customizados) e permite instalação remota com
acompanhamento de progresso e recuperação de erros.

**Princípios-chave:**
- **Múltiplas fontes, uma prioridade:** LOCAL > OFFICIAL_CATALOG > CUSTOM_CATALOG(s)
- **Sem instalação parcial:** Falha retorna a um estado limpo; sucesso garante consistência
- **Resiliência de rede:** Uma fonte indisponível não bloqueia as demais
- **Instalação orientada pelo cliente:** Usuário clica explicitamente em "instalar"; sem polling em segundo plano

---

## Tipos de Fonte

### Repositório Local
- **Localização:** `modules/repository/` em disco
- **Formato:** arquivos `.mod` (arquivos ZIP)
- **Descoberta:** varredura do sistema de arquivos na inicialização da plataforma
- **Uso:** desenvolvimento, contribuições da comunidade

### Catálogo Oficial
- **Hospedado por:** TechForge (nós)
- **URL:** definida em `CatalogSourceConfig` (tipicamente `https://techforge.io/catalog`)
- **Formato:** `index.json` (metadados de todos os módulos) + arquivos `.mod`
- **Gerado por:** pipeline de CI/CD (ver "Publicação" abaixo)
- **Uso:** módulos verificados; atualizações automáticas via sincronização do registry

### Catálogo Customizado
- **Hospedado por:** terceiros (GitHub, GitLab, self-hosted)
- **URL:** configurada pelo usuário por fonte em `CatalogSourceConfig`
- **Formato:** GitHub Contents API + estrutura de pastas (sem automação necessária)
- **Descoberta:** pasta `modules/<id>/manifest.yaml` por módulo
- **Uso:** fontes específicas de organização, mantidas pelo próprio usuário

---

## Configuração de Fontes

Armazenada em SQLite (tabela `catalog_sources`):

```python
class CatalogSourceConfig(Base):
    __tablename__ = "catalog_sources"

    id: str              # UUID
    name: str            # "Módulos da Minha Equipe"
    url: str             # "https://github.com/myorg/techforge-modules"
    type: str            # "official_catalog" ou "custom_catalog"
    enabled: bool        # alternância True/False
    created_at: datetime
    updated_at: datetime
```

**Múltiplas fontes customizadas são permitidas.** Sem limite; a ordem importa (ordem de criação = prioridade).

---

## Catálogo Oficial: formato do `index.json`

Publicado em `https://raw.githubusercontent.com/julianscunha/Tech.Forge.Modules/main/modules/index.json`
(`settings.OFFICIAL_CATALOG_BASE_URL`).

```json
{
  "modules": [
    {
      "id": "module_a",
      "name": "Module A",
      "version": "1.0.0",
      "category": "Utilities",
      "vendor": "TechForge",
      "author": "Team",
      "description": "Does useful things",
      "mod_url": "module_a/module_a-1.0.0.mod",
      "checksum": "c4d19d96b2f4280baa0e91260472981fef76c11c801038514e5fd2d9e71e30bc"
    }
  ]
}
```

Formato real gerado por `techforge catalog build-index` (validado contra um `index.json`
real servido localmente, Fase 11 fechamento). `mod_url` é relativo ao `base_url` da fonte
— `OfficialCatalogProvider` resolve `f"{base_url}/{mod_url}"` quando não é uma URL absoluta.
O caminho é aninhado por módulo (`<id>/<id>-<versão>.mod`, não um arquivo solto) — cada
versão já publicada de um módulo fica empilhada na mesma pasta, para sempre; `index.json`
sempre aponta só para a mais recente.

Gere com:
```bash
techforge catalog build-index <source_dir> --output <catalog_dir>
```

Isso:
1. Varre `<source_dir>/modules/*/manifest.yaml`
2. Compacta cada módulo em `.mod`
3. Escreve `index.json` com os metadados

**Sem etapa de PR/revisão:** os arquivos `.mod` são construídos a partir do código-fonte a cada merge;
o índice é regenerado automaticamente.

---

## Catálogo Customizado: Convenção de Diretório

Nenhuma automação é necessária. Seu repositório precisa ter:

```
your-repo/
  modules/
    module_a/
      manifest.yaml
      backend/
        main.py
      frontend/
        main.js
    module_b/
      manifest.yaml
      backend/
      frontend/
```

**É só isso.** A plataforma:
1. Lista `modules/` via GitHub Contents API
2. Lê `manifest.yaml` de cada pasta
3. Em `POST /marketplace/install-remote/{id}`, baixa todos os arquivos e os compacta

Não é necessário pré-construir arquivos `.mod`; a plataforma faz isso sob demanda.

---

## Detecção de Conflitos

Quando o mesmo `module_id` aparece em mais de 1 fonte, a UI avisa o usuário:

```
"Disponível em 3 fontes" (chip no card)
```

O usuário escolhe de qual fonte instalar. **Nenhuma seleção silenciosa.**

A detecção de conflitos é automática via `detect_conflicts(packages: list[PackageInfo])`.

---

## Cache

**Por fonte, em memória, com TTL.**

- **TTL padrão:** 15 minutos (configurável em `settings.py`)
- **Chave de cache:** `source_id`
- **Gatilhos de invalidação:**
  - TTL expira → a próxima chamada busca de novo
  - Usuário clica em "Atualizar" → `force_refresh=True` ignora o TTL
  - URL do `CatalogSourceConfig` editada → cache limpo imediatamente
  - Fonte removida → cache limpo imediatamente

**Importante:** baixar um módulo (instalar) nunca usa cache.
`fetch_mod_path()` sempre busca da fonte ao vivo no clique do usuário.

---

## Fluxo de Instalação: Fonte Remota

```
POST /marketplace/install-remote/{module_id}
  ↓
Cria job assíncrono: ACQUIRING
  ↓
Resolve o provider (qual fonte tem este módulo?)
  ↓
fetch_mod_path() — baixa para cache/
  ↓
Job → VALIDATING → INSTALLING
  ↓
package_manager.install(mod_path) — mesmo pipeline da instalação local
  ↓
Job → DONE (ou FAILED com mensagem de erro)
  ↓
GET /marketplace/install-jobs/{job_id} — polling de progresso
```

**Sem WebSocket/SSE.** Polling simples; a UI atualiza a cada 500–1000ms.

---

## Confiança & Verificação

Módulos remotos passam pelo mesmo pipeline de verificação que os locais:

1. **Integridade** (SHA-256 por arquivo) — gerada durante a instalação
2. **Assinatura** (opcional, depende do provider)
3. **Publicador** (resolvido a partir do manifest)
4. **Nível de Confiança** (TRUSTED, VERIFIED, UNVERIFIED, MODIFIED, INVALID)

Não há diferença na verificação; todos os módulos são módulos.

---

## Notificações

O agregador cria notificações apenas em *transições* de disponibilidade:

- **Fonte estava disponível, agora não está:** "Catálogo indisponível" (nível warning)
- **Dedupe:** apenas 1 notificação por transição; falhas repetidas não geram spam
- **Fonte se recupera:** notificação opcional (detalhe de implementação; atualmente não é enviada)

---

## Endpoints da API

### Listagem & Descoberta

| Endpoint | Método | Propósito |
|----------|--------|-----------|
| `/catalog/modules` | GET | Lista todos os módulos disponíveis com filtros |
| `/catalog/modules/{id}` | GET | Detalhe de um módulo |
| `/catalog/categories` | GET | Lista de categorias com contagens |
| `/catalog/sources` | GET | Status de todas as fontes configuradas |
| `/catalog/updates` | GET | Módulos instalados com atualizações disponíveis |

### Favoritos (Somente Local)

| Endpoint | Método | Propósito |
|----------|--------|-----------|
| `/catalog/favorites` | GET | Lista IDs de módulos favoritados |
| `/catalog/favorites/{id}` | POST | Favoritar um módulo |
| `/catalog/favorites/{id}` | DELETE | Desfavoritar um módulo |

### Gerenciamento de Fontes

| Endpoint | Método | Propósito |
|----------|--------|-----------|
| `/catalog/sources` | POST | Adicionar uma nova fonte customizada |
| `/catalog/sources/{id}` | DELETE | Remover uma fonte |

### Instalação Remota

| Endpoint | Método | Propósito |
|----------|--------|-----------|
| `/marketplace/install-remote/{id}` | POST | Inicia instalação assíncrona |
| `/marketplace/install-jobs/{job_id}` | GET | Consulta o progresso do job |

---

## CLI: `techforge catalog`

```bash
# Listar módulos disponíveis
techforge catalog list

# Buscar
techforge catalog search <term>

# Mostrar um módulo
techforge catalog show <module_id>

# Listar fontes configuradas
techforge catalog sources

# Construir um índice (para gerar `index.json`)
techforge catalog build-index <source_dir> --output <catalog_dir>
```

---

## Limitações Conhecidas (Fase 11)

1. **`CustomCatalogProvider` só suporta GitHub Contents API.**
   - GitHub, GitLab (com API compatível), outros hosts Git com suporte a Contents API.
   - GitLab self-hosted ou Gitea exigem um adapter (Fase 18.1).

2. **Sem rollback completo em falha de atualização.**
   - Se a instalação falhar parcialmente, os arquivos já instalados permanecem.
   - A versão anterior NÃO é restaurada automaticamente.
   - Mesmo comportamento da instalação local (decisão da Fase 4, mantida aqui).

3. **Sem polling em segundo plano para atualizações.**
   - Notificações de "novo módulo disponível" e "atualização disponível" só aparecem quando
     o usuário abre a página do Catálogo.
   - Nenhum job agendado em background checando novos módulos.
   - Adequado para instância única/desktop; fases futuras podem adicionar polling no servidor.

4. **Favoritos são somente locais (sem sincronização, sem avaliação).**
   - Marcação pessoal de favorito ★; sem "4,5 estrelas de 100 pessoas".
   - Sem armazenamento em nuvem nem sincronização entre dispositivos (fase de Servidor Central trata disso).

---

## Para Autores de Módulos

### Publicando no Catálogo Oficial

1. Contribua seu módulo para o [Tech.Forge.Modules](https://github.com/julianscunha/Tech.Forge.Modules)
   — veja o [CONTRIBUTING.md](https://github.com/julianscunha/Tech.Forge.Modules/blob/main/CONTRIBUTING.md)
   de lá pro passo a passo completo.
2. Envie um PR com sua pasta `submissions/<id>/` (transitória — nunca em
   `modules/`, que é gerenciada só pela automação do repositório).
3. O CI valida, e depois do merge constrói o `.mod` (aninhado em
   `modules/<id>/<id>-<versão>.mod`, preservando versões anteriores) e
   regenera o `index.json`.
4. Merge → disponível na próxima sincronização da plataforma.

### Publicando em Catálogo Customizado

1. Crie um repositório GitHub (ou qualquer host git com Contents API).
2. Adicione `modules/<id>/manifest.yaml` + arquivos-fonte.
3. Configure a URL no TechForge ("Adicionar Fonte Customizada").
4. Seus módulos aparecem imediatamente.
5. Sem etapa de aprovação; você controla atualizações e remoção.

---

## Notas de Arquitetura

- **Agregador singleton:** instância de `CatalogAggregator` por plataforma (compartilhada entre requisições).
- **Providers sem estado:** cada `RepositoryProvider` é stateless; todo estado (cache, rastreamento de disponibilidade) vive no agregador.
- **Sessão de banco por requisição:** criação de notificação requer acesso ao DB; passada através de `_fetch_source()`.
- **Sem hot-reload da lista de providers:** alterar a configuração de fonte só é refletido na próxima chamada de `list_all_available()` (não é retroativo).

---

Veja também:
- [Module Lifecycle](module-lifecycle.md)
- [Module Trust](module-trust.md)
- [Package Manager](package-manager.md)
