"""Sonda de diagnóstico temporária — CI (`CLI test suite`) trava depois do
pytest imprimir "N passed" (processo não retorna até o timeout). Não
reproduz no Windows local. Lista threads não-daemon vivas no fim da sessão
pra achar o que está segurando o processo aberto no runner Linux — ver
docs/limitations.md. Remover depois de identificar a causa."""
import threading


def pytest_sessionfinish(session, exitstatus):
    alive = [t for t in threading.enumerate() if t is not threading.main_thread()]
    print("\n[DIAG] non-main threads at session finish:", file=__import__("sys").stderr)
    for t in alive:
        print(f"[DIAG]   name={t.name!r} daemon={t.daemon} alive={t.is_alive()} ident={t.ident}",
              file=__import__("sys").stderr)
    if not alive:
        print("[DIAG]   (none)", file=__import__("sys").stderr)
