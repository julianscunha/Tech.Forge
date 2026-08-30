"""
TechForge Fase 14 Slice 1 — Logger central + Log Context
==========================================================
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.observability.context import bind_log_context, get_log_context
from app.observability.logging_setup import JsonLogFormatter, LogContextFilter, configure_logging
from app.observability.retention import cleanup_old_logs

pytestmark = pytest.mark.unit


def make_record(name="techforge.core", level=logging.INFO, msg="hello") -> logging.LogRecord:
    return logging.LogRecord(name=name, level=level, pathname=__file__, lineno=1,
                              msg=msg, args=(), exc_info=None)


class TestLogContext:

    def test_empty_by_default(self):
        assert get_log_context() == {}

    def test_bind_merges_fields(self):
        with bind_log_context(module_id="hello_world"):
            assert get_log_context() == {"module_id": "hello_world"}

    def test_bind_restores_previous_on_exit(self):
        with bind_log_context(module_id="hello_world"):
            with bind_log_context(execution_id="abc123"):
                assert get_log_context() == {"module_id": "hello_world", "execution_id": "abc123"}
            assert get_log_context() == {"module_id": "hello_world"}
        assert get_log_context() == {}

    def test_bind_restores_on_exception(self):
        with pytest.raises(ValueError):
            with bind_log_context(module_id="hello_world"):
                raise ValueError("boom")
        assert get_log_context() == {}


class TestJsonLogFormatter:

    def test_produces_valid_json(self):
        record = make_record(msg="Sizing calculation failed")
        line = JsonLogFormatter().format(record)
        json.loads(line)  # não levanta

    def test_required_fields(self):
        record = make_record(name="techforge.module_runtime", level=logging.ERROR, msg="failed")
        data = json.loads(JsonLogFormatter().format(record))
        assert data["level"] == "ERROR"
        assert data["component"] == "techforge.module_runtime"
        assert data["message"] == "failed"
        assert "timestamp" in data

    def test_includes_context_fields_when_present(self):
        record = make_record()
        record.log_context = {"module_id": "veeam_m365", "execution_id": "abc123"}
        data = json.loads(JsonLogFormatter().format(record))
        assert data["module_id"] == "veeam_m365"
        assert data["execution_id"] == "abc123"

    def test_omits_absent_context_fields(self):
        record = make_record()
        record.log_context = {}
        data = json.loads(JsonLogFormatter().format(record))
        assert "module_id" not in data
        assert "execution_id" not in data


class TestLogContextFilter:

    def test_attaches_current_context_to_record(self):
        record = make_record()
        with bind_log_context(module_id="hello_world"):
            LogContextFilter().filter(record)
        assert record.log_context == {"module_id": "hello_world"}


class TestConfigureLogging:

    def test_writes_jsonlines_file(self, tmp_path):
        logs_dir = tmp_path / "logs"
        configure_logging(level="INFO", logs_path=logs_dir)

        logger = logging.getLogger("techforge.test_configure")
        with bind_log_context(module_id="hello_world"):
            logger.info("test message")

        jsonl_path = logs_dir / "backend.jsonl"
        assert jsonl_path.exists()
        lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
        last = json.loads(lines[-1])
        assert last["message"] == "test message"
        assert last["module_id"] == "hello_world"

        # cleanup handlers pra não vazar pros outros testes do processo
        logging.getLogger().handlers.clear()

    def test_console_handler_uses_human_format(self, tmp_path):
        configure_logging(level="INFO", logs_path=tmp_path / "logs")
        root = logging.getLogger()
        console_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)
                            and not isinstance(h, logging.FileHandler)]
        assert len(console_handlers) == 1
        assert not isinstance(console_handlers[0].formatter, JsonLogFormatter)
        root.handlers.clear()

    def test_console_and_file_levels_can_diverge(self, tmp_path):
        configure_logging(level="WARNING", logs_path=tmp_path / "logs", file_level="DEBUG")
        root = logging.getLogger()
        console = next(h for h in root.handlers
                       if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler))
        file_handler = next(h for h in root.handlers if isinstance(h, logging.FileHandler))
        assert console.level == logging.WARNING
        assert file_handler.level == logging.DEBUG
        # root precisa aceitar DEBUG pra o file handler poder filtrar por conta própria
        assert root.level == logging.DEBUG
        root.handlers.clear()

    def test_file_level_defaults_to_console_level(self, tmp_path):
        configure_logging(level="ERROR", logs_path=tmp_path / "logs")
        root = logging.getLogger()
        file_handler = next(h for h in root.handlers if isinstance(h, logging.FileHandler))
        assert file_handler.level == logging.ERROR
        root.handlers.clear()

    def test_file_handler_rotates_by_size(self, tmp_path):
        from logging.handlers import RotatingFileHandler
        configure_logging(level="INFO", logs_path=tmp_path / "logs",
                          max_bytes=1000, backup_count=3)
        root = logging.getLogger()
        file_handler = next(h for h in root.handlers if isinstance(h, logging.FileHandler))
        assert isinstance(file_handler, RotatingFileHandler)
        assert file_handler.maxBytes == 1000
        assert file_handler.backupCount == 3
        root.handlers.clear()


class TestLogRetention:

    def _write_line(self, path: Path, level: str, days_ago: int) -> None:
        ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
        line = json.dumps({"timestamp": ts, "level": level, "component": "x", "message": "m"})
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def test_removes_lines_older_than_retention_for_their_level(self, tmp_path):
        jsonl = tmp_path / "backend.jsonl"
        self._write_line(jsonl, "DEBUG", days_ago=10)   # DEBUG retention 7d -> removida
        self._write_line(jsonl, "DEBUG", days_ago=1)     # dentro da retenção -> mantida
        self._write_line(jsonl, "ERROR", days_ago=10)    # ERROR retention 90d -> mantida

        removed = cleanup_old_logs(jsonl, retention_days={"DEBUG": 7, "ERROR": 90})

        assert removed == 1
        remaining = [json.loads(l) for l in jsonl.read_text(encoding="utf-8").strip().splitlines()]
        assert len(remaining) == 2
        assert sum(1 for r in remaining if r["level"] == "DEBUG") == 1
        assert sum(1 for r in remaining if r["level"] == "ERROR") == 1

    def test_noop_when_file_does_not_exist(self, tmp_path):
        removed = cleanup_old_logs(tmp_path / "nope.jsonl", retention_days={"DEBUG": 7})
        assert removed == 0

    def test_keeps_lines_without_matching_retention_rule(self, tmp_path):
        jsonl = tmp_path / "backend.jsonl"
        self._write_line(jsonl, "CRITICAL", days_ago=365)
        removed = cleanup_old_logs(jsonl, retention_days={"DEBUG": 7})
        assert removed == 0

    def test_keeps_malformed_lines(self, tmp_path):
        jsonl = tmp_path / "backend.jsonl"
        jsonl.write_text("not json at all\n", encoding="utf-8")
        removed = cleanup_old_logs(jsonl, retention_days={"DEBUG": 7})
        assert removed == 0
        assert jsonl.read_text(encoding="utf-8") == "not json at all\n"
