# Contribuindo com o TechForge

Obrigado pelo interesse em contribuir. Este guia cobre as duas frentes de
contribuição possíveis, setup local, e o que esperamos antes de um PR.

## Módulos vs. Core

A grande maioria das contribuições deveria ser um **módulo** (`.mod`), não
uma mudança ao Core. O princípio do projeto é: o Core não contém lógica de
negócio — tudo de domínio vive em módulos instalados separadamente.

- **Quer adicionar uma funcionalidade de domínio** (integração com um
  serviço, um relatório, uma ferramenta)? Crie um módulo. Siga o
  [Guia Completo de Desenvolvimento de Módulos](docs/developer-center/guides/development-guide.md).
- **Acha que o Core precisa mudar**? Antes de abrir um PR, pergunte "isto
  poderia ser um módulo independente?" (ver
  [`docs/roadmap/long-term-governance.md`](docs/roadmap/long-term-governance.md)).
  Se a resposta for sim, prefira o módulo. Mudanças reais ao Core exigem
  justificativa arquitetural explícita — abra uma issue de discussão antes
  de investir tempo escrevendo o código.

## Setup local

```bash
# Backend — sempre a partir de core/backend/ (DB path e imports dependem do CWD)
cd core/backend
python -m venv .venv
.venv/Scripts/pip install -e .
.venv/Scripts/python.exe run.py    # uvicorn em 127.0.0.1:8000

# Frontend — a partir de core/frontend/
cd core/frontend
npm install
npm run dev                         # vite :5173

# CLI
pip install -e cli
techforge --help
```

Veja também [`docs/developer-center/guides/core-development-setup.md`](docs/developer-center/guides/core-development-setup.md)
para o setup completo do ambiente de desenvolvimento do Core.

## Antes de abrir um PR

```bash
cd core/backend && .venv/Scripts/python.exe -m pytest tests -q
cd core/frontend && npm run lint && npm run build
```

Se sua contribuição for um módulo, valide também a documentação dele:

```
GET /api/v1/docs/completeness/<seu-modulo>
```

deve retornar sem pendências.

## Commits e PRs

Não há um padrão rígido de formato de commit (não usamos Conventional
Commits) — mas cada commit deve ter uma mensagem clara em português
descrevendo a mudança, geralmente prefixada por um tipo curto (`feat:`,
`fix:`, `docs:`, `refactor:`, `test:`). Prefira commits pequenos e
atômicos a um único commit gigante.

No PR, descreva o que mudou e por quê, não só o quê — se for uma mudança
ao Core, inclua a justificativa arquitetural mencionada acima.

## Código de conduta

Este projeto segue o [Código de Conduta](CODE_OF_CONDUCT.md). Ao
participar, espera-se que você o respeite.

## Segurança

Encontrou uma vulnerabilidade? Não abra uma issue pública — veja
[`SECURITY.md`](SECURITY.md).
