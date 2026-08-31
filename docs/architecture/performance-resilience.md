---
title: Performance, Resilience and Deprecation Policy
category: governanca-setup
domain: [governanca-setup]
tags: [architecture, consolidation]
---

# TechForge Core — Performance, Resilience e Deprecation Policy

> Baseline medido no ambiente de desenvolvimento atual (não é benchmark
> científico nem SLA — números de referência pra detectar regressão
> grosseira no futuro). Ver também [`core-inventory.md`](core-inventory.md),
> [`registry-consolidation.md`](registry-consolidation.md) e
> [`observability-security-desktop.md`](observability-security-desktop.md).

## Performance baseline

Medido com `techforge start`/`stop` reais neste ambiente, estado limpo
(nenhum outro processo do Core rodando antes/depois):

| Operação | Tempo medido | Observação |
|---|---|---|
| `techforge start` → `GET /health` responde 200 | ~4,8 s | Inclui subir uvicorn, `scan_installed()` dos 6 diretórios em `modules/installed/` (3 válidos, 3 inválidos por manifesto ausente) e ficar pronto pra aceitar requisição |
| Execução de um export simples (`POST /services/hello_world/invoke/ping`) | ~265 ms na primeira chamada (inclui overhead de conexão HTTP do curl) | Não medido em isolamento puro de `invoke()` — número inclui round-trip HTTP completo, não é o custo do runtime sozinho |
| `techforge stop` → todos os serviços `STOPPED` | ~2,4 s | Sem processo órfão após o comando (confirmado via `techforge status`) |

Módulo discovery: 6 diretórios em `modules/installed/`, 3 reais
(`hello_world`, `system_health_check`, `system_information_service`) e 3
órfãos sem manifesto (`some_module`, `test_module`, `unknown` —
reportados como `INVALID` no health check, não afetam o boot). Com esse
volume pequeno, o tempo de scan não é distinguível do tempo total de
boot — não há dado suficiente ainda pra isolar o custo de discovery por
módulo; revisitar quando o número de módulos instalados crescer.

**Nenhuma meta de performance foi definida aqui** — os números acima são
o baseline atual, não um SLA. Meta formal fica pra quando houver volume
real de módulos/usuários que justifique otimização.

## Core weight

Todas as 15 dependências de `core/backend/requirements.txt` têm uso real
confirmado por import no código:

| Dependência | Uso confirmado |
|---|---|
| `fastapi`, `uvicorn` | Framework HTTP e servidor ASGI |
| `sqlalchemy`, `aiosqlite` | ORM + driver async do SQLite |
| `pydantic`, `pydantic-settings` | Schemas de API e `Settings` centralizado |
| `python-dotenv` | Sem import direto no código — usado transitivamente por `pydantic-settings` para carregar `env_file` (`app/core/settings.py:70`); é dependência funcional real, não morta |
| `alembic` | `app/db/migrations.py` |
| `httpx` | `app/package_manager/repository.py` (catálogo remoto) |
| `pyyaml` | Parsing de manifesto |
| `packaging` | Comparação de versões (`dependency_engine`, `module_engine.manifest`, `compatibility`, `changelog`) |
| `keyring` | `security/secret_store.py` (único ponto de acesso) |
| `psutil` | `services/resource_usage.py` |
| `platformdirs` | Paths por SO |
| `cryptography` | `module_trust/signature.py` (verificação Ed25519) |

**Nenhuma dependência removida** — todas justificadas, sem candidato real
a remoção.

## Failure isolation

Cobertura de teste existente confirmada por área (via inspeção dos
arquivos de teste, sem criar testes novos):

