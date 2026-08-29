"""
ModuleExecutionContext — Fase 9 §8 Slice 4
==============================================
Forma oficial (lado Core) de descrever a que recursos uma execução de
módulo tem acesso: identidade, Service Registry, logger, caminhos,
configuração e um slot de cancelamento (preenchido na Slice 5). Não é
injetado como parâmetro nos hooks do ModuleContract (que já têm assinatura
fixa desde a Fase 3) — é a estrutura que o Runtime usa internamente para
rastrear e, futuramente, para as APIs de execução.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from app.core.settings import settings
from app.module_runtime.paths import ModulePaths
from app.security.secret_store import ModuleSecretStore
from app.services.module_storage import ModuleKVStorage


@dataclass
class ModuleExecutionContext:
    module_id:      str
    module_version: str
    runtime_id:     str
    configuration:  dict[str, Any]
    services:       Any
    logger:         logging.Logger
    paths:          ModulePaths
    storage:        ModuleKVStorage
    secrets:        ModuleSecretStore
    cancellation:   Optional[Any] = None
    metadata:       dict[str, Any] = field(default_factory=dict)

    @classmethod
    def build(cls, module_id: str, module_registry) -> Optional["ModuleExecutionContext"]:
        """Retorna None se o módulo não estiver registrado — não há
        contexto de execução pra um módulo que o Core não conhece."""
        entry = module_registry.get(module_id)
        if entry is None:
            return None

        from app.service_registry.registry import service_registry

        return cls(
            module_id=module_id,
            module_version=entry.version,
            runtime_id=str(uuid.uuid4()),
            configuration={},
            services=service_registry,
            logger=logging.getLogger(f"techforge.module.{module_id}"),
            paths=ModulePaths.for_module(settings.MODULES_INSTALLED_PATH / module_id),
            storage=ModuleKVStorage(module_id),
            secrets=ModuleSecretStore(module_id),
        )
