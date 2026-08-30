# Changelog

Todas as mudanças relevantes da plataforma Core do TechForge são documentadas aqui. Formato baseado em [Keep a Changelog](https://keepachangelog.com/) e [Semantic Versioning](https://semver.org/) — seções permitidas por versão: `Added`, `Changed`, `Fixed`, `Deprecated`, `Removed`, `Known Issues`.

Este changelog cobre o **Core** apenas. Cada módulo mantém seu próprio `CHANGELOG.md` na raiz do módulo — não misturar releases de módulo com releases do Core. Padrão de processo de release documentado em [`docs/developer-center/core/quality-and-release.md`](docs/developer-center/core/quality-and-release.md).

## [Unreleased]

### Added
- **Observability, Telemetry & Diagnostics** — logs estruturados (JSON-lines) com rotação/retenção configurável; redação automática de dados sensíveis por padrão de chave; métricas operacionais (execuções, falhas, dependências); Error Registry e Execution History persistidos com códigos de diagnóstico estáveis; correlação de falha entre erro, módulo, execução e dependências; página `/diagnostics` e Dashboard incrementado (uso de recursos, módulo mais pesado, eventos críticos recentes, cards reorganizáveis); export de relatório de diagnóstico e Support Bundle sanitizado (JSON/TXT/ZIP); `techforge diagnostics`/`techforge modules diagnostics`/`techforge logs --follow`.

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
