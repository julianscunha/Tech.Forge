"""
SDK Services — Fase 9 §9 / invoke (dependência entre módulos)
==================================================================
Proxy fino pro Service Registry do Core (Fase 8) — descoberta de
capabilities e invocação de exports públicos. Mesmo padrão de isolamento
de `notifications`: o SDK nunca importa `app.*` diretamente, só fala com
o Core via a API HTTP local (módulos rodam no mesmo processo do Core,
mas atravessam a fronteira do pacote sempre por HTTP).

Usage:
    from techforge_sdk import sdk

    providers = sdk.services.find_capability("aws.cost.read")
    descriptor = sdk.services.get("aws_cost_service")
    info = sdk.services.invoke("system_information_service", "get_cpu_info")
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Optional

logger = logging.getLogger("techforge.sdk.services")


class ServiceInvokeError(Exception):
    """Erro tipado de uma chamada `invoke()` — espelha o `code` do
    Service Registry do Core (SERVICE_NOT_FOUND, INVALID_ARGUMENTS etc.)
    pra quem consome poder distinguir os cenários do §7 (ausente vs.
    incompatível vs. falha de execução) sem parsear texto."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ServicesSDK:
    DEFAULT_CORE_URL = "http://127.0.0.1:8000/api/v1"

    def __init__(self, module_id: str) -> None:
        self._module_id = module_id
        self.core_api_url: str = self.DEFAULT_CORE_URL
        self.http_timeout: float = 2.0

    def find_capability(self, capability: str) -> list[dict[str, Any]]:
        """Serviço(s) que provêm uma capability, ou lista vazia se nenhum
        (ou se o Core não estiver acessível)."""
        return self._get(f"/services/capabilities/{capability}") or []

    def get(self, service_id: str) -> Optional[dict[str, Any]]:
        """Descritor de um serviço pelo id, ou None se não encontrado/indisponível."""
        return self._get(f"/services/{service_id}")

    def invoke(self, service_id: str, export_name: str, **kwargs: Any) -> Any:
        """Invoca um export público e já validado do contrato de outro
        módulo (dependência declarada no manifest, Fase 8.1) — nunca
        importar o código do outro módulo diretamente.

        Raises:
            ServiceInvokeError: com `.code` igual ao erro do Service
            Registry (SERVICE_NOT_FOUND, SERVICE_DISABLED,
            SERVICE_UNAVAILABLE, CAPABILITY_NOT_FOUND, CONTRACT_VIOLATION,
            INVALID_ARGUMENTS, SERVICE_EXECUTION_FAILED) — ou com code
            "SERVICE_UNREACHABLE" se o Core local não respondeu.
        """
        url = f"{self.core_api_url.rstrip('/')}/services/{service_id}/invoke/{export_name}"
        body = json.dumps(kwargs).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, method="POST", headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self.http_timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            detail = json.loads(exc.read() or b"{}")
            error = detail.get("detail", detail)
            code = error.get("code", "SERVICE_ERROR") if isinstance(error, dict) else "SERVICE_ERROR"
            message = error.get("message", str(error)) if isinstance(error, dict) else str(error)
            raise ServiceInvokeError(code, message) from None
        except Exception as exc:
            logger.debug("[%s] services SDK invoke %s.%s failed: %s",
                        self._module_id, service_id, export_name, exc)
            raise ServiceInvokeError("SERVICE_UNREACHABLE", str(exc)) from None

    def _get(self, path: str) -> Any:
        url = f"{self.core_api_url.rstrip('/')}{path}"
        try:
            with urllib.request.urlopen(url, timeout=self.http_timeout) as resp:
                return json.loads(resp.read())
        except Exception as exc:
            logger.debug("[%s] services SDK call to %s failed: %s", self._module_id, path, exc)
            return None
