"""ModulePaths — Fase 12 §20/§21.

Caminhos oficiais de um módulo instalado — nenhum módulo monta caminho
arbitrário na mão, todos vêm daqui (via `ModuleExecutionContext.paths`).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModulePaths:
    root:    Path  # modules/installed/<id>/ — raiz do módulo (código + manifest)
    data:    Path  # dados persistentes do módulo (nunca apagados em update)
    cache:   Path  # dados descartáveis, sem TTL próprio garantido
    exports: Path  # relatórios/CSV/XLSX/PDF gerados pelo módulo
    temp:    Path  # arquivos de vida curta de uma execução

    @classmethod
    def for_module(cls, module_root: Path) -> "ModulePaths":
        return cls(
            root=module_root,
            data=module_root / "data",
            cache=module_root / "cache",
            exports=module_root / "exports",
            temp=module_root / "temp",
        )

    def ensure_exist(self) -> None:
        for path in (self.data, self.cache, self.exports, self.temp):
            path.mkdir(parents=True, exist_ok=True)
