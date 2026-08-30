"""Splash UI — banner + progress checklist (launcher/techforge_launcher/splash.py).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase6_splash.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO / "launcher"))

from techforge_launcher.splash import STEPS, Splash  # noqa: E402

pytestmark = pytest.mark.unit


def test_disabled_splash_never_prints(capsys):
    splash = Splash(enabled=False)
    splash.step("Ambiente")
    splash.done(1.0)
    assert capsys.readouterr().out == ""


def test_disabled_splash_has_no_color():
    assert Splash(enabled=False).color is False


def test_step_render_tracks_printed_line_count(capsys, monkeypatch):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    splash = Splash(enabled=True)
    splash.step("Ambiente")
    out = capsys.readouterr().out
    assert splash._last_line_count == out.count("\n")


def test_all_steps_appear_in_final_render(monkeypatch):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    splash = Splash(enabled=True)
    rendered = []
    monkeypatch.setattr("builtins.print", lambda text, **kw: rendered.append(text))
    for name in STEPS:
        splash.step(name)
    last_render = rendered[-1]
    for name in STEPS:
        assert name in last_render


def test_clear_never_goes_negative_on_first_render(capsys, monkeypatch):
    """Regressão: `step()` chamava `_clear()` antes de qualquer render
    anterior existir — garantir que o primeiro passo não tenta limpar
    linhas que nunca foram impressas."""
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    splash = Splash(enabled=True)
    splash.step("Ambiente")  # não deve lançar exceção nem limpar nada indevido
    assert splash._last_line_count > 0
