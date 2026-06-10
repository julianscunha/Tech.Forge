"""
TechForge CLI — Console helpers
================================
Centralised Rich console and styled output helpers.
Every command imports from here so styling is consistent.
"""
from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

THEME = Theme({
    "title":    "bold white",
    "success":  "bold green",
    "warning":  "bold yellow",
    "error":    "bold red",
    "info":     "cyan",
    "muted":    "dim white",
    "accent":   "bold blue",
    "path":     "bold cyan",
    "version":  "dim cyan",
    "pass":     "green",
    "fail":     "red",
    "warn":     "yellow",
    "header":   "bold white on blue",
})

console = Console(theme=THEME)


# ── Styled print helpers ──────────────────────────────────────────────────────

def print_header(text: str) -> None:
    console.print(f"\n[accent]❯[/accent] [title]{text}[/title]")


def print_success(text: str) -> None:
    console.print(f"  [success]✓[/success] {text}")


def print_error(text: str) -> None:
    console.print(f"  [error]✗[/error] {text}")


def print_warning(text: str) -> None:
    console.print(f"  [warning]⚠[/warning] {text}")


def print_info(text: str) -> None:
    console.print(f"  [info]·[/info] {text}")


def print_muted(text: str) -> None:
    console.print(f"    [muted]{text}[/muted]")


def print_section(text: str) -> None:
    console.print(f"\n[muted]──[/muted] [title]{text}[/title]")


def print_banner() -> None:
    console.print(
        "\n[accent]"
        "  ████████╗███████╗ ██████╗██╗  ██╗███████╗ ██████╗ ██████╗  ██████╗ ███████╗\n"
        "     ██╔══╝██╔════╝██╔════╝██║  ██║██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝\n"
        "     ██║   █████╗  ██║     ███████║█████╗  ██║   ██║██████╔╝██║  ███╗█████╗  \n"
        "     ██║   ██╔══╝  ██║     ██╔══██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  \n"
        "     ██║   ███████╗╚██████╗██║  ██║██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗\n"
        "     ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝\n"
        "[/accent]"
        "[muted]  Module Development CLI  v1.0.0[/muted]\n"
    )
