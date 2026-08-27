"""
API YAML Parser
================
Parses a module's contracts/api.yaml into a typed ServiceContract.

Expected api.yaml format:
    service_id: my_service
    description: What this service does
    version: 1.0.0
    dependencies: [other_service]
    capabilities: [my_service.read, my_service.summary]
    exports:
      - name: my_function
        description: What it does
        parameters:
          - name: input
            type: str
            description: The input value
        returns: str
        examples:
          - "my_function('hello') → 'HELLO'"
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.doc_engine.models import ServiceContract, ServiceExport

try:
    import yaml as _yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


def _normalize_returns(value) -> Optional[str]:
    """
    Normalize the `returns` field, which the official §16 spec allows as
    either a plain string ("str") or a structured mapping ({type: X}).

    Examples:
        returns: str               → "str"
        returns: {type: CostSummary[]}  → "CostSummary[]"
    """
    if value is None:
        return None
    if isinstance(value, dict):
        t = value.get("type")
        return str(t) if t else None
    text = str(value).strip()
    return text or None


class APIYamlParser:
    """
    Stateless parser for contracts/api.yaml files.

    Usage:
        contract = APIYamlParser.parse(
            path=Path("modules/installed/my_module/docs/contracts/api.yaml"),
            module_id="my_module",
        )
    """

    @staticmethod
    def parse(path: Path, module_id: str) -> Optional[ServiceContract]:
        """
        Parse an api.yaml file.

        Returns:
            ServiceContract if the file is valid, None otherwise.
        """
        if not path.exists() or not _HAS_YAML:
            return None

        try:
            raw: dict = _yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            return None

        if not isinstance(raw, dict):
            return None

        service_id = str(raw.get("service_id", module_id)).strip()
        description = str(raw.get("description", "")).strip()
        version = str(raw.get("version", "1.0.0")).strip()
        dependencies = list(raw.get("dependencies", []))
        capabilities = [str(c) for c in raw.get("capabilities", [])]

        exports: list[ServiceExport] = []
        for exp in raw.get("exports", []):
            if not isinstance(exp, dict):
                continue
            params = []
            for p in exp.get("parameters", []):
                if isinstance(p, dict):
                    params.append({
                        "name":        str(p.get("name", "")),
                        "type":        str(p.get("type", "any")),
                        "description": str(p.get("description", "")),
                        "required":    bool(p.get("required", True)),
                    })
            exports.append(ServiceExport(
                name=str(exp.get("name", "")).strip(),
                description=str(exp.get("description", "")).strip(),
                parameters=params,
                returns=_normalize_returns(exp.get("returns")),
                examples=list(exp.get("examples", [])),
            ))

        return ServiceContract(
            service_id=service_id,
            module_id=module_id,
            description=description,
            version=version,
            exports=exports,
            dependencies=dependencies,
            capabilities=capabilities,
            raw=raw,
        )
