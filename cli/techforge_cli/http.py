"""Cliente HTTP fino compartilhado para falar com o Core local (127.0.0.1:8000).

Consolida o padrão urllib.request + tratamento de erro que estava
reimplementado quase idêntico em ~11 arquivos de `commands/` (achado em
auditoria de over-engineering — cada arquivo tinha seu próprio `_get`/
`_core_get`/`_post`, um deles chegando a comentar "mesmo padrão já usado
em modules.py" e duplicar de qualquer jeito).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from techforge_cli.config import CORE_BASE_URL
from techforge_cli.console import print_error

_UNREACHABLE = "Plataforma não acessível ({reason}). Use 'techforge start'."


def core_get(path: str, *, timeout: float = 15, raw: bool = False) -> Any:
    """GET em `{CORE_BASE_URL}{path}`. Devolve JSON decodificado (ou texto
    cru se raw=True). Sai com código 1 se a plataforma não responder."""
    try:
        with urllib.request.urlopen(f"{CORE_BASE_URL}{path}", timeout=timeout) as resp:
            data = resp.read()
            return data.decode("utf-8") if raw else json.loads(data)
    except urllib.error.HTTPError as exc:
        print_error(exc.read().decode("utf-8", errors="replace"))
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print_error(_UNREACHABLE.format(reason=exc.reason))
        raise SystemExit(1)


def core_post(path: str, payload: dict | None = None, *, method: str = "POST",
              timeout: float = 15, raise_on_error: bool = True) -> Any:
    """POST/PUT/DELETE em `{CORE_BASE_URL}{path}`, devolve JSON decodificado
    (ou {"ok": True} se a resposta não tiver corpo). Por padrão sai com
    código 1 em erro; com raise_on_error=False devolve
    {"ok": False, "detail": ...} pro caller decidir — usado por fluxos de
    lifecycle que já compõem sua própria mensagem de sucesso/erro."""
    body = json.dumps(payload).encode("utf-8") if payload is not None else b""
    req = urllib.request.Request(
        f"{CORE_BASE_URL}{path}", data=body, method=method,
        headers={"Content-Type": "application/json"} if payload is not None else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {"ok": True}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if not raise_on_error:
            return {"ok": False, "detail": detail}
        print_error(detail)
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        detail = _UNREACHABLE.format(reason=exc.reason)
        if not raise_on_error:
            return {"ok": False, "detail": detail}
        print_error(detail)
        raise SystemExit(1)


def core_post_raw(path: str, *, timeout: float = 30) -> bytes:
    """POST sem payload, devolve o corpo bruto da resposta — usado por
    exports binários (ex: support bundle ZIP)."""
    req = urllib.request.Request(f"{CORE_BASE_URL}{path}", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        print_error(_UNREACHABLE.format(reason=exc.reason))
        raise SystemExit(1)
