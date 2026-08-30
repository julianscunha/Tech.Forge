"""Fase 15 Slice 4 — unit tests do parser de exemplos executáveis.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_contract_examples_parser.py -q
"""
from __future__ import annotations

import pytest

from app.doc_engine.contract_examples import extract_example_calls
from app.doc_engine.models import ServiceExport

pytestmark = pytest.mark.unit


def _export(name: str, examples: list[str]) -> ServiceExport:
    return ServiceExport(name=name, description="", parameters=[], returns=None, examples=examples)


def test_extracts_kwargs_from_a_valid_call_example():
    export = _export("calculate_storage", ["result = await calculate_storage(users=500, mailbox_quota_gb=50)"])
    assert extract_example_calls(export) == [{"users": 500, "mailbox_quota_gb": 50}]


def test_skips_http_style_examples():
    export = _export("ping", ["GET /api/v1/modules/hello_world/ping"])
    assert extract_example_calls(export) == []


def test_skips_examples_with_positional_arguments():
    export = _export("calculate_storage", ["calculate_storage(500, 50)"])
    assert extract_example_calls(export) == []


def test_skips_examples_with_non_literal_values():
    export = _export("calculate_storage", ["calculate_storage(users=get_count())"])
    assert extract_example_calls(export) == []


def test_extracts_multiple_examples_independently():
    export = _export(
        "calculate_storage",
        [
            "calculate_storage(users=500, mailbox_quota_gb=50)",
            "calculate_storage(users=1000, mailbox_quota_gb=100)",
        ],
    )
    assert extract_example_calls(export) == [
        {"users": 500, "mailbox_quota_gb": 50},
        {"users": 1000, "mailbox_quota_gb": 100},
    ]
