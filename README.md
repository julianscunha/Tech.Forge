# TechForge — Fase 1: Core Platform

Plataforma corporativa modular para execução de ferramentas técnicas e comerciais via plugins.

---

## Estrutura do Projeto

```
techforge/
├── core/
│   ├── backend/          # FastAPI + SQLAlchemy + SQLite
│   └── frontend/         # React + TypeScript + Vite + TailwindCSS
├── sdk/
│   ├── python/           # SDK Python (stub Phase 2)
│   └── frontend/         # SDK TypeScript (stub Phase 2)
├── cli/                  # CLI (Phase 4)
├── marketplace/          # Marketplace (Phase 3)
├── modules/
│   ├── repository/       # Módulos disponíveis para download
│   └── installed/        # Módulos instalados ativos
├── shared/               # Contratos e tipos compartilhados
├── docs/                 # Documentação técnica
├── config/               # .env e configurações
└── logs/                 # Logs da plataforma
```

---

## Iniciando o Projeto

### Backend

```bash
cd core/backend
pip install -r requirements.txt
cp ../../config/.env.example ../../config/.env
python run.py
# API disponível em http://127.0.0.1:8000
# Docs em http://127.0.0.1:8000/api/docs
```

### Frontend

```bash
cd core/frontend
npm install
npm run dev
# App disponível em http://localhost:5173
```

---

## Decisões Arquiteturais

### Por que FastAPI + SQLAlchemy async?
- Permite migração transparente SQLite → PostgreSQL via troca de `DATABASE_URL`
- Async nativo prepara para múltiplos módulos rodando concorrentemente

### Por que Zustand?
- Estado global leve sem boilerplate Redux
- Persist middleware para salvar tema e estado da sidebar no localStorage

### Por que React Router v6 com Outlet?
- O `<AppShell>` envolve todas as rotas via `<Outlet />`
- Em Phase 2, o Plugin Loader injeta rotas de módulos dinamicamente neste mesmo shell

---

## Pontos de Extensão para Fases Futuras

### Phase 2 — Plugin Loader
- `core/frontend/src/AppRouter.tsx` — comentário `PLUGIN LOADER HOOK` indica onde adicionar `<Route path="modules/:moduleId/*">`
- `core/frontend/src/lib/navigation.ts` — seção `id: 'modules'` recebe `NavItem[]` injetados dinamicamente
- `core/backend/app/api/routes/modules.py` — endpoint `POST /modules` registra módulo; em Phase 2 dispara `install()` e `enable()`
- `core/backend/app/services/registry.py` — `ModuleService` será estendido com métodos de lifecycle

### Phase 3 — Marketplace
- `marketplace/` — diretório reservado para o servidor de distribuição
- `core/frontend/src/pages/MarketplacePage.tsx` — placeholder pronto para implementação
- Endpoint `/api/v1/modules` já aceita `checksum` e `signature` no payload

### Phase 4 — CLI
- `cli/` — diretório reservado
- `sdk/python/techforge_sdk.py` — interface do SDK que a CLI utilizará

### Phase 5 — Segurança
- Campos `signature` e `checksum` já existem no modelo `Module`
- `StatusBadge` já suporta estado `error` para alertas de assinatura inválida

---

## API Endpoints (Phase 1)

| Method | Path | Descrição |
|--------|------|-----------|
| GET | `/api/v1/platform/status` | Status e contadores da plataforma |
| GET | `/api/v1/categories` | Lista categorias registradas |
| POST | `/api/v1/categories` | Cria categoria |
| GET | `/api/v1/categories/:slug` | Detalhe de categoria |
| GET | `/api/v1/modules` | Lista módulos instalados |
| POST | `/api/v1/modules` | Registra módulo |
| GET | `/api/v1/modules/:id` | Detalhe de módulo |
