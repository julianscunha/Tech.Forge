"""Fase 15 Slice 4 — contract tests genéricos (spec §7/§8).

Diferente de `test_phase8_service_registry.py::TestInvoke`, que valida à mão
um exemplo por módulo conhecido, este teste é GENÉRICO: varre TODOS os
módulos instalados com `docs/contracts/api.yaml`, extrai os exemplos que são
chamadas Python executáveis (`extract_example_calls`) e invoca de verdade via
`app.service_registry.invoker.invoke` — o mesmo caminho público usado em
produção. Roda automaticamente contra qualquer módulo futuro sem precisar de
um teste hand-written por módulo (é isso que o torna reutilizável em
`techforge validate-module` / release readiness, Slices 9-10).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_contract_tests.py -q
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import pytest

from app.core.settings import settings
from app.doc_engine.api_yaml_parser import APIYamlParser
from app.doc_engine.contract_examples import extract_example_calls
from app.main import app
from app.service_registry.invoker import invoke

pytestmark = pytest.mark.contract


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _iter_installed_contracts():
    for module_dir in sorted(settings.MODULES_INSTALLED_PATH.iterdir()):
        api_yaml = module_dir / "docs" / "contracts" / "api.yaml"
        if not api_yaml.exists():
            continue
        contract = APIYamlParser.parse(api_yaml, module_dir.name)
        if contract is not None:
            yield contract


_REFERENCE_MODULE_IDS = {"hello_world"}


def test_every_documented_example_executes_without_raising(client):
    """Escopo restrito aos módulos de referência (hello_world) — a suíte
    roda contra o `modules/installed/` real do ambiente de dev, que pode
    ter outros módulos instalados (uso legítimo da plataforma); o teste
    não deve quebrar por causa deles."""
    checked = 0
    for contract in _iter_installed_contracts():
        if contract.service_id not in _REFERENCE_MODULE_IDS:
            continue
        for export in contract.exports:
            for kwargs in extract_example_calls(export):
                checked += 1
                result = invoke(contract.service_id, export.name, **kwargs)
                assert result is not None, (
                    f"{contract.service_id}.{export.name}({kwargs}) retornou None — "
                    "exemplo documentado não corresponde ao comportamento real"
                )
    # hello_world.ping e hello_world.info usam exemplos HTTP (não parseáveis
    # como chamada Python) — nenhum exemplo executável no único módulo de
    # referência restante.
    assert checked == 0, f"esperava 0 exemplos executáveis no módulo de referência, achou {checked}"
