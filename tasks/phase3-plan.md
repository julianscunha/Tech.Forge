# Plano — Fase 3: Module System (fechamento das lacunas)

> Spec: docs/phases/03-Fase-03-Module-System.md
> Auditoria de origem: tasks/phase-audit.md — Fase 3 está ⚠️ 11/16.
> O fluxo Discovery→Validation→Registry→Loader→API→UI JÁ funciona (192+ testes).
> Este plano fecha apenas as lacunas reais.

## Premissas validadas no código

1. ✅ CLI tem create/validate/package-module e platform start/stop/status, mas NÃO `modules list/show/validate`
2. ✅ `cli/techforge_cli/validators/module_validator.py` duplica lógica de validação fora do Core (spec §19 veda: "não duplicar validações exclusivamente para CLI")
3. ✅ `ModuleHost.tsx` existe e rota ativa, mas renderiza host estático — `entry_frontend` não é carregado dinamicamente (comentário no próprio arquivo)
4. ✅ Estados do registry: INSTALLED/DISABLED/INVALID/INCOMPATIBLE vs spec §9 DISCOVERED/VALIDATED/INVALID/REGISTERED/FAILED — cobertura funcional superior; MANTER os nossos (decisão arquitetural já tomada em fases 4–6 que dependem deles)
5. ✅ APIs /modules e /registry/navigation existentes cobrem spec §17

## Slices

### Slice 1 — CLI `techforge modules` reaproveitando o Core (spec §19)
- Novo grupo `cli/techforge_cli/commands/modules.py`:
  - `modules list` — via HTTP GET /api/v1/modules quando plataforma no ar; fallback: scan local de modules/installed/ usando o ManifestParser do Core (sys.path para core/backend), sem reimplementar validação
  - `modules show <id>` — detalhe (mesma fonte)
  - `modules validate [path]` — delega ao validator do Core (`app.module_engine.validator`), substituindo a chamada interna à lógica duplicada
- `validate_module_cmd` passa a usar o validator do Core como engine; o `module_validator.py` da CLI fica apenas com checks de estrutura de arquivos (contratos entry_backend/frontend) que são específicos de empacotamento
- Testes CLI existentes atualizados + novos para `modules list/show/validate`

**Aceite:** nenhum campo obrigatório de manifest validado em código duplicado; comandos funcionam contra plataforma parada (scan) e ligada (API).

### Slice 2 — Dynamic import de entry_frontend (spec §11/§24.8-9)
- Contrato: módulo compila frontend para UMD/ESM em `frontend/dist/main.js`; manifest declara `entry_frontend`
- Backend: endpoint GET /api/v1/modules/{id}/assets/{path} servindo arquivos do dir instalado (sandbox: resolve dentro do diretório do módulo, content-type por extensão)
- Frontend ModuleHost: dynamic import() do asset URL → monta componente exportado; fallback visual amigável se ausente/falha
- hello_world ganha frontend mínimo real exportando componente, validando o fluxo completo

**Aceite:** módulo application renderiza DENTRO do App Shell (sem nova aba), falha de carga não derruba nada.

### Slice 3 — Docs + relatório + browser E2E
- docs/developer-center/reference/manifest.md: documentar entry_frontend/assets contract
- README: seção "Module Lifecycle" atualizada com dynamic loading
- Browser test: instalar hello_world com UI real, navegar pelo menu, renderizar dentro do shell, verificar console limpo
- tasks/phase-03-report.md no formato da spec + auditoria → Fase 3 ✅

## Fora de escopo (spec §23)
Marketplace remoto, dependências, Service Registry, sandbox, assinatura.

## Ordem
Slice 1 (TDD) → Slice 2 (TDD) → Slice 3 → commit/push por slice.
