# Plano — Fase 16: Desktop Distribution & User Experience

> Spec: docs/phases/16-Fase-16-Desktop-Distribution-User-Experience.md
> Pré-requisito: Fase 15 (Platform Quality) ✅ fechada, Fase 14 (Observability) ✅ fechada.
> Fase 13 (Central Server Multi-User) segue adiada — nada aqui assume servidor central.

## Premissas validadas (investigação de código real)

1. `launcher/` já cobre grande parte do fluxo de startup (§4/§5): valida
   ambiente → sobe backend → `wait_backend()` via poll em
   `/api/v1/platform/status` → serve frontend estático em modo desktop
   (sem Node) → abre browser padrão. Não existe endpoint `/ready`
   dedicado — o launcher usa `/platform/status` como proxy.
2. Single instance (§6) já detecta PID vivo + porta ocupada
   (`_port_in_use`, corrigido na Fase 6), mas ao encontrar instância
   viva só avisa por texto — não reabre/foca a aplicação.
3. Módulo com falha já não derruba o boot (§17) — resolvido desde a
   Fase 4/9, nada a fazer aqui.
4. `BASE_DIR` (`app/core/settings.py`) é a raiz do repositório — DB,
   logs e `modules/installed/` vivem todos dentro dela. Não existe
   separação Application Install vs User Data (§11-13). É a base de
   quase todo o resto da fase (paths de instalador, update, uninstall,
   repair dependem disso).
5. `GET /api/v1/platform/health` (Fase 1) e `GET /api/v1/system/version`
   (Fase 15) existem; `/ready` como conceito distinto de `/health` não.
6. Não existe Safe Mode em nenhuma camada (CLI, backend, launcher).
7. `devmode.ts` (frontend) hoje é um toggle local só da página Módulos
   — não é um "modo de app". Nenhuma camada do backend distingue
   User Mode de Developer Mode.
8. Não existe packaging de backend (PyInstaller, embeddable Python) nem
   instalador Windows (Inno Setup/MSI/NSIS) — packaging real da fase
   parte do zero.
9. Module Trust / integrity manifest (Fase 10) já existe e é reutilizável
   para `techforge repair-check` (verificar arquivos do Core sem
   reinventar hashing).

## Decisões arquiteturais (confirmadas com o usuário antes do plano)

1. **Application Window: browser do sistema**, não WebView Shell
   (`pywebview`/Electron/Tauri). Mantém a distribuição leve — zero
   dependência nova, zero binário extra — conforme a própria spec (§8)
   recomenda quando isso é suficiente. "Focar instância existente"
   (§6) resolvido reabrindo a mesma URL no browser padrão, sem shell
   nativo.
2. **Backend packaging: PyInstaller `--onedir`**, não `--onefile`.
   Onefile descompacta pra temp a cada start (mais lento, mais
   sensível a antivírus corporativo). Escopo desta fase: documentar a
   estratégia + script de build reproduzível; o instalador Windows
   completo (Inno Setup/MSI) fica fora do fechamento — ver "Fora de
   escopo" abaixo.
3. **Safe Mode: global, não seletivo.** `TECHFORGE_SAFE_MODE=true`
   (via `techforge start --safe-mode` / `techforge safe-mode`) faz o
   `ModuleLoader` pular o carregamento de `entry_backend` de todos os
   módulos — registry populado só para leitura/diagnóstico (aparecem
   como "não carregado, safe mode"). Dashboard/Diagnostics continuam
   acessíveis; usuário desativa/remove o módulo problemático e reinicia
   normal. Sem lógica de "detectar automaticamente o módulo culpado".
4. **Paths oficiais por SO: `platformdirs`** (dependência nova, pequena,
   padrão de facto). Resolve install-dir (código, read-only em
   produção) vs user-data-dir (`%LOCALAPPDATA%\TechForge` no Windows) —
   substitui `BASE_DIR` fixo na raiz do repo. `ModulePaths` (Fase 12)
   continua cuidando de paths *dentro* de cada módulo, sem mudança.
