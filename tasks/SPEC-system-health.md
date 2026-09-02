# Spec: System Health — upgrade para módulo real de diagnóstico e otimização

## Objetivo

Transformar os dois módulos de referência `system_information_service` (Service)
e `system_health_check` (Application) — hoje exemplos mínimos, só stdlib — no
primeiro módulo de fato utilizável do catálogo TechForge: um dashboard de
saúde do sistema que lê hardware/SO real, mostra métricas ao vivo com
gráficos, recomenda otimizações (serviços, drivers, updates) e aplica as
seguras com confirmação explícita, gerando um relatório de antes/depois com
% de melhora.

Serve dois propósitos ao mesmo tempo:
1. Entregar valor real de produto (o módulo vira usável, não só prova de
   arquitetura).
2. Validar de ponta a ponta o pipeline de desenvolvimento de módulo:
   SDK Python (`techforge_sdk`) → manifest → Package Manager → Marketplace →
   PR contra o [`Tech.Forge.Modules`](https://github.com/julianscunha/Tech.Forge.Modules) → aprovação → reinstalação → teste real.

**Usuário:** dono de uma máquina Windows rodando o TechForge Desktop,
querendo entender o estado do próprio hardware/SO e aplicar otimizações
sem abrir o Painel de Controle.

**Sucesso:** o módulo mostra dado real (não mockado) da máquina onde roda,
o usuário consegue aplicar pelo menos uma otimização seguramente reversível
e ver o relatório de antes/depois refletir a mudança real.

## Decisões já fechadas (não reabrir sem motivo novo)

- **Aplicar mudanças**: recomendação + aplicação com confirmação explícita
  por item (nunca em lote, nunca silenciosa).
- **Plataforma**: Windows-first. Métricas de hardware (CPU/RAM/disco)
  funcionam em qualquer SO via `psutil`. Serviços/drivers/updates são
  Windows-only — noutro SO aparecem como indisponíveis, sem quebrar o
  módulo.
- **Dependências**: `psutil` (já presente no venv do Core) para métricas;
  `subprocess` + PowerShell (`Get-Service`, `Get-CimInstance`, `Get-HotFix`)
  para o que é Windows-específico — sem adicionar `pywin32` ao Core (não
  existe hoje mecanismo de dependência Python por módulo).
- **Escopo de "aplicar"**: só a categoria **Serviços do Windows** ganha ação
  de aplicar (start/stop com tipo de inicialização revertível), restrita a
  uma whitelist curada de serviços não-essenciais conhecidos (ex.: Fax,
  Windows Media Player Network Sharing, Maps Broker — nunca serviços
  críticos do SO). **Drivers e Windows Update são só recomendação** — não
  existe fonte confiável de "driver mais novo" nem forma seguro-reversível
  de aplicar update automaticamente sem infraestrutura extra; o módulo
  aponta o problema e linka a ação manual (`ms-settings:windowsupdate`).
  → Se você quiser aplicar automaticamente para drivers/updates também,
  isso é um projeto à parte (precisa de fonte de verdade de versões).

## Arquitetura

Mantém a separação Fase 8.1 já existente — Service Module fornece dado via
contrato público, Application Module consome, nunca importa código direto.

```
system_information_service (Service, sem UI)
  novos exports:
  - get_hardware_info()      → CPU model, cores/threads, RAM total, discos
  - get_live_metrics()       → CPU%, RAM%, disco (I/O + uso), snapshot pontual
  - get_windows_services()   → [{name, display_name, status, start_type}]
  - get_windows_drivers()    → [{name, version, date, class, signed}]
  - get_windows_update_status() → {last_installed_at, pending_reboot, service_running}
  - apply_service_action(name, action)  → start/stop/set_start_type, com log
      de estado anterior (revert)

system_health_check (Application, tem UI React)
  backend/
    dashboard.py    → GET /dashboard (hardware + live metrics + status geral)
    recommendations.py → GET /recommendations (engine de regras determinística)
                          POST /recommendations/{id}/apply (confirm-to-apply,
                          só service_action; grava snapshot antes/depois via
                          sdk.database)
    report.py        → GET /report (histórico de snapshots, % de melhora)
  frontend/ (React + Vite, mesmo padrão do lead_tracker/frontend)
    Dashboard com cards de hardware, gauges de métrica ao vivo (SVG
    hand-rolled, sem lib de gráfico nova), lista de recomendações com botão
    "Aplicar" por item, tela de relatório antes/depois.
```

Motor de recomendação é **regras determinísticas**, não IA/ML — cada
recomendação é uma função pura `(hardware, services, drivers, update_status)
→ list[Recommendation]`, testável isoladamente sem mockar SO.

## Comandos

```bash
# Backend do módulo (mesmo venv do Core — módulos rodam no processo do Core)
cd core/backend && .venv/Scripts/python.exe -m pytest ../../modules/installed/system_health_check/tests -q
cd core/backend && .venv/Scripts/python.exe -m pytest ../../modules/installed/system_information_service/tests -q

# Frontend do módulo (build próprio, gera frontend/index.js compilado — igual lead_tracker)
cd modules/installed/system_health_check/frontend && npm install && npm run build
cd modules/installed/system_health_check/frontend && npm run test   # vitest, se houver lógica pura a testar

# Rodar a plataforma pra teste manual (Core + módulos)
techforge dev
```

## Estrutura de projeto

```
modules/installed/system_information_service/
  backend/main.py         → exports novos (hardware, live metrics, services,
                             drivers, update status, apply_service_action)
  backend/windows.py      → wrappers subprocess/PowerShell isolados (fácil
                             de mockar em teste; noop/None fora do Windows)
  tests/                  → testa parsing dos wrappers com saída de exemplo
                             capturada (fixture), não depende de rodar no
                             Windows real durante CI

modules/installed/system_health_check/
  backend/main.py         → rotas + registro do ModuleContract
  backend/recommendations.py → engine de regras puro (testável sem SO)
  backend/report.py       → agrega snapshots (sdk.database) em % de melhora
  frontend/               → workspace Vite/React próprio (package.json,
                             src/, compila pra frontend/index.js)
  tests/                  → testa recommendations.py e report.py com dados
                             sintéticos
```

## Code Style

Segue o padrão já usado em `lead_tracker` e nos módulos de referência:
Python com type hints, `sdk = create_sdk("module_id")` no topo, nunca import
direto de outro módulo. Recomendação como dataclass:

```python
@dataclass
class Recommendation:
    id: str
    category: Literal["service", "driver", "update", "hardware"]
    severity: Literal["info", "warning", "critical"]
    title: str
    description: str
    applicable: bool          # False = drivers/updates, sempre manual
    action: Optional[ServiceAction] = None
```

React/TS segue o padrão de `lead_tracker/frontend/src` (componentes
funcionais, sem CSS-in-JS pesado, `styles.ts` para tokens compartilhados).

## Testing Strategy

- **`backend/windows.py`**: testado com saída de comando *capturada* como
  fixture (ex.: JSON de exemplo de `Get-CimInstance Win32_PnPSignedDriver`),
  nunca chamando o SO real no teste — evita teste flaky/lento e roda em
  qualquer CI.
- **`recommendations.py`/`report.py`**: testes unitários puros, sem
  `TestClient`, sem banco — funções determinísticas com dado sintético de
  entrada.
- **Rotas** (`dashboard.py`, integração `apply`): `TestClient(app)`,
  mockando `sdk.services.invoke` como já faz `test_phase_*` do módulo atual.
- Cobertura mínima: todo caminho de decisão do motor de recomendação (uma
  regra por teste), e o fluxo apply→revert de serviço.

## Boundaries

- **Sempre**: cada ação de "aplicar" grava estado anterior antes de mudar
  (permitir reverter); nenhuma ação roda sem confirmação explícita por
  item; testes cobrem cada regra de recomendação antes de mesclar.
- **Perguntar antes**: qualquer novo item na whitelist de serviços
  aplicáveis (mudar o que pode ser desligado é uma decisão de risco, não
  técnica); adicionar nova dependência Python além de `psutil`.
- **Nunca**: aplicar mudança em lote sem confirmação item a item; tocar em
  serviços críticos do SO (a whitelist é a única fonte de verdade — nunca
  aceitar um `service_name` fora dela, mesmo vindo da UI); aplicar
  atualização de driver/Windows Update automaticamente; mexer em arquivos
  de `core/` para lógica de negócio do módulo (só a camada de UI/badge do
  Core, já fechada nesta sessão).

## Success Criteria

- [ ] `GET /dashboard` retorna hardware real (CPU, RAM, disco) da máquina
      onde o Core está rodando — sem dado mockado.
- [ ] Pelo menos 3 categorias de recomendação implementadas (serviço,
      driver, update), cada uma com pelo menos 1 regra real e 1 teste.
- [ ] Aplicar uma recomendação de serviço muda o estado real do serviço no
      Windows e é revertível.
- [ ] Relatório antes/depois mostra uma métrica que de fato mudou após uma
      aplicação real (ex.: RAM livre subiu X%).
- [ ] `npm run build` do frontend do módulo gera `frontend/index.js` que o
      `ModuleHost` carrega sem erro.
- [ ] Suíte de testes do módulo (backend) passa, `ruff check` limpo.
- [ ] PR aberto contra `Tech.Forge.Modules`, revisado e aprovado.
- [ ] Módulo reinstalado a partir do catálogo após aprovação, testado ao
      vivo (não só localmente antes do PR).

## Open Questions

- Nenhuma bloqueante — segue com os defaults acima. Se drivers/updates
  precisarem de aplicação automática no futuro, é um spec novo (precisa de
  fonte de verdade de versão que hoje não existe).
