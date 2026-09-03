"""Sonda de diagnóstico temporária — CI (`CLI test suite`) trava depois do
pytest imprimir "N passed" (processo não retorna até o timeout). Não
reproduz no Windows local. Lista threads não-daemon vivas no fim da sessão
pra achar o que está segurando o processo aberto no runner Linux — ver
docs/limitations.md. Remover depois de identificar a causa."""
import sys
import threading
import traceback


def pytest_sessionfinish(session, exitstatus):
    alive = [t for t in threading.enumerate() if t is not threading.main_thread()]
    frames = sys._current_frames()
    print("\n[DIAG] non-main threads at session finish:", file=sys.stderr)
    for t in alive:
        print(f"[DIAG]   name={t.name!r} daemon={t.daemon} alive={t.is_alive()} ident={t.ident}",
              file=sys.stderr)
        frame = frames.get(t.ident)
        if frame is not None:
            print("[DIAG]   stack:", file=sys.stderr)
            for line in traceback.format_stack(frame):
                print("[DIAG]    " + line.rstrip(), file=sys.stderr)
    if not alive:
        print("[DIAG]   (none)", file=sys.stderr)