5. **Developer Mode: promovido de toggle de página pra modo de app.**
   Mesmo `devmode.ts`, mas lido em mais lugares (Settings/Sidebar, não
   só ModulesPage) e passa a gatear: exibição de paths reais
   (install-dir/user-data-dir), acesso a logs recentes na UI, botão de
   reload/rescan de módulos. Reaproveita APIs de diagnóstico já
   existentes da Fase 14 — nenhuma API nova de dados, só exposição
   condicional na UI + os poucos endpoints (`/ready`, reload) que este
   plano já cria por outro motivo.
6. **Fora de escopo nesta fase — decisão explícita, mesmo padrão da
   Fase 13** (registrar em `tasks/phase-audit.md` ao fechar):
   - Instalador Windows GUI completo (Inno Setup/MSI) — só o script
     PyInstaller documentado.
   - Update flow do Core (§26/§27) além do "arquiteturalmente
     previsto" — a separação de paths (decisão 4) já cobre o critério
     de aceitação #19 (user data preservado ao reinstalar).
   - Uninstall com opções formais (§31) e Repair "restaurar
     componentes" (§33) além de `repair-check` (só verificação).
   - Proxy corporativo (§29) além de confirmar/documentar que nada usa
     lib que assuma internet direta (já é verdade hoje).
   - Packaging validation em clean machine real (§44) — testável só
     depois de existir instalador; fica como próximo incremento.

## Novo pacote / arquivos (estimativa)

```
core/backend/app/core/paths.py              # platformdirs: install_dir / user_data_dir
core/backend/app/core/settings.py           # BASE_DIR derivado de paths.py, não hardcoded
core/backend/app/api/routes/platform.py     # GET /ready (novo, distinto de /health)
core/backend/app/module_engine/loader.py    # skip de entry_backend sob TECHFORGE_SAFE_MODE
cli/techforge_cli/commands/safe_mode.py     # techforge safe-mode
cli/techforge_cli/commands/repair.py        # techforge repair-check
launcher/techforge_launcher/launcher.py     # /ready probe, focus-existing-instance, erro amigável
core/frontend/src/store/devmode.ts          # sem mudança de shape, só mais consumidores
core/frontend/src/pages/SettingsPage.tsx    # seção Developer Mode (paths, logs, reload)
docs/user-guide/, docs/it-guide/, docs/developer-guide/   # novos (§40)
docs/developer-center/core/desktop.md       # §41
```

## Slices

### Slice 1 — Paths oficiais por SO (TDD) — §11/§12/§13
- `platformdirs` como dependência nova.
- `app/core/paths.py`: `install_dir()` (raiz do código) e
  `user_data_dir()` (`%LOCALAPPDATA%\TechForge` no Windows).
- `settings.py` deriva `DATABASE_URL`, `MODULES_INSTALLED_PATH`,
  caminho de logs a partir de `user_data_dir()` em vez de `BASE_DIR`
  fixo — com fallback para o comportamento atual em modo dev
  (variável de ambiente ou detecção de `.git`/`pyproject.toml` na
  árvore, pra não quebrar `cd core/backend && pytest`).

**Aceite:** suíte completa roda sem mudança de comando; um teste novo
confirma que, fora do dev tree (simulado via monkeypatch), os paths
resolvem para o diretório de dados do usuário, não para a raiz do
código.

### Slice 2 — `/ready` + erro de startup amigável (TDD) — §15/§35/§42
- `GET /api/v1/platform/ready`: probe leve e determinístico (DB
  acessível + registry populado), distinto de `/health` (mais amplo,
  já existente).
- Launcher: ao falhar o startup, mostra mensagem + diagnostic code
  (reaproveita catálogo de códigos da Fase 14, ex. `TF-STARTUP-001`)
  em vez de string genérica; nunca mostra stack trace por padrão.

**Aceite:** `/ready` retorna 200 só quando DB+registry estão prontos;
teste simula falha de backend e confirma que o launcher reporta código
+ mensagem amigável, não "Connection refused".

### Slice 3 — Single instance: focus existing (TDD) — §6
- `already_running()` passa a reabrir a URL no browser padrão em vez
  de só logar aviso.

