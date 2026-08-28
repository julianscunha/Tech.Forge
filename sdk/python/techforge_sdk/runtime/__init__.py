"""
SDK Runtime — Fase 9 §9/§18
===============================
Proxy fino, somente leitura do próprio estado de execução (Runtime State,
health) via a API HTTP do Core — mesmo padrão de isolamento de
`sdk.services`/`sdk.notifications`.

Usage:
    from techforge_sdk import sdk

    state = sdk.runtime.state()  # {"state": "READY", "last_error": None, ...} ou None
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Optional

logger = logging.getLogger("techforge.sdk.runtime")


class RuntimeSDK:
    DEFAULT_CORE_URL = "http://127.0.0.1:8000/api/v1"

    def __init__(self, module_id: str) -> None:
        self._module_id = module_id
        self.core_api_url: str = self.DEFAULT_CORE_URL
        self.http_timeout: float = 2.0

    def state(self) -> Optional[dict[str, Any]]:
        """Runtime State atual do próprio módulo, ou None se indisponível
        (Core fora do ar, ou módulo sem entrada de Runtime State ainda)."""
        url = f"{self.core_api_url.rstrip('/')}/runtime/modules/{self._module_id}"
        try:
            with urllib.request.urlopen(url, timeout=self.http_timeout) as resp:
                return json.loads(resp.read())
        except Exception as exc:
            logger.debug("[%s] runtime SDK call failed: %s", self._module_id, exc)
            return None
