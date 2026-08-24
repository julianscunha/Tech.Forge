"""
TechForge Launcher — CLI entry point
=====================================
    python -m techforge_launcher start   → full startup
    python -m techforge_launcher stop    → coordinated shutdown
    python -m techforge_launcher status  → component states
"""
from __future__ import annotations

import argparse
import sys


def _fmt_state(state: str) -> str:
    return {"READY": "READY", "STOPPED": "STOPPED", "FAILING": "FAILING",
            "UNKNOWN": "UNKNOWN"}.get(state, state)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="TechForge Launcher")
    parser.add_argument("command", choices=["start", "stop", "status"],
                        help="start: iniciar plataforma · stop: encerrar · status: estado atual")
    parser.add_argument("--no-splash", action="store_true",
                        help="disable the console startup screen")
    args = parser.parse_args(argv)

    from techforge_launcher import start, stop, status

    if args.command == "start":
        ok, message = start(splash=not args.no_splash)
        if not ok and "--quiet" not in (argv or []):
            print(message)
        elif not message.startswith("TechForge já"):
            print(message)
        else:
            print(message)  # already running — inform, do not fail
        return 0 if ok else 1

    if args.command == "stop":
        ok, message = stop()
        print(message)
        return 0 if ok else 1

    # status
    ps = status()
    print("\nTechForge")
    for comp in (ps.launcher, ps.backend, ps.frontend, ps.database, ps.runtime):
        print(f"  {comp.name:<12} {_fmt_state(comp.state)}"
              + (f"  ({comp.detail})" if comp.detail else ""))
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
