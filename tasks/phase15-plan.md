# Plano — Fase 15: Platform Quality, Testing & Release Engineering

Aprovado em 2026-08-30. Spec: `docs/phases/15-Fase-15-Platform-Quality-Testing-Release-Engineering.md`.

## Premissas validadas contra o código real

- ~600 testes existem, organizados por fase (`test_phase11_*.py`), não por nível. Não há test de arquitetura nem contract test dedicado.
- Não existe `.github/workflows/` — nenhum CI hoje.
- `PLATFORM_VERSION="1.0.0"` já é fonte única (`app/core/settings.py`). `packaging` já é dependência (Fase 12) — reusar `packaging.version` para SemVer, sem nova lib.
- `requirements.txt` já pina exato (`==`) tudo; frontend já tem `package-lock.json` — §29/§30 já satisfeitos na prática.
- `techforge validate-module` e `DocCompletenessChecker` (Fase 7) existem e serão reaproveitados (§8/§9), não recriados.
- **Zero config de lint/format/type-check no backend** (nenhum `pyproject.toml`/`.ini`/`.cfg` de tooling). Gap real a fechar no Slice 6.
- `eslint` não é devDependency do frontend (`npm run lint` quebra) — gap pré-existente documentado na Fase 12, fechado aqui (§18/§31 exigem lint no pipeline).

## Decisões arquiteturais confirmadas (2026-08-30)

1. **Não reorganizar/renomear os ~600 testes existentes.** Registrar markers pytest (`unit`/`integration`/`contract`/`e2e`/`smoke`/`regression`) via config; aplicar markers aos arquivos existentes de forma mecânica (script, não reescrita manual); testes novos desta fase já nascem marcados.
2. **CI = GitHub Actions** (`.github/workflows/ci.yml`), rodando os mesmos comandos já usados manualmente. Sem serviço pago, sem infra nova.
3. **Architecture tests via `ast-grep`**, não `import-linter` — ferramenta já mandatória no projeto, evita dependência nova.
4. **Changelog**: `CHANGELOG.md` na raiz (Core); módulos usam `CHANGELOG.md` próprio na pasta do módulo.
5. **Fora de escopo** (§48 do próprio spec + racional das Fases 13/18.1-20 adiadas): CI comercial, deploy automático, GitOps/Kubernetes, cobertura % arbitrária, release automático sem aprovação, UI de catálogo dedicada para pre-release channels (sem usuários externos ainda — mecanismo pronto, sem UI).
6. **Static quality Python**: adotar `ruff` (lint + format + import order em uma ferramenta só, evita empilhar black+flake8+isort). Type-checking (`mypy`) fica como baseline leve (rodar sobre o código novo desta fase, não retrofit de tudo) — decisão a confirmar durante o Slice 6 se o baseline for muito ruidoso.

## Slices

1. **Test level markers** — registrar markers em `pytest.ini` (`unit, integration, contract, e2e, smoke, regression`) com `--strict-markers`; aplicar aos ~600 testes existentes (script de categorização, não handwritten).
2. **Test fixtures centralizadas** (§13) — `tests/fixtures/` com módulos válidos/inválidos, dependências, incompatibilidades, packages, migrations, doc failures; consolidar duplicação já espalhada.
3. **Architecture tests** (§19/§20) — regras via `ast-grep` rodadas como teste pytest: módulo não importa interno do Core, Application não é dependência de Service, Service não depende de Application, módulo não acessa DB de outro módulo.
4. **Contract tests de serviço** (§7) — validar Service Contract declarado (Fase 8) vs. comportamento real.
5. **Compatibility matrix tests** (§21) — Core version × Module version requirement, via `packaging.version`.
6. **Static quality** (§16/17/18) — `ruff` configurado (backend), `eslint` adicionado como devDependency (frontend, fecha gap conhecido).
7. **Release versioning** (§23/24/25) — helper SemVer, `GET /api/v1/system/version`, `techforge version`.
8. **Changelog & Release Notes** (§26/27) — `CHANGELOG.md` raiz + template, validador de seções (Added/Changed/Fixed/Deprecated/Removed/Known Issues).
9. **Release Readiness Report** (§36/37) — serviço agregador (tests/build/module validation/docs/version/migration/diagnostic) + `GET /api/v1/release/readiness` + `techforge release-check`.
10. **Module quality/release-readiness** (§44/45/46) — `GET /modules/{id}/quality`, `/modules/{id}/release-readiness`, `techforge modules quality|release-check`.
11. **Build artifacts & integrity** (§28/29/41) — metadata (version+checksum+build info) para backend package/frontend build/module package.
12. **Pre-release channels & rollback readiness** (§34/35/38/39/40) — canais `stable/beta/development` no manifest (mecanismo, sem UI dedicada), Known Issues registry, nota de rollback (Desktop simples, módulo via Package Manager já existente).
13. **CI pipeline + smoke + e2e crítico** (§11/12/31/32) — `.github/workflows/ci.yml`; smoke test (start→health→storage→discover→activate→execute); e2e crítico (catalog→install→validate→activate→execute→deactivate→remove), consolidando fluxos já cobertos em fases anteriores.
14. **Developer Center + AI Context + fechamento** (§43/44 dashboard opcional/29) — docs de estratégia de teste, release checklist; AI Context com Definition of Done; auditoria final contra os 34 critérios §49; `phase-audit.md` + `README.md`.

## Known issues a monitorar
- Retrofit de markers em 600 testes é mecânico — risco de categorização imprecisa; aceitável pois não muda comportamento, só metadata.
- `mypy` pode gerar ruído alto no primeiro run — decisão de escopo (baseline vs. full) adiada para o Slice 6.
