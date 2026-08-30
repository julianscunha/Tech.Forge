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

_ORANGE = "\x1b[38;5;208m"
_DIM = "\x1b[2m"
_BOLD = "\x1b[1m"
_RESET = "\x1b[0m"

_BANNER = r"""
  _____         _      ______
 |_   _|__  ___| |__  |  ____|__  _ __ __ _  ___
   | |/ _ \/ __| '_ \ | |__ / _ \| '__/ _` |/ _ \
   | |  __/ (__| | | ||  __| (_) | | | (_| |  __/
   |_|\___|\___|_| |_||_|   \___/|_|  \__, |\___|
                                       |___/
""".strip("\n")


class Splash:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled and sys.stdout is not None and sys.stdout.isatty()
        self.color = self.enabled and (sys.platform != "win32" or _supports_ansi_on_windows())
        self._current = -1
        self._last_line_count = 0

    # ── internal ──────────────────────────────────────────────────────────────

    def _c(self, text: str, code: str) -> str:
        return f"{code}{text}{_RESET}" if self.color else text

    def _render(self, done: list[str], current: str | None) -> None:
        lines = [""]
        lines += [self._c(line, _ORANGE) for line in _BANNER.splitlines()]
        lines.append("")
        for name in STEPS:
            if name in done:
                marker = self._c("✓", _ORANGE)
            elif current == name:
                marker = self._c("●", _BOLD)
            else:
                marker = self._c("○", _DIM)
            lines.append(f"  {marker} {name}")
        if current:
            lines += ["", self._c("Inicializando... aguarde.", _DIM)]
        text = "\n".join(lines)
        print(text, flush=True)
        self._last_line_count = text.count("\n") + 1

    def _clear(self) -> None:
        for _ in range(self._last_line_count):
            sys.stdout.write("\x1b[1A\x1b[2K")  # move up + clear line
        sys.stdout.flush()

    # ── public ────────────────────────────────────────────────────────────────

    def step(self, name: str) -> None:
        if not self.enabled:
            return
        if self._current >= 0:
            self._clear()
        self._render(STEPS[:self._current + 1], name)
        self._current += 1

    def done(self, elapsed: float) -> None:
        if self.enabled:
            self._clear()
            print(self._c(f"✓ TechForge está pronto ({elapsed:.1f}s).", _ORANGE))

    def fail(self, message: str) -> None:
        if self.enabled:
            self._clear()
        print(message)
        print("[Os detalhes técnicos estão em logs/launcher.log]")


def _supports_ansi_on_windows() -> bool:
    """Windows Terminal/PowerShell 7+/VS Code integrated terminal handle ANSI
    fine; legacy cmd.exe often doesn't unless VT processing was enabled.
    WT_SESSION/TERM_PROGRAM are reliable signals; ANSICON covers older setups."""
    import os

    return bool(os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM") or os.environ.get("ANSICON"))
