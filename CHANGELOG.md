# Changelog

Todas as mudanças relevantes da plataforma Core do TechForge são documentadas aqui. Formato baseado em [Keep a Changelog](https://keepachangelog.com/) e [Semantic Versioning](https://semver.org/) — seções permitidas por versão: `Added`, `Changed`, `Fixed`, `Deprecated`, `Removed`, `Known Issues`.

Este changelog cobre o **Core** apenas. Cada módulo mantém seu próprio `CHANGELOG.md` na raiz do módulo — não misturar releases de módulo com releases do Core. Padrão de processo de release documentado em [`docs/developer-center/core/quality-and-release.md`](docs/developer-center/core/quality-and-release.md).

## [Unreleased]

### Added
- **Observability, Telemetry & Diagnostics** — logs estruturados (JSON-lines) com rotação/retenção configurável; redação automática de dados sensíveis por padrão de chave; métricas operacionais (execuções, falhas, dependências); Error Registry e Execution History persistidos com códigos de diagnóstico estáveis; correlação de falha entre erro, módulo, execução e dependências; página `/diagnostics` e Dashboard incrementado (uso de recursos, módulo mais pesado, eventos críticos recentes, cards reorganizáveis); export de relatório de diagnóstico e Support Bundle sanitizado (JSON/TXT/ZIP); `techforge diagnostics`/`techforge modules diagnostics`/`techforge logs --follow`.
- **Desktop Runtime Resilience** — paths oficiais por SO (diretório de instalação vs. diretório de dados do usuário); `GET /ready` com erro de startup amigável no launcher; nova instância foca a janela existente em vez de só avisar; Safe Mode global (Core mínimo, nenhum módulo carregado); `techforge repair-check`; Developer Mode real (paths + reload de módulos); empacotamento do backend via PyInstaller onedir.
- **Security, Integrity & Module Trust (Hardening)** — resource limits contra zip bomb na extração de pacotes; assinatura Ed25519 real; Publisher Registry real; `GET/POST /api/v1/security/*` + CLI de segurança; audit events de segurança via EventBus; secret lifecycle explícito com redação de authorization; SBOM mínimo (`GET /modules/{id}/sbom`); Security UI no Developer Center; aviso de Trust Level agora chega de fato ao usuário no install/update (antes era resolvido mas nunca notificado).
- **`sdk.database`** — persistência real via SQLite (um arquivo isolado por módulo), substituindo o mock in-memory anterior (ver ADR-007).
- **`techforge update`** — self-update do Core via `git pull` (deps + migrations + build do frontend), com checagem de versão contra a release mais recente do GitHub; mostra as release notes e avisa explicitamente que a plataforma será parada/reiniciada antes de pedir confirmação. Rodapé da Sidebar mostra a versão real da instalação e um badge discreto "Update disponível" quando há versão nova (`GET /system/update-check`).
- Endpoint de invocação entre módulos (`services.invoke`) + `techforge_sdk.services.invoke()`.
- Abas de múltiplos módulos abertas simultaneamente (module tab strip).
- Filtro por módulo na seção "Módulos Instalados" do Developer Center.
- Seletor de fuso horário em Configurações (exibição, sem alterar dados armazenados).

### Changed
- Header e Breadcrumb mesclados numa única linha; botão de ajuda no header vira ícone-only.
- Dashboard aproveita melhor a largura da tela em monitores grandes; filtros e layout do Marketplace > Catálogo reorganizados.
- Documentação pública reorganizada: `docs/phases/` e `tasks/` removidos (conteúdo migrado para `docs/limitations.md` e `docs/roadmap.md`); referências internas de fase/slice removidas dos documentos voltados ao público.

### Fixed
- Rotas de módulo não respondiam em modo Desktop (bug crítico).
- Botão "Atualizar" do Catálogo (fonte remota) sempre falhava, ou não refletia um módulo recém-publicado.
- Notificação de instalação via Catálogo remoto dizia "instalado" mesmo quando era uma atualização de módulo já instalado.
- Contador de módulos do Dashboard divergia da realidade; status mostrava Launcher/Frontend `STOPPED` com a plataforma saudável.
- Notificação desaparecia da lista assim que marcada como lida (deveria só perder o destaque de não-lida).
- Launcher não detectava processos órfãos já ocupando a porta do backend.
- Reinstalar um Service Module sem reiniciar a plataforma deixava o contrato em `FAILED` permanentemente.
- `sdk.database` (`DatabaseSDK`) travava para sempre quando usado a partir de event loops `asyncio` diferentes no mesmo processo.
- Corrida real que podia vazar uma notificação de segurança de teste para o banco de dados de produção.
- Seção "SDK Frontend" do Developer Center sempre vazia; README/overview de módulo só era encontrável pela busca, sem link de volta.
- CLI: `UnicodeEncodeError` no console padrão do Windows (cp1252, glifos Unicode do `rich`).

## [1.0.0] - 2026-08-30

Primeira release estável do Core. Plataforma modular local-first completa: instalar, executar, configurar e documentar módulos plugáveis numa única aplicação Desktop leve.

### Added
- **Core & Module System** — FastAPI + React/TS + SQLite; manifest declarativo (`manifest.yaml`) com validação de estrutura, versão e compatibilidade; carregamento dinâmico de módulos com navegação gerada por metadados.
- **Marketplace & Package Manager** — ciclo completo instalar → ativar → desativar → atualizar → remover, com rollback automático em falha; empacotamento `.mod` (ZIP + checksum SHA-256).
- **Developer Center & Documentation Engine** — indexação e busca de documentação, contratos de API tipados, checklist de completude de documentação, export de contexto para IA.
- **Launcher & Runtime** — inicialização com um único comando (`techforge start/stop/status`), modo Desktop leve (sem processo Node separado), instância única, shutdown ordenado.
- **Service Registry & Dependency Governance** — descoberta de serviços por contrato, invocação tipada entre módulos, grafo de dependências com detecção de ciclos.
- **Module Runtime & Execution** — lifecycle hooks reais (`enable`/`disable`/`health_check`), contexto de execução isolado por módulo.
- **Security, Integrity & Module Trust** — verificação de integridade por arquivo, registro de publishers, níveis de confiança.
- **Marketplace Distribution** — catálogo multi-fonte (oficial + GitHub customizado), instalação remota, notificações de disponibilidade.
- **Configuration & Persistence** — migrations versionadas (Alembic), configuração de módulo tipada e validada, cofre de segredos nativo do SO (`keyring`), armazenamento key-value isolado por módulo.
- **Quality & Release Engineering** — suíte de testes por nível (unit/integration/contract/e2e/smoke), CI automatizado, relatório de prontidão de release (`techforge release-check`), verificação de qualidade por módulo (`techforge modules quality`).

### Known Issues
- Configuração de módulo não suporta valores em lista/array — só tipos escalares (string/integer/float/boolean).
- Cofre de segredos depende do backend nativo do sistema operacional (`keyring`); sem fallback definido para Linux sem sessão gráfica.
- Sem suporte a múltiplos usuários simultâneos ou servidor central — a plataforma é single-user, otimizada para uso local em uma máquina.
- `hello_world` (módulo de referência) ainda distribui frontend como código-fonte não compilado; não afeta módulos reais publicados no catálogo.
