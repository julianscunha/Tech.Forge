"""TD-019 — printing Unicode glyphs must not crash on a cp1252 stream."""
import io

from techforge_cli.console import force_utf8_streams


def test_force_utf8_streams_lets_cp1252_stream_print_glyphs(monkeypatch):
    cp1252_stdout = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr("sys.stdout", cp1252_stdout)

    force_utf8_streams()
    print("❤ ✓ ✗ ⚠", file=cp1252_stdout)  # ❤ ✓ ✗ ⚠
    cp1252_stdout.flush()

    assert cp1252_stdout.encoding.lower() == "utf-8"
