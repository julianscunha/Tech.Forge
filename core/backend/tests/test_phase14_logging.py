"""
TechForge Fase 14 Slice 1 — Logger central + Log Context
==========================================================
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.observability.context import bind_log_context, get_log_context
from app.observability.logging_setup import JsonLogFormatter, LogContextFilter, configure_logging

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