**Aceite:** segunda chamada de `techforge start` com instância viva
não sobe segundo backend e reabre a URL (verificado via mock de
`webbrowser.open`).

**Checkpoint 1:** suíte completa + `techforge start`/`stop`/`status`
manual, confirmando paths novos em uso.

### Slice 4 — Safe Mode (TDD) — §16/§18
- `TECHFORGE_SAFE_MODE` env var; `ModuleLoader.scan_installed()` pula
  `entry_backend` quando ativa, preenchendo o registry só para leitura.
- `techforge safe-mode` (CLI) seta a env var e chama `start()`.
- Indicador visual no Dashboard quando o backend reporta safe mode
  ativo (via `/platform/status`).

**Aceite:** com safe mode, nenhum módulo monta rota própria, mas
aparecem no registry como bloqueados; desativar/remover módulo
funciona normalmente; reinício sem a flag volta ao normal.

### Slice 5 — `techforge repair-check` (TDD) — §33
- Reusa integrity manifest / hashing da Fase 10 (`app/module_trust/`)
  para verificar arquivos do Core (não só módulos) contra um manifesto
  gerado no build.
- Só verifica e reporta — não tenta restaurar nada automaticamente.

**Aceite:** alterar um arquivo do Core após gerar o manifesto faz
`repair-check` reportar divergência; instalação íntegra reporta OK.

**Checkpoint 2:** suíte completa.

### Slice 6 — Developer Mode real (frontend) — §38
- Promove `devmode.ts` de toggle local pra modo de app: novo controle
  em Settings (além do já existente em Módulos, que continua).
- Quando ativo: mostra paths reais (install-dir/user-data-dir via
  endpoint novo ou já exposto), acesso a logs recentes (reusa API da
  Fase 14), botão de reload/rescan de módulos.

**Aceite:** `npm run lint`/`npm run build` limpos; com Developer Mode
desligado (padrão), nenhuma dessas seções aparece.

### Slice 7 — Backend packaging (documentado) — §10
- Script de build PyInstaller `--onedir` (`scripts/build-backend.ps1`
  ou equivalente) gerando executável standalone do backend.
- Documentar decisão e limitações (rebuild a cada dependência nova,
  tamanho do artefato) — sem instalador GUI.

**Aceite:** script roda localmente e produz um `.exe` que sobe o
backend sem `.venv` ativo.

**Checkpoint 3:** suíte completa + fluxo manual do "Regra final" do
spec adaptado ao escopo (start pelo atalho, confirmar backend, ready,
abrir módulo, minimizar menu, fechar, reiniciar, segunda instância,
Safe Mode, falha de módulo, offline, gerar diagnóstico).

### Slice 8 — Documentação + Developer Center + AI Context — §40/§41
- User Guide, IT/Deployment Guide, Developer Guide (§40).
- Developer Center: Desktop Application Architecture, Launcher
  Lifecycle, Desktop Paths, Safe Mode, Startup Troubleshooting,
  Development vs Distribution (§41).
- AI Context: diferença entre development environment e production
  desktop distribution.

### Slice 9 — Fechamento
- `tasks/phase-audit.md` atualizado (Fase 16 fechada, itens adiados
  listados como Known Issues, mesmo padrão da Fase 13/12).
- `tasks/phase-16-report.md` consolidado.
- Auditoria final contra os 30 critérios de aceitação do spec §48,
  marcando explicitamente quais foram cobertos e quais foram adiados
  por decisão consciente.

## Known Issues esperados (documentar no report, não bloquear a fase)

- Instalador Windows GUI (Inno Setup/MSI) não implementado — só script
  de build do backend. Packaging validation (§44) em clean machine
  real fica pendente até existir instalador.
- Update flow do Core (§26/§27), Uninstall formal (§31) e Repair
  "restaurar componentes" (§33) reduzidos ao mínimo arquiteturalmente
  necessário — sem fluxo de usuário completo nesta fase.
- Proxy corporativo (§29): documentado que nada assume internet
  direta hoje; sem tela de configuração.
