# Graph Report - .  (2026-08-11)

## Corpus Check
- 159 files · ~53,433 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1564 nodes · 3201 edges · 99 communities (79 shown, 20 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 343 edges (avg confidence: 0.53)
- Token cost: 7,000 input · 4,000 output

## Community Hubs (Navigation)
- Core Platform Architecture
- Hello World Plugin
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Veeam M365 Integration
- Documentation System
- Package Management
- API Endpoints
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 81
- Community 94
- Community 95
- Community 96
- Community 98

## God Nodes (most connected - your core abstractions)
1. `cn()` - 59 edges
2. `DocIndex` - 44 edges
3. `ModuleRegistry` - 40 edges
4. `DocIndexer` - 36 edges
5. `DocCategory` - 36 edges
6. `ServiceContract` - 34 edges
7. `ModuleStatus` - 34 edges
8. `get()` - 33 edges
9. `TemplateGenerator` - 30 edges
10. `LocalRepositoryProvider` - 30 edges

## Surprising Connections (you probably didn't know these)
- `Phase 2: Module Engine` --documents--> `ManifestParser`  [EXTRACTED]
  docs/phase2_module_engine.md → core/backend/app/module_engine/manifest.py
- `Module Loader` --delegates_to--> `ManifestParser`  [EXTRACTED]
  docs/developer-center/core/module-registry.md → core/backend/app/module_engine/manifest.py
- `Phase 2: Module Engine` --documents--> `ModuleValidator`  [EXTRACTED]
  docs/phase2_module_engine.md → core/backend/app/module_engine/validator.py
- `Module Loader` --delegates_to--> `ModuleValidator`  [EXTRACTED]
  docs/developer-center/core/module-registry.md → core/backend/app/module_engine/validator.py
- `Package Manager` --logs_to--> `OperationLog`  [EXTRACTED]
  docs/developer-center/core/package-manager.md → core/backend/app/module_engine/operation_log.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **TechForge Core Platform Stack** — techforge_platform, fastapi_backend, react_frontend, techforge_sdk, docs_developer_center_core_module_registry, module_loader, docs_developer_center_core_package_manager [INFERRED 0.75]
- **Documentation First Governance Structure** — docs_developer_center_governance_documentation_first_principle, validate_module_cmd, doc_completeness_checker, all_example_tiers, developer_center [EXTRACTED 0.95]
- **Module Lifecycle State Flow** — docs_developer_center_core_module_lifecycle, docs_developer_center_core_module_lifecycle_contract, techforge_sdk, docs_developer_center_examples_hello_world_example, docs_developer_center_core_package_manager, docs_developer_center_core_module_registry, module_status_system [INFERRED 0.85]
- **he_module_lifecycle** — create-module, validate-module, package-module, install_module_cmd, modules_installed [INFERRED]
- **he_module_registration** — ModuleLoader, manifest.yaml, ModuleRegistry, NavigationBuilder, AppShell [INFERRED]
- **he_sdk_instantiation** — create_sdk, Module, techforge_sdk, sdk.logger, sdk.settings, sdk.storage, sdk.database, sdk.notifications [INFERRED]
- **he_service_module_contract** — ServiceModule, field_module_type, api.yaml, field_service_id, field_dependencies, field_exports, upload_file, download_file [INFERRED]
- **he_frontend_module_config** — moduleConfig, ModulePageConfig, field_id, field_icon, field_category, field_vendor, ModulePage, @techforge/sdk [INFERRED]
- **he_manifest_fields** — manifest.yaml, field_id, field_name, field_version, field_category, field_vendor, field_author, field_description, field_entry_backend, field_entry_frontend, field_icon, field_order [INFERRED]
- **Module Validation Pipeline** — module_loader, core_backend_app_module_engine_manifest_manifestparser, core_backend_app_module_engine_validator_modulevalidator, docs_developer_center_core_module_registry [INFERRED]
- **Package Management Flow** — docs_developer_center_core_package_manager, module_loader, docs_developer_center_core_module_registry, core_backend_app_module_engine_operation_log, hot_reload [INFERRED]
- **Backend Architecture** — docs_developer_center_core_module_registry, marketplace_api, registry_api, loader_journal, core_backend_app_module_engine_operation_log, docs_developer_center_core_package_manager, module_loader, core_backend_app_module_engine_manifest_manifestparser, core_backend_app_module_engine_validator_modulevalidator, core_backend_app_module_engine_repository_provider [INFERRED]

## Communities (99 total, 20 thin omitted)

### Community 0 - "Core Platform Architecture"
Cohesion: 0.05
Nodes (32): _component_name(), _len(), _make_env(), ModuleSpec, Path, TechForge CLI — Template Generator =====================================…, # TODO: create tables, default settings, initial data, # TODO: start background tasks, open connections (+24 more)

### Community 1 - "Hello World Plugin"
Cohesion: 0.05
Nodes (55): Category, create_category(), get_category(), list_categories(), AsyncSession, post, get_module_health(), get_platform_health() (+47 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (58): Module, PackageManager, PermissionError, Three Example Tiers (basic.md, advanced.md, integration.md), OperationLog, RepositoryProvider, create-module, create_sdk (+50 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (47): _completeness_to_read(), CompletenessReportRead, _contract_to_read(), DocEntryFull, DocEntryMeta, DocSummary, DoDCheckRead, export_ai_context() (+39 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (48): @techforge/sdk, AppShell, Button, Card, Core, DataTable, DeveloperCenter, EmptyState (+40 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (23): APIYamlParser, API YAML Parser ================ Parses a module's contracts/api.yaml into a…, Stateless parser for contracts/api.yaml files. Usage: contract =…, CompletenessReport, DocCompletenessChecker, DoDCheck, ServiceContract, Documentation Completeness Checker — §16 Documentation First Principle… (+15 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (17): DatabaseSDK, LoggerSDK, NotificationsSDK, ABC, Any, TechForge SDK — Service Contracts =================================== All SDK…, Per-module key-value configuration store. Phase 3: backed by a dedicated table…, Push in-app notifications to the Core header bell. Phase 3: will emit Server-… (+9 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (26): Documentation Indexer ====================== Scans all documentation sources…, AIContextExporter, Documentation Engine ===================== Process-level singleton assembly and…, Generates a single consolidated Markdown document containing the entire…, MarkdownParser, Markdown Parser ================ Reads .md files, optionally parses YAML…, Parses a single .md file into a DocEntry. Usage: entry = MarkdownParser.parse(…, DocCategory (+18 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (18): LocalRepositoryProvider, ABC, PackageInfo, Path, Repository Provider ==================== Abstraction layer between the Package…, Return path to the latest .mod file for module_id., Accept a manually uploaded .mod file and store it in cache/. Returns the path…, Extract manifest.yaml from a .mod file and return PackageInfo. (+10 more)

### Community 9 - "Community 9"
Cohesion: 0.15
Nodes (28): create_module_cmd(), command, option, techforge create-module — interactive module scaffold generator., Scaffold a new TechForge module interactively. Generates the complete directory…, package_module_cmd(), argument, command (+20 more)

### Community 10 - "Veeam M365 Integration"
Cohesion: 0.16
Nodes (25): ModuleStatus, Enum, str, Lifecycle states for a module as defined in the TechForge specification.…, LoadEvent, ModuleLoader, ModuleLoader ============ Orchestrates the complete module lifecycle pipeline…, One timestamped entry in the loader journal. (+17 more)

### Community 11 - "Documentation System"
Cohesion: 0.14
Nodes (8): make_mod_file(), make_package_manager(), Path, Create a minimal valid .mod file in tmp/., TestInstall, TestPackageManagerQueries, TestRemove, TestUpdate

### Community 12 - "Package Management"
Cohesion: 0.15
Nodes (8): Build a NavigationTree from all INSTALLED modules in the registry. Args: reg:…, ModuleRegistry, Central in-memory store for all discovered modules. Accessed by: - ModuleLoader…, Remove a module entry. No-op if not present., Remove all entries. Used during full re-scans., make_entry(), TestNavigationBuilder, ModuleEntry

### Community 13 - "API Endpoints"
Cohesion: 0.10
Nodes (23): CompatibilityBadge(), CONFIG, Props, ActionBtn(), PackageCard(), Props, Tab, Variant (+15 more)

### Community 14 - "Community 14"
Cohesion: 0.10
Nodes (15): InstallResult, PackageManager, PackageInfo, Path, Install a module from a .mod file path. Steps: 1. Validate the .mod archive…, Remove an installed module. Steps: 1. Verify it exists in the registry 2.…, Update an installed module from a newer .mod file. Steps: 1. Verify current…, List all packages available in repository/. (+7 more)

### Community 15 - "Community 15"
Cohesion: 0.16
Nodes (6): DocIndex, In-memory inverted-index of documentation entries. Rebuilt from scratch on…, Remove a doc from the index (used after module uninstall)., make_entry(), TestDocIndex, TestDocSearchEngine

### Community 16 - "Community 16"
Cohesion: 0.14
Nodes (18): Breadcrumb(), PATH_LABELS, Header(), CategorySection(), COLOR_DOT, ICON_MAP, ModuleNavItem(), Sidebar() (+10 more)

### Community 17 - "Community 17"
Cohesion: 0.14
Nodes (12): Scan docs/developer-center/ and index all .md files., _extract_h1(), _parse_frontmatter(), Path, Parse all .md files in *directory* matching *glob*. Returns entries sorted by…, Return (frontmatter_dict, body_without_frontmatter)., Return the first H1 heading text, or None., Create a stable doc ID from the file path relative to base. e.g.… (+4 more)

### Community 18 - "Community 18"
Cohesion: 0.14
Nodes (7): Path, Locate, load, and validate the manifest.yaml inside *module_path*. Validation…, _version_tuple(), veeam_m365 (order=10) should sort before hello_world (order=99) but they are in…, TestManifestParserNavFields, TestRealModuleManifests, write_manifest()

### Community 19 - "Community 19"
Cohesion: 0.12
Nodes (21): categoriesApi, modulesApi, navigationApi, CORE_NAV, NavState, Category, DocEntryFull, DocEntryMeta (+13 more)

### Community 20 - "Community 20"
Cohesion: 0.14
Nodes (9): DocIndexer, Path, ServiceContract, Scan all installed modules and index their docs., Builds and refreshes the DocIndex from all documentation sources., Clear and rebuild the entire index. Returns: Total number of documents indexed., Index (or re-index) documentation for a single module. Called by PackageManager…, Remove all docs for a module. Called after uninstall. (+1 more)

### Community 21 - "Community 21"
Cohesion: 0.08
Nodes (23): compilerOptions, allowImportingTsExtensions, baseUrl, isolatedModules, jsx, lib, module, moduleDetection (+15 more)

### Community 22 - "Community 22"
Cohesion: 0.14
Nodes (22): check_compat(), CompatibilityRequest, CompatibilityResponse, get_operation_log(), import_module(), install_module(), OperationLogRead, OperationResponse (+14 more)

### Community 23 - "Community 23"
Cohesion: 0.21
Nodes (21): get_loader_journal(), get_navigation_tree(), get_registry_module(), list_registry_modules(), NavCategoryRead, NavigationTreeRead, NavModuleRead, NavVendorRead (+13 more)

### Community 24 - "Community 24"
Cohesion: 0.19
Nodes (3): TestModuleCLIValidator, Path, TestCLIValidatorNavFields

### Community 25 - "Community 25"
Cohesion: 0.10
Nodes (22): backup sizing, compliance, advanced.md, basic.md, integration.md, overview.md, calculate_storage, sales_proposal_module (+14 more)

### Community 26 - "Community 26"
Cohesion: 0.17
Nodes (11): BuildResult, PackageBuilder, Path, TechForge CLI — Package Builder ================================== Builds a…, Builds a .mod package from a module directory., Package *module_path* into a .mod archive. Args: module_path: Absolute or…, _should_exclude(), make_valid_module() (+3 more)

### Community 27 - "Community 27"
Cohesion: 0.15
Nodes (8): _normalize_returns(), Path, ServiceContract, Normalize the `returns` field, which the official §16 spec allows as either a…, Parse an api.yaml file. Returns: ServiceContract if the file is valid, None…, TestReturnsNormalization, Path, TestAPIYamlParser

### Community 28 - "Community 28"
Cohesion: 0.10
Nodes (19): BadgeProps, badgeVariant, ButtonProps, CardProps, Column, DataTableProps, EmptyStateProps, FormFieldProps (+11 more)

### Community 29 - "Community 29"
Cohesion: 0.13
Nodes (11): DatabaseSDK, Any, Best-effort table name extraction for mock routing., Isolated database access for a single module. Each module receives its own…, Execute a SELECT query and return all matching rows. Phase 3 mock: returns rows…, Execute a SELECT query and return the first matching row, or None., Execute an INSERT, UPDATE, or DELETE statement. Phase 3 mock: stores rows in…, Batch execute a statement for multiple parameter sets. (+3 more)

### Community 30 - "Community 30"
Cohesion: 0.16
Nodes (11): Path, Read a text file. Convenience wrapper around read()., Write a text file. Convenience wrapper around write()., Resolve path relative to module base, preventing directory traversal., Isolated file storage scoped to a single module's data directory. Phase 3:…, Read a file from the module's storage directory. Args: path: Relative path…, Write bytes to a file in the module's storage directory. Creates parent…, Delete a file from the module's storage directory. No-op if the file does not… (+3 more)

### Community 31 - "Community 31"
Cohesion: 0.11
Nodes (19): autoprefixer, devDependencies, autoprefixer, postcss, tailwindcss, @types/node, @types/react, @types/react-dom (+11 more)

### Community 32 - "Community 32"
Cohesion: 0.12
Nodes (19): Examples, ModuleContract, backup_sizing, hello_world/info, hello_world/ping, veeam_m365/ping, calculate_storage, ping (+11 more)

### Community 33 - "Community 33"
Cohesion: 0.12
Nodes (11): TechForge CLI — Automated Test Suite ======================================…, ModuleContract, ABC, TechForge SDK — Module Contracts ================================== Base…, Called when the module is disabled. Stop background tasks, release connections.…, Called when upgrading from a previous version. Run migrations, transform stored…, Called when the module is permanently removed. Delete all data, tables, files…, Abstract base class for all TechForge module backends. Every module MUST… (+3 more)

### Community 34 - "Community 34"
Cohesion: 0.15
Nodes (13): CompletenessBadge(), Props, ModuleCard(), Props, Field(), ModuleDetailPanel(), Props, CONFIG (+5 more)

### Community 35 - "Community 35"
Cohesion: 0.11
Nodes (10): _DatabaseSDK, _LoggerSDK, _NotificationsSDK, TechForge SDK — Python ====================== This is the stub/skeleton for the…, Phase 2: will wrap SQLAlchemy sessions scoped to the calling module. Modules…, Phase 2: isolated file storage per module under modules/installed/<id>/data/, Phase 2: structured logging tagged with the calling module's ID., Phase 2: push notifications to the Core header bell. (+2 more)

### Community 36 - "Community 36"
Cohesion: 0.32
Nodes (12): Compatibility Checker ====================== Determines whether a package is…, CompatibilityLevel, InstallStatus, Enum, str, Trust level for a package source. Phase 5 will populate this based on…, RemoveStatus, TrustLevel (+4 more)

### Community 37 - "Community 37"
Cohesion: 0.16
Nodes (14): CATEGORY_LABELS, DocSearch(), Props, MarkdownRenderer(), Props, ExportCard(), Props, ServiceContractPanel() (+6 more)

### Community 38 - "Community 38"
Cohesion: 0.14
Nodes (14): EventRow(), LEVEL_CONFIG, LoaderJournalViewer(), Pill(), Props, completenessApi, registryApi, LoadState (+6 more)

### Community 39 - "Community 39"
Cohesion: 0.12
Nodes (17): clsx, dependencies, clsx, lucide-react, marked, @radix-ui/react-dialog, react, react-router-dom (+9 more)

### Community 40 - "Community 40"
Cohesion: 0.16
Nodes (9): Any, Path, Per-module persistent settings backed by a JSON file. Thread-safe for single-…, Retrieve a setting value. Args: key: Setting name. default: Value to return if…, Store a setting value. Persists immediately to disk. Args: key: Setting name…, Remove a setting. No-op if the key does not exist., Return a snapshot of all current settings., Delete all settings for this module. Called by ModuleContract.uninstall() to… (+1 more)

### Community 41 - "Community 41"
Cohesion: 0.15
Nodes (7): ModuleStatus, Register a failed module so it appears in the UI with its error state., ModuleEntry, ModuleStatus, Add or replace a module entry in the registry., Update the status of an already-registered module. Returns True if the module…, One entry in the module registry. Combines manifest data with runtime state so…

### Community 42 - "Community 42"
Cohesion: 0.20
Nodes (8): CheckResult, ModuleCLIValidator, Path, TechForge CLI — Module Validator ================================== Standalone…, §16 — Documentation First Principle. A module is not "done" without:…, §16 — every export in api.yaml must declare: name, description, parameters…, Validates a module directory and returns a detailed ValidationReport. Usage:…, ValidationReport

### Community 43 - "Community 43"
Cohesion: 0.16
Nodes (9): LoaderJournal ============= Simple process-lifetime store for the most recent…, LoaderResult, Path, Validate and register a single module directory., Summary returned after a full scan., Full startup scan. 1. Clear the registry (idempotent — safe to call multiple…, Path, Run all validation checks on *module_path*. Checks (in order): 1. manifest.yaml… (+1 more)

### Community 44 - "Community 44"
Cohesion: 0.21
Nodes (5): OperationLog, OperationLogEntry, Package Manager Operation Log ================================ Records every…, In-process ring buffer of Package Manager events., TestOperationLog

### Community 45 - "Community 45"
Cohesion: 0.16
Nodes (11): StatCard(), StatCardProps, Status, STATUS_CONFIG, StatusBadge(), StatusBadgeProps, platformApi, DashboardPage() (+3 more)

### Community 46 - "Community 46"
Cohesion: 0.16
Nodes (8): Notification, NotificationsSDK, SDK Notifications Service ========================== Push in-app notifications…, Mark a notification as read by its ID., Discard all notifications for this module., In-process notification queue for one module. The Core API drains this queue…, Enqueue a notification for the Core UI to display. Args: title: Short headline…, Return all unread notifications.

### Community 48 - "Community 48"
Cohesion: 0.24
Nodes (5): CompatibilityLevel, check_compatibility(), Check whether *platform_version* falls within [min_version, max_version]. Args:…, _vt(), TestCompatibility

### Community 49 - "Community 49"
Cohesion: 0.19
Nodes (6): PackageInfo, Path, Full metadata about a package — either from a .mod file in the repository or…, True when the repository has a newer version than what is installed., _version_tuple(), TestPackageInfo

### Community 50 - "Community 50"
Cohesion: 0.21
Nodes (4): HealthResult, Any, Return the current health state of the module. Called periodically by the Core…, Returned by health_check().

### Community 51 - "Community 51"
Cohesion: 0.17
Nodes (9): NavCategoryNode, NavigationTree, NavModuleNode, NavVendorNode, Navigation Tree Builder ======================== Builds the hierarchical…, Leaf node — one installed module., Mid-level node — one vendor within a category., Top-level node — one category. (+1 more)

### Community 52 - "Community 52"
Cohesion: 0.17
Nodes (12): Badge(), Button(), Card(), cn(), DataTable(), EmptyState(), LoadingState(), Modal() (+4 more)

### Community 53 - "Community 53"
Cohesion: 0.21
Nodes (6): ModuleSettings, navigationSDK, NotificationLevel, notificationsSDK, sdk, settingsSDK

### Community 55 - "Community 55"
Cohesion: 0.24
Nodes (7): AppRouter(), AppShell(), ComingSoon(), ComingSoonProps, stored, MarketplacePage(), SettingsPage()

### Community 56 - "Community 56"
Cohesion: 0.18
Nodes (4): ping(), veeam_m365 — Backend Entry Point =================================== Module :…, Calcula uma estimativa simplificada de storage para backup M365. Esta é uma…, VeeamM365Module

### Community 57 - "Community 57"
Cohesion: 0.20
Nodes (9): name, private, scripts, build, dev, lint, preview, type (+1 more)

### Community 58 - "Community 58"
Cohesion: 0.33
Nodes (4): HelloWorldModule, info(), ping(), hello_world — Backend Entry Point =================================== Reference…

### Community 59 - "Community 59"
Cohesion: 0.20
Nodes (5): TechForge SDK — Core ===================== Assembles all SDK services into a…, SDK Database Service ==================== Provides isolated database access for…, SDK Logger Service — Phase 3 (functional), SDK Settings Service ===================== Per-module key-value configuration…, SDK Storage Service ==================== Sandboxed file storage for module…

### Community 61 - "Community 61"
Cohesion: 0.25
Nodes (5): create_sdk(), Path, Root SDK object. Module backends should call create_sdk(module_id) to get a…, Factory function — creates an SDK instance scoped to *module_id*. Call this at…, TechForgeSDK

### Community 64 - "Community 64"
Cohesion: 0.29
Nodes (6): cls, colors, fontSize, fontWeight, radius, spacing

### Community 65 - "Community 65"
Cohesion: 0.33
Nodes (3): ModuleMetadata, Static identity information about a module. Mirrors the fields declared in…, Return the module's static identity information. Must match the values in…

### Community 68 - "Community 68"
Cohesion: 0.40
Nodes (4): Notification, notificationsSDK, sdk, settingsSDK

### Community 69 - "Community 69"
Cohesion: 0.40
Nodes (3): ModuleLifecycleHooks, ModulePageConfig, ModuleSubRoute

### Community 70 - "Community 70"
Cohesion: 0.50
Nodes (4): cli(), TechForge Module Development CLI \b Commands: create-module Scaffold a new…, group, version_option

### Community 71 - "Community 71"
Cohesion: 0.50
Nodes (3): plugin, $schema, file:///D:/Github/Tech.Forge/.kilo/plugins/graphify.js

## Knowledge Gaps
- **139 isolated node(s):** `$schema`, `file:///D:/Github/Tech.Forge/.kilo/plugins/graphify.js`, `name`, `private`, `version` (+134 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ModuleCLIValidator` connect `Community 42` to `Core Platform Architecture`, `Community 33`, `Community 5`, `Community 9`, `Package Management`, `Community 47`, `Community 18`, `Community 24`, `Community 26`, `Community 27`, `Community 63`?**
  _High betweenness centrality (0.168) - this node is a cross-community bridge._
- **Why does `ModuleLoader` connect `Veeam M365 Integration` to `Hello World Plugin`, `Community 36`, `Community 41`, `Community 43`, `Package Management`, `Community 14`, `Community 18`, `Community 24`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Why does `ManifestParser` connect `Veeam M365 Integration` to `Community 24`, `Community 18`, `Community 2`, `Package Management`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `DocIndex` (e.g. with `DocIndexer` and `AIContextExporter`) actually correct?**
  _`DocIndex` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ModuleRegistry` (e.g. with `ModuleStatus` and `ParsedManifest`) actually correct?**
  _`ModuleRegistry` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `DocIndexer` (e.g. with `APIYamlParser` and `MarkdownParser`) actually correct?**
  _`DocIndexer` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `DocCategory` (e.g. with `CompletenessReportRead` and `DocEntryFull`) actually correct?**
  _`DocCategory` has 20 INFERRED edges - model-reasoned connections that need verification._