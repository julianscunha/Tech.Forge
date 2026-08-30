"""
SDK Logger Service — Phase 3 (functional)
"""
from __future__ import annotations

import logging
from typing import Any


class LoggerSDK:
    def __init__(self, module_id: str) -> None:
        self._module_id = module_id
        self._log = logging.getLogger(f"techforge.module.{module_id}")

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log.debug(self._fmt(message, args, kwargs))

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log.info(self._fmt(message, args, kwargs))

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log.warning(self._fmt(message, args, kwargs))

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log.error(self._fmt(message, args, kwargs))

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log.critical(self._fmt(message, args, kwargs))

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log.exception(self._fmt(message, args, kwargs))

    def _fmt(self, message: str, args: tuple, kwargs: dict) -> str:
        try:
            if args:
                message = message % args
        except (TypeError, ValueError):
            message = f"{message} {args}"
        if kwargs:
            message = f"{message} | " + " ".join(f"{k}={v!r}" for k, v in kwargs.items())
        return message
