"""Fase 15 §7/§8 — extrai chamadas executáveis dos exemplos de um ServiceExport.

Nem todo exemplo documentado é uma chamada Python (alguns são HTTP, tipo
`GET /api/v1/modules/x/ping`) — só os que casam com `nome_do_export(...)` e
têm apenas keyword arguments literais são extraídos; o resto é ignorado.
"""
from __future__ import annotations

import ast
import re

from app.doc_engine.models import ServiceExport


def extract_example_calls(export: ServiceExport) -> list[dict]:
    """Retorna a lista de kwargs de cada exemplo executável de `export`."""
    pattern = re.compile(rf"\b{re.escape(export.name)}\(([^)]*)\)")
    calls: list[dict] = []
    for example in export.examples:
        match = pattern.search(example)
        if not match:
            continue
        try:
            call_node = ast.parse(f"f({match.group(1)})", mode="eval").body
        except SyntaxError:
            continue
        if not isinstance(call_node, ast.Call) or call_node.args:
            continue
        kwargs: dict = {}
        for kw in call_node.keywords:
            if kw.arg is None:
                kwargs = None
                break
            try:
                kwargs[kw.arg] = ast.literal_eval(kw.value)
            except (ValueError, SyntaxError):
                kwargs = None
                break
        if kwargs is not None:
            calls.append(kwargs)
    return calls