| Área | Cobertura confirmada |
|---|---|
| Módulo com erro de import/carregamento | `test_missing_file_raises_module_load_error`, `test_import_error_in_module_raises_module_load_error` — erro tipado, não derruba o Core |
| Falha em `on_activate`/`on_deactivate` | `test_on_activate_enable_failure_sets_failed_with_last_error`, `test_activate_module_failure_in_enable_does_not_block_administrative_state` — falha de runtime não corrompe o estado administrativo do módulo |
| Falha em `health_check` | `test_health_check_exception_sets_failed`, `test_health_check_unhealthy_sets_degraded` |
| Falha de rede durante instalação remota | `test_background_task_network_failure_reaches_failed`, `test_no_module_installed_on_network_failure` — confirma que módulo não fica instalado pela metade numa falha de rede |
| Falha de dependência bloqueada | Suíte de compatibilidade/governança de dependência (`test_phase8_1_dependency_governance.py`, `test_phase4_install_guard.py`) cobre bloqueio de ativação por dependência não satisfeita |
| Falha de pacote (zip corrompido, manifesto inválido) | Tratada em `manager.py` (`except (zipfile.BadZipFile, yaml.YAMLError)`) — coberta pela suíte de instalação |

**Lacuna real encontrada**: `StorageProvider.health_check()` só tem teste
pro caminho saudável (`test_storage_provider_health_check_reports_writable_true_on_healthy_db`).
Não há teste simulando banco indisponível/não-gravável e confirmando que
o restante da plataforma degrada de forma isolada (em vez de propagar
exceção não tratada). Registrado como item de débito técnico no
Technical Debt Registry — não implementado aqui (fora de escopo criar
bateria nova de testes de falha de infraestrutura nesta revisão).

## Data integrity

`package_manager/manager.py::install()` já limpa o diretório de extração
temporário (`shutil.rmtree(extract_tmp)`) em qualquer exceção durante a
instalação — módulo não fica em estado parcialmente extraído.
`update()` vai além: mantém backup do diretório anterior e faz rollback
explícito dele em caso de falha durante a atualização (comentário no
código confirma a intenção: "falha de update — rollback do bloco except
abaixo"). Nenhuma lacuna de atomicidade encontrada nos dois fluxos.

## Backward compatibility

Reconfirmação breve (detalhe completo já em
[`public-contracts.md`](public-contracts.md)): `ParsedManifest` só cresceu
por campos opcionais desde sua criação, sem mudança de assinatura
existente reportada. Nenhum contrato do catálogo teve breaking change
identificado.

## Deprecation policy

Não existia uma política formal até agora — o que segue formaliza a
prática implícita já seguida no projeto (nunca remover um contrato sem
aviso):

1. **Mark** — o item a depreciar (endpoint, campo de schema, contrato,
   comando CLI) ganha uma anotação explícita no código-fonte (comentário
   `# DEPRECATED: <motivo>, remover a partir de <critério>` acima da
   definição, ou `deprecated=True` quando o framework suportar, como em
   rotas FastAPI).
2. **Document** — o item entra na tabela de estabilidade do documento de
   contratos relevante (ver [`public-contracts.md`](public-contracts.md))
   com status `Deprecated`, motivo da depreciação e o que usar no lugar.
3. **Warn** — consumidores reais (UI, CLI, módulos de exemplo) que usam o
   item passam a receber aviso visível: log em nível `WARNING` no
   backend quando o path é exercitado, ou mensagem explícita na resposta
   de API (campo `deprecation_notice`, por exemplo) quando fizer sentido
   pro consumidor perceber sem precisar ler logs.
4. **Migrate** — todo uso interno do item (Core, módulos de exemplo,
   CLI) é migrado pro substituto antes da remoção — nunca remover algo
   que o próprio Core ainda usa internamente.
5. **Remove** — remoção só depois de pelo menos um ciclo de release
   completo com o item marcado como `Deprecated` e sem uso interno
   restante. Contratos classificados como `Stable` (ver
   `public-contracts.md`) exigem esse ciclo completo; contratos
   `Experimental` podem ser removidos com aviso simples em release
   notes, sem o ciclo completo (já definido na policy de versionamento
   de contratos).

Esta política não introduz nenhum mecanismo automático de aviso agora —
é a definição do processo, a implementar conforme surgir a primeira
depreciação real.

## Suíte de testes

`cd core/backend && .venv/Scripts/python.exe -m pytest tests -q` →
**949 passed, 3 skipped**, sem regressão. Nenhum código de produção foi
alterado nesta revisão (lacuna de teste de storage registrada como
débito, não implementada agora).
