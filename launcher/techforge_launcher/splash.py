"""
Splash / Startup screen (Phase 6 — §7)
=======================================
Extremely simple console progress display. Disappears (clears) when the
platform is ready. On failure shows a plain-language message; technical
detail stays in logs/launcher.log.
"""
from __future__ import annotations

import sys

STEPS = ["Ambiente", "Backend", "Frontend", "Plataforma"]


class Splash:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled and sys.stdout is not None and sys.stdout.isatty()
        self._current = -1

    # ── internal ──────────────────────────────────────────────────────────────

    def _render(self, done: list[str], current: str | None) -> None:
        lines = ["", "TechForge", ""]
        for name in STEPS:
            if name in done:
                marker = "✓"
            elif current == name:
                marker = "●"
            else:
                marker = "○"
            lines.append(f"  {marker} {name}")
        if current:
            lines += ["", "Inicializando... aguarde."]
        print("\n".join(lines), flush=True)

    def _clear(self, n: int = 10) -> None:
        for _ in range(n):
            sys.stdout.write("\x1b[1A\x1b[2K")  # move up + clear line
        sys.stdout.flush()

    # ── public ────────────────────────────────────────────────────────────────

    def step(self, name: str) -> None:
        if not self.enabled:
            return
        self._render(STEPS[:self._current + 1], name)
        self._current += 1

    def done(self, elapsed: float) -> None:
        if self.enabled:
            self._clear()
            print(f"TechForge está pronto ({elapsed:.1f}s).")

    def fail(self, message: str) -> None:
        if self.enabled:
            self._clear()
        print(message)
        print("[Os detalhes técnicos estão em logs/launcher.log]")
