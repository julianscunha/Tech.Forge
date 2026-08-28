"""
SDK Services — Fase 9 §9
============================
Proxy fino, somente leitura, pro Service Registry do Core (Fase 8) — pra
um módulo descobrir capabilities sem reimplementar discovery. Mesmo padrão
de isolamento de `notifications`: o SDK nunca importa `app.*` diretamente,
só fala com o Core via a API HTTP local (módulos rodam no mesmo processo
do Core, mas atravessam a fronteira do pacote sempre por HTTP).

Usage:
    from techforge_sdk import sdk

    providers = sdk.services.find_capability("aws.cost.read")
    descriptor = sdk.services.get("aws_cost_service")
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Optional

logger = logging.getLogger("techforge.sdk.services")


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

    def _get(self, path: str) -> Any:
        url = f"{self.core_api_url.rstrip('/')}{path}"
        try:
            with urllib.request.urlopen(url, timeout=self.http_timeout) as resp:
                return json.loads(resp.read())
        except Exception as exc:
            logger.debug("[%s] services SDK call to %s failed: %s", self._module_id, path, exc)
            return None
