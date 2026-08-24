# Graph Report - Tech.Forge  (2026-08-24)

## Corpus Check
- 164 files · ~57,769 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1795 nodes · 3250 edges · 124 communities (97 shown, 27 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 295 edges (avg confidence: 0.97)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `28dce2b8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TemplateGenerator
- ModuleService
- TechForge SDK (techforge_sdk)
- get
- manifest.yaml
- TechForgeRuntime
- ._not_implemented
- test_phase5.py
- LocalRepositoryProvider
- package_module_cmd
- ModuleStatus
- make_package_manager
- ModuleRegistry
- MarketplacePage.tsx
- PackageManager
- DocIndex
- cn
- .parse
- .parse
- types/index.ts
- DocIndexer
- compilerOptions
- marketplace.py
- .check
- .validate
- calculate_storage
- test_phase3.py
- .parse
- components/index.tsx
- DatabaseSDK
- StorageSDK
- devDependencies
- hello_world
- ModuleContract
- ModulesPage.tsx
- techforge_sdk.py
- manager.py
- DeveloperCenterPage.tsx
- LoaderJournalViewer.tsx
- dependencies
- SettingsSDK
- ModuleEntry
- ModuleCLIValidator
- journal.py
- OperationLog
- DashboardPage.tsx
- NotificationsSDK
- TestSDKServices
- check_compatibility
- PackageInfo
- HealthResult
- NavCategoryNode
- cn
- src/index.ts
- .export
- AppRouter.tsx
- VeeamM365Module
- package.json
- HelloWorldModule
- app/main.py
- LoggerSDK
- create_sdk
- TestRealModuleDocs
- TestSDKContracts
- tokens/index.ts
- ModuleMetadata
- hello_world/frontend/index.tsx
- veeam_m365/frontend/index.tsx
- frontend/index.ts
- contracts/index.ts
- techforge_cli/main.py
- test_documentation_first.py
- techforge_launcher/__init__.py
- Settings
- class-variance-authority
- @radix-ui/react-dropdown-menu
- Componentes principais
- @radix-ui/react-slot
- @radix-ui/react-tooltip
- react-dom
- core.py
- BlogBackup
- FAQ (Frequently Asked Questions)
- download_file
- module_integration
- upload_file
- Launcher
- TestHelloWorldModule
- techforge_sdk/__init__.py
- api/__init__.py
- Referência do Manifesto (manifest.yaml)
- SDK Backend (Python)
- Service Modules
- hello_world/docs/examples/integration.md
- veeam_m365/docs/examples/integration.md
- Runtime
- Introdução ao TechForge
- context7
- hello_world/docs/examples/basic.md
- Hello World
- hello_world Module
- advanced.md
- veeam_m365/docs/examples/basic.md
- Veeam M365 Sizing
- AGENTS.md
- code-reviewer.md
- SKILL.md
- @radix-ui/react-dialog
- veeam_m365/docs/README.md
- NavigationTree

## God Nodes (most connected - your core abstractions)
1. `cn()` - 62 edges
2. `DocIndex` - 40 edges
3. `ModuleRegistry` - 39 edges
4. `get()` - 32 edges
5. `DocIndexer` - 31 edges
6. `ModuleStatus` - 26 edges
7. `make_package_manager()` - 26 edges
8. `DocCategory` - 24 edges
9. `check_compatibility()` - 22 edges
10. `DocEntry` - 21 edges

## Surprising Connections (you probably didn't know these)
- `Phase 2: Module Engine` --documents--> `ManifestParser`  [INFERRED]
  docs/phase2_module_engine.md → core/backend/app/module_engine/manifest.py
- `Module Loader` --delegates_to--> `ManifestParser`  [INFERRED]
  docs/developer-center/core/module-registry.md → core/backend/app/module_engine/manifest.py
- `Phase 2: Module Engine` --documents--> `ModuleValidator`  [INFERRED]
  docs/phase2_module_engine.md → core/backend/app/module_engine/validator.py
- `Module Loader` --delegates_to--> `ModuleValidator`  [INFERRED]
  docs/developer-center/core/module-registry.md → core/backend/app/module_engine/validator.py
- `TestSDKServices` --uses--> `TechForgeSDK`  [INFERRED]
  cli/tests/test_phase3.py → sdk/python/techforge_sdk.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Documentation First Governance Structure** — docs_developer_center_governance_documentation_first_principle, validate_module_cmd, doc_completeness_checker, all_example_tiers, developer_center [EXTRACTED 0.95]
- **TechForge Core Platform Stack** — techforge_platform, fastapi_backend, react_frontend, techforge_sdk, docs_developer_center_core_module_registry, module_loader, docs_developer_center_core_package_manager [INFERRED 0.75]
- **Module Lifecycle State Flow** — docs_developer_center_core_module_lifecycle, docs_developer_center_core_module_lifecycle_contract, techforge_sdk, docs_developer_center_examples_hello_world_example, docs_developer_center_core_package_manager, docs_developer_center_core_module_registry, module_status_system [INFERRED 0.85]
- **he_frontend_module_config** — moduleConfig, ModulePageConfig, field_id, field_icon, field_category, field_vendor, ModulePage, @techforge/sdk [INFERRED]
- **he_manifest_fields** — manifest.yaml, field_id, field_name, field_version, field_category, field_vendor, field_author, field_description, field_entry_backend, field_entry_frontend, field_icon, field_order [INFERRED]
- **he_module_lifecycle** — create-module, validate-module, package-module, install_module_cmd, modules_installed [INFERRED]
- **he_module_registration** — ModuleLoader, manifest.yaml, ModuleRegistry, NavigationBuilder, AppShell [INFERRED]
- **he_sdk_instantiation** — create_sdk, Module, techforge_sdk, sdk.logger, sdk.settings, sdk.storage, sdk.database, sdk.notifications [INFERRED]
- **he_service_module_contract** — ServiceModule, field_module_type, api.yaml, field_service_id, field_dependencies, field_exports, upload_file, download_file [INFERRED]
- **Module Validation Pipeline** — module_loader, core_backend_app_module_engine_manifest_manifestparser, core_backend_app_module_engine_validator_modulevalidator, docs_developer_center_core_module_registry [INFERRED]

## Communities (124 total, 27 thin omitted)

### Community 0 - "TemplateGenerator"
Cohesion: 0.09
Nodes (22): _component_name(), _len(), _make_env(), ModuleSpec, Path, TechForge CLI — Template Generator =====================================…, # TODO: create tables, default settings, initial data, # TODO: start background tasks, open connections (+14 more)

### Community 1 - "ModuleService"
Cohesion: 0.07
Nodes (41): Category, create_category(), get_category(), list_categories(), AsyncSession, post, get_module(), list_modules() (+33 more)

### Community 2 - "TechForge SDK (techforge_sdk)"
Cohesion: 0.06
Nodes (56): Module, PackageManager, PermissionError, Three Example Tiers (basic.md, advanced.md, integration.md), create-module, create_sdk, Developer Center, Developer Mode (+48 more)

### Community 3 - "get"
Cohesion: 0.06
Nodes (59): _completeness_to_read(), CompletenessReportRead, _contract_to_read(), DocEntryFull, DocEntryMeta, DocSummary, DoDCheckRead, export_ai_context() (+51 more)

### Community 4 - "manifest.yaml"
Cohesion: 0.05
Nodes (48): @techforge/sdk, AppShell, Button, Card, Core, DataTable, DeveloperCenter, EmptyState (+40 more)

### Community 5 - "TechForgeRuntime"
Cohesion: 0.05
Nodes (21): asyncio, Enum, str, TechForge Runtime (Phase 6 — foundation)…, One lifecycle event received by the runtime., Process-lifetime singleton holding platform run state. Usage (FastAPI…, RuntimeEvent, RuntimeState (+13 more)

### Community 6 - "._not_implemented"
Cohesion: 0.09
Nodes (17): DatabaseSDK, LoggerSDK, NotificationsSDK, ABC, Any, TechForge SDK — Service Contracts =================================== All SDK…, Per-module key-value configuration store. Phase 3: backed by a dedicated table…, Push in-app notifications to the Core header bell. Phase 3: will emit Server-… (+9 more)

### Community 7 - "test_phase5.py"
Cohesion: 0.10
Nodes (24): Documentation Indexer ====================== Scans all documentation sources…, AIContextExporter, Documentation Engine ===================== Process-level singleton assembly and…, Generates a single consolidated Markdown document containing the entire…, Markdown Parser ================ Reads .md files, optionally parses YAML…, DocCategory, DocEntry, ExampleTier (+16 more)

### Community 8 - "LocalRepositoryProvider"
Cohesion: 0.09
Nodes (18): LocalRepositoryProvider, ABC, PackageInfo, Path, Repository Provider ==================== Abstraction layer between the Package…, Return path to the latest .mod file for module_id., Accept a manually uploaded .mod file and store it in cache/. Returns the path…, Extract manifest.yaml from a .mod file and return PackageInfo. (+10 more)

### Community 9 - "package_module_cmd"
Cohesion: 0.16
Nodes (25): create_module_cmd(), command, option, techforge create-module — interactive module scaffold generator., Scaffold a new TechForge module interactively. Generates the complete directory…, package_module_cmd(), argument, command (+17 more)

### Community 10 - "ModuleStatus"
Cohesion: 0.14
Nodes (25): ModuleStatus, Enum, str, Lifecycle states for a module as defined in the TechForge specification.…, ModuleLoader, ModuleLoader ============ Orchestrates the complete module lifecycle pipeline…, Scans the installed modules directory, validates each module, and populates the…, _assert_semver() (+17 more)

### Community 11 - "make_package_manager"
Cohesion: 0.14
Nodes (8): make_mod_file(), make_package_manager(), Path, Create a minimal valid .mod file in tmp/., TestInstall, TestPackageManagerQueries, TestRemove, TestUpdate

### Community 12 - "ModuleRegistry"
Cohesion: 0.11
Nodes (14): NavigationBuilder, NavModuleNode, NavVendorNode, Leaf node — one installed module., Mid-level node — one vendor within a category., Stateless builder — call build() whenever the registry changes. The Sidebar…, Build a NavigationTree from all INSTALLED modules in the registry. Args: reg:…, ModuleRegistry (+6 more)

### Community 13 - "MarketplacePage.tsx"
Cohesion: 0.10
Nodes (22): CompatibilityBadge(), CONFIG, Props, ActionBtn(), PackageCard(), Props, Tab, Variant (+14 more)

### Community 14 - "PackageManager"
Cohesion: 0.10
Nodes (15): InstallResult, PackageManager, PackageInfo, Path, Install a module from a .mod file path. Steps: 1. Validate the .mod archive…, Remove an installed module. Steps: 1. Verify it exists in the registry 2.…, Update an installed module from a newer .mod file. Steps: 1. Verify current…, List all packages available in repository/. (+7 more)

### Community 15 - "DocIndex"
Cohesion: 0.16
Nodes (6): DocIndex, In-memory inverted-index of documentation entries. Rebuilt from scratch on…, Remove a doc from the index (used after module uninstall)., make_entry(), TestDocIndex, TestDocSearchEngine

### Community 16 - "cn"
Cohesion: 0.12
Nodes (22): Breadcrumb(), PATH_LABELS, Header(), CategorySection(), COLOR_DOT, ICON_MAP, ModuleNavItem(), Sidebar() (+14 more)

### Community 17 - ".parse"
Cohesion: 0.13
Nodes (14): Scan docs/developer-center/ and index all .md files., _extract_h1(), MarkdownParser, _parse_frontmatter(), Path, Parse all .md files in *directory* matching *glob*. Returns entries sorted by…, Return (frontmatter_dict, body_without_frontmatter)., Return the first H1 heading text, or None. (+6 more)

### Community 18 - ".parse"
Cohesion: 0.14
Nodes (7): Path, Locate, load, and validate the manifest.yaml inside *module_path*. Validation…, _version_tuple(), veeam_m365 (order=10) should sort before hello_world (order=99) but they are in…, TestManifestParserNavFields, TestRealModuleManifests, write_manifest()

### Community 19 - "types/index.ts"
Cohesion: 0.12
Nodes (23): categoriesApi, modulesApi, navigationApi, CORE_NAV, NavState, Category, DocEntryFull, DocEntryMeta (+15 more)

### Community 20 - "DocIndexer"
Cohesion: 0.14
Nodes (9): DocIndexer, Path, ServiceContract, Scan all installed modules and index their docs., Builds and refreshes the DocIndex from all documentation sources., Clear and rebuild the entire index. Returns: Total number of documents indexed., Index (or re-index) documentation for a single module. Called by PackageManager…, Remove all docs for a module. Called after uninstall. (+1 more)

### Community 21 - "compilerOptions"
Cohesion: 0.08
Nodes (23): compilerOptions, allowImportingTsExtensions, baseUrl, isolatedModules, jsx, lib, module, moduleDetection (+15 more)

### Community 22 - "marketplace.py"
Cohesion: 0.09
Nodes (31): CompatibilityLevel, check_compat(), CompatibilityRequest, CompatibilityResponse, get_operation_log(), import_module(), install_module(), list_available() (+23 more)

### Community 23 - ".check"
Cohesion: 0.08
Nodes (16): CompletenessReport, DocCompletenessChecker, Path, Computes a full §16 Definition-of-Done report for one module directory. Usage:…, Full Definition-of-Done report for a single module. is_complete is True only…, Percentage of required checks passing, 0.0–100.0., make_module(), Path (+8 more)

### Community 24 - ".validate"
Cohesion: 0.19
Nodes (3): TestModuleCLIValidator, Path, TestCLIValidatorNavFields

### Community 25 - "calculate_storage"
Cohesion: 0.10
Nodes (22): backup sizing, compliance, advanced.md, basic.md, integration.md, overview.md, calculate_storage, sales_proposal_module (+14 more)

### Community 26 - "test_phase3.py"
Cohesion: 0.16
Nodes (12): BuildResult, PackageBuilder, Path, TechForge CLI — Package Builder ================================== Builds a…, Builds a .mod package from a module directory., Package *module_path* into a .mod archive. Args: module_path: Absolute or…, _should_exclude(), make_valid_module() (+4 more)

### Community 27 - ".parse"
Cohesion: 0.15
Nodes (8): _normalize_returns(), Path, ServiceContract, Normalize the `returns` field, which the official §16 spec allows as either a…, Parse an api.yaml file. Returns: ServiceContract if the file is valid, None…, TestReturnsNormalization, Path, TestAPIYamlParser

### Community 28 - "components/index.tsx"
Cohesion: 0.10
Nodes (19): BadgeProps, badgeVariant, ButtonProps, CardProps, Column, DataTableProps, EmptyStateProps, FormFieldProps (+11 more)

### Community 29 - "DatabaseSDK"
Cohesion: 0.13
Nodes (11): DatabaseSDK, Any, Best-effort table name extraction for mock routing., Isolated database access for a single module. Each module receives its own…, Execute a SELECT query and return all matching rows. Phase 3 mock: returns rows…, Execute a SELECT query and return the first matching row, or None., Execute an INSERT, UPDATE, or DELETE statement. Phase 3 mock: stores rows in…, Batch execute a statement for multiple parameter sets. (+3 more)

### Community 30 - "StorageSDK"
Cohesion: 0.14
Nodes (11): Path, Read a text file. Convenience wrapper around read()., Write a text file. Convenience wrapper around write()., Resolve path relative to module base, preventing directory traversal., Isolated file storage scoped to a single module's data directory. Phase 3:…, Read a file from the module's storage directory. Args: path: Relative path…, Write bytes to a file in the module's storage directory. Creates parent…, Delete a file from the module's storage directory. No-op if the file does not… (+3 more)

### Community 31 - "devDependencies"
Cohesion: 0.11
Nodes (19): autoprefixer, devDependencies, autoprefixer, postcss, tailwindcss, @types/node, @types/react, @types/react-dom (+11 more)

### Community 32 - "hello_world"
Cohesion: 0.12
Nodes (19): Examples, ModuleContract, backup_sizing, hello_world/info, hello_world/ping, veeam_m365/ping, calculate_storage, ping (+11 more)

### Community 33 - "ModuleContract"
Cohesion: 0.14
Nodes (9): ModuleContract, ABC, TechForge SDK — Module Contracts ================================== Base…, Called when the module is disabled. Stop background tasks, release connections.…, Called when upgrading from a previous version. Run migrations, transform stored…, Called when the module is permanently removed. Delete all data, tables, files…, Abstract base class for all TechForge module backends. Every module MUST…, Called once when the module is first installed. Create database tables, default… (+1 more)

### Community 34 - "ModulesPage.tsx"
Cohesion: 0.13
Nodes (17): ModuleCard(), Props, Field(), ModuleDetailPanel(), Props, CONFIG, ModuleStatusBadge(), Props (+9 more)

### Community 35 - "techforge_sdk.py"
Cohesion: 0.09
Nodes (12): _DatabaseSDK, _LoggerSDK, _NotificationsSDK, TechForge SDK — Python ====================== This is the stub/skeleton for the…, Phase 2: will wrap SQLAlchemy sessions scoped to the calling module. Modules…, Phase 2: isolated file storage per module under modules/installed/<id>/data/, Phase 2: structured logging tagged with the calling module's ID., Phase 2: per-module settings isolated from global Core settings. (+4 more)

### Community 36 - "manager.py"
Cohesion: 0.28
Nodes (13): Compatibility Checker ====================== Determines whether a package is…, CompatibilityLevel, InstallStatus, Enum, str, Trust level for a package source. Phase 5 will populate this based on…, RemoveStatus, TrustLevel (+5 more)

### Community 37 - "DeveloperCenterPage.tsx"
Cohesion: 0.17
Nodes (12): CATEGORY_LABELS, DocSearch(), Props, MarkdownRenderer(), Props, ExportCard(), Props, ServiceContractPanel() (+4 more)

### Community 38 - "LoaderJournalViewer.tsx"
Cohesion: 0.29
Nodes (7): EventRow(), LEVEL_CONFIG, LoaderJournalViewer(), Pill(), Props, LoaderResult, LoadEvent

### Community 39 - "dependencies"
Cohesion: 0.12
Nodes (17): clsx, dependencies, clsx, lucide-react, marked, @radix-ui/react-separator, react, react-router-dom (+9 more)

### Community 40 - "SettingsSDK"
Cohesion: 0.16
Nodes (9): Any, Path, Per-module persistent settings backed by a JSON file. Thread-safe for single-…, Retrieve a setting value. Args: key: Setting name. default: Value to return if…, Store a setting value. Persists immediately to disk. Args: key: Setting name…, Remove a setting. No-op if the key does not exist., Return a snapshot of all current settings., Delete all settings for this module. Called by ModuleContract.uninstall() to… (+1 more)

### Community 41 - "ModuleEntry"
Cohesion: 0.14
Nodes (7): ModuleStatus, Register a failed module so it appears in the UI with its error state., ModuleEntry, ModuleStatus, Add or replace a module entry in the registry., Update the status of an already-registered module. Returns True if the module…, One entry in the module registry. Combines manifest data with runtime state so…

### Community 42 - "ModuleCLIValidator"
Cohesion: 0.18
Nodes (8): CheckResult, ModuleCLIValidator, Path, TechForge CLI — Module Validator ================================== Standalone…, §16 — Documentation First Principle. A module is not "done" without:…, §16 — every export in api.yaml must declare: name, description, parameters…, Validates a module directory and returns a detailed ValidationReport. Usage:…, ValidationReport

### Community 43 - "journal.py"
Cohesion: 0.12
Nodes (12): LoaderJournal ============= Simple process-lifetime store for the most recent…, store(), LoaderResult, LoadEvent, Path, Validate and register a single module directory., One timestamped entry in the loader journal., Summary returned after a full scan. (+4 more)

### Community 44 - "OperationLog"
Cohesion: 0.24
Nodes (4): OperationLog, OperationLogEntry, In-process ring buffer of Package Manager events., TestOperationLog

### Community 45 - "DashboardPage.tsx"
Cohesion: 0.18
Nodes (10): StatCard(), StatCardProps, Status, STATUS_CONFIG, StatusBadge(), StatusBadgeProps, platformApi, DashboardPage() (+2 more)

### Community 46 - "NotificationsSDK"
Cohesion: 0.16
Nodes (8): Notification, NotificationsSDK, SDK Notifications Service ========================== Push in-app notifications…, Mark a notification as read by its ID., Discard all notifications for this module., In-process notification queue for one module. The Core API drains this queue…, Enqueue a notification for the Core UI to display. Args: title: Short headline…, Return all unread notifications.

### Community 48 - "check_compatibility"
Cohesion: 0.27
Nodes (4): check_compatibility(), Check whether *platform_version* falls within [min_version, max_version]. Args:…, _vt(), TestCompatibility

### Community 49 - "PackageInfo"
Cohesion: 0.19
Nodes (6): PackageInfo, Path, Full metadata about a package — either from a .mod file in the repository or…, True when the repository has a newer version than what is installed., _version_tuple(), TestPackageInfo

### Community 50 - "HealthResult"
Cohesion: 0.24
Nodes (4): HealthResult, Any, Return the current health state of the module. Called periodically by the Core…, Returned by health_check().

### Community 52 - "cn"
Cohesion: 0.17
Nodes (12): Badge(), Button(), Card(), cn(), DataTable(), EmptyState(), LoadingState(), Modal() (+4 more)

### Community 53 - "src/index.ts"
Cohesion: 0.21
Nodes (6): ModuleSettings, navigationSDK, NotificationLevel, notificationsSDK, sdk, settingsSDK

### Community 55 - "AppRouter.tsx"
Cohesion: 0.16
Nodes (11): AppRouter(), AppShell(), ComingSoon(), ComingSoonProps, registryApi, stored, DeveloperCenterPage(), MarketplacePage() (+3 more)

### Community 57 - "package.json"
Cohesion: 0.20
Nodes (9): name, private, scripts, build, dev, lint, preview, type (+1 more)

### Community 58 - "HelloWorldModule"
Cohesion: 0.20
Nodes (4): HelloWorldModule, info(), ping(), hello_world — Backend Entry Point =================================== Reference…

### Community 59 - "app/main.py"
Cohesion: 0.15
Nodes (15): init_db(), Create all tables on startup., create_app(), lifespan(), FastAPI, Startup sequence: 1. Initialize / migrate database tables 2. Module Loader —…, add_event(), Append a single event to the stored result (used by the Plugin Loader). (+7 more)

### Community 61 - "create_sdk"
Cohesion: 0.25
Nodes (5): create_sdk(), Path, Root SDK object. Module backends should call create_sdk(module_id) to get a…, Factory function — creates an SDK instance scoped to *module_id*. Call this at…, TechForgeSDK

### Community 64 - "tokens/index.ts"
Cohesion: 0.29
Nodes (6): cls, colors, fontSize, fontWeight, radius, spacing

### Community 65 - "ModuleMetadata"
Cohesion: 0.33
Nodes (3): ModuleMetadata, Static identity information about a module. Mirrors the fields declared in…, Return the module's static identity information. Must match the values in…

### Community 68 - "frontend/index.ts"
Cohesion: 0.40
Nodes (4): Notification, notificationsSDK, sdk, settingsSDK

### Community 69 - "contracts/index.ts"
Cohesion: 0.40
Nodes (3): ModuleLifecycleHooks, ModulePageConfig, ModuleSubRoute

### Community 70 - "techforge_cli/main.py"
Cohesion: 0.16
Nodes (17): command, option, techforge start | stop | status — Phase 6…, Start the complete TechForge platform (backend + frontend + browser)., Stop the running TechForge platform (frontend → backend, no orphans)., Show the current state of every TechForge component., _run_launcher(), start_cmd() (+9 more)

### Community 71 - "test_documentation_first.py"
Cohesion: 0.19
Nodes (16): APIYamlParser, API YAML Parser ================ Parses a module's contracts/api.yaml into a…, Stateless parser for contracts/api.yaml files. Usage: contract =…, DoDCheck, ServiceContract, Documentation Completeness Checker — §16 Documentation First Principle…, One Definition-of-Done criterion., Validate that a ServiceContract meets §16 requirements for every export: name,… (+8 more)

### Community 72 - "techforge_launcher/__init__.py"
Cohesion: 0.08
Nodes (37): already_running(), _clear_state(), ComponentStatus, _http_ok(), _npm_exe(), _pid_alive(), PlatformState, Path (+29 more)

### Community 76 - "Componentes principais"
Cohesion: 0.17
Nodes (11): Button, Card, Componentes principais, DataTable, EmptyState / LoadingState, Importação, Modal, moduleConfig — contrato obrigatório (+3 more)

### Community 80 - "core.py"
Cohesion: 0.20
Nodes (5): TechForge SDK — Core ===================== Assembles all SDK services into a…, SDK Database Service ==================== Provides isolated database access for…, SDK Logger Service — Phase 3 (functional), SDK Settings Service ===================== Per-module key-value configuration…, SDK Storage Service ==================== Sandboxed file storage for module…

### Community 99 - "Launcher"
Cohesion: 0.22
Nodes (8): Arquitetura, Comandos, Desenvolvimento vs Produção, Encerramento, Launcher, Logs, Portabilidade, Single-instance

### Community 101 - "techforge_sdk/__init__.py"
Cohesion: 0.40
Nodes (3): ping(), veeam_m365 — Backend Entry Point =================================== Module :…, TechForge SDK — Python ====================== Official SDK for TechForge module…

### Community 102 - "api/__init__.py"
Cohesion: 0.39
Nodes (6): get_module_health(), get_platform_health(), ModuleHealth, PlatformHealth, BaseModel, /api/v1/health — Module Health Checks ======================================…

### Community 103 - "Referência do Manifesto (manifest.yaml)"
Cohesion: 0.29
Nodes (6): Campos obrigatórios, Campos opcionais, Exemplo completo, Referência do Manifesto (manifest.yaml), Validação, Ícones disponíveis

### Community 104 - "SDK Backend (Python)"
Cohesion: 0.29
Nodes (6): SDK Backend (Python), sdk.database, sdk.logger, sdk.notifications, sdk.settings, sdk.storage

### Community 105 - "Service Modules"
Cohesion: 0.29
Nodes (6): Como consumir um serviço, Como o Developer Center exibe um serviço, Contrato de serviço — api.yaml, Exemplos estruturais, Identificação, Service Modules

### Community 106 - "hello_world/docs/examples/integration.md"
Cohesion: 0.29
Nodes (6): Declarando a dependência no manifesto, Entradas, Exemplo, Objetivo, Observações, Saídas

### Community 107 - "veeam_m365/docs/examples/integration.md"
Cohesion: 0.29
Nodes (6): Declarando a dependência no manifesto, Entradas, Exemplo, Objetivo, Observações, Saídas

### Community 108 - "Runtime"
Cohesion: 0.33
Nodes (5): Consumo pelo Dashboard, Integração, O que NÃO faz nesta fase, Responsabilidade atual, Runtime

### Community 109 - "Introdução ao TechForge"
Cohesion: 0.33
Nodes (5): Começando, Como funciona, Estrutura do projeto, Filosofia da Plataforma, Introdução ao TechForge

### Community 110 - "context7"
Cohesion: 0.40
Nodes (5): npx, context7, playwright, @context7/mcp-server, @modelcontextprotocol/server-playwright

### Community 111 - "hello_world/docs/examples/basic.md"
Cohesion: 0.33
Nodes (5): Entradas, Exemplo, Objetivo, Observações, Saídas

### Community 112 - "Hello World"
Cohesion: 0.33
Nodes (5): Como usar como template, Descrição, Endpoints, Hello World, O que valida

### Community 113 - "hello_world Module"
Cohesion: 0.33
Nodes (5): hello_world Module, How to use as a template, Lifecycle, Purpose, What it does NOT do

### Community 114 - "advanced.md"
Cohesion: 0.33
Nodes (5): Entradas, Exemplo, Objetivo, Observações, Saídas

### Community 115 - "veeam_m365/docs/examples/basic.md"
Cohesion: 0.33
Nodes (5): Entradas, Exemplo, Objetivo, Observações, Saídas

### Community 116 - "Veeam M365 Sizing"
Cohesion: 0.33
Nodes (5): Campos do manifest, Descrição, Próximos passos, Status, Veeam M365 Sizing

## Knowledge Gaps
- **221 isolated node(s):** `@context7/mcp-server`, `@modelcontextprotocol/server-playwright`, `name`, `private`, `version` (+216 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get()` connect `get` to `ModuleService`, `TechForgeRuntime`, `api/__init__.py`, `techforge_sdk/__init__.py`, `journal.py`, `marketplace.py`, `HelloWorldModule`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Why does `Phase 2: Module Engine` connect `TechForge SDK (techforge_sdk)` to `ModuleStatus`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `TechForge SDK (techforge_sdk)` connect `TechForge SDK (techforge_sdk)` to `manifest.yaml`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `DocIndex` (e.g. with `DocIndexer` and `DocCategory`) actually correct?**
  _`DocIndex` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `DocIndexer` (e.g. with `APIYamlParser` and `MarkdownParser`) actually correct?**
  _`DocIndexer` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `@context7/mcp-server`, `@modelcontextprotocol/server-playwright`, `name` to the rest of the system?**
  _221 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `TemplateGenerator` be split into smaller, more focused modules?**
  _Cohesion score 0.08902439024390243 - nodes in this community are weakly interconnected._