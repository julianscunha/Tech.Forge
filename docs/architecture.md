# Fonte Única de Verdade — Registry de Módulos

## Regra (2026-08-25, decisão do usuário)

O **registry in-memory** (`app/module_engine/registry.py`, singleton `registry`)
é a FONTE ÚNICA DE VERDADE sobre módulos em runtime. Toda leitura de estado
de módulos deve partir dele.

Hierarquia:
1. `modules/installed/` — verdade física (disco)
2. `ModuleLoader.scan_installed()` → popula o registry in-memory
3. `registry` in-memory — fonte de leitura para TODAS as APIs e UI
4. `sync_registry_to_db()` espelha para a tabela `modules` APENAS para
   contadores do Dashboard e persistência — nunca fonte primária de listagem

## Regras

- API de listagem (`/registry/modules`, `/marketplace/installed`, `/health`,
  navegação) lê do registry in-memory global.
- `PackageManager.list_installed()/list_available()` NÃO cria registries
  locais paralelos — usa o global (evita visões divergentes, ex.: 4 vs 2).
- Módulos INVALID/INCOMPATIBLE ficam no registry com status próprio; a UI
  decide como exibir. Não filtrar na fonte.
- Após qualquer mutação (install/remove/activate/deactivate): chamar
  `loader._hot_reload()` ou `scan_installed()` + `sync_registry_to_db()`.

## Histórico

Inconsistência "Módulos: 4 vs Marketplace: 2" (2026-08-25): lixo de teste em
modules/installed/ + backend antigo ainda em memória + list_installed() criando
registry local paralelo. Corrigido em registry_sync.py + manager.py.
