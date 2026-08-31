"""Entry point do backend empacotado (Fase 16 §10).

PyInstaller precisa de um script concreto pra congelar, não de uma
invocação de CLI (`python -m uvicorn app.main:app`) — este módulo é
esse ponto de entrada. Uso normal (dev, `techforge start`) continua via
uvicorn CLI; isto só é exercitado pelo executável gerado por
`scripts/build-backend.ps1`.
"""
from __future__ import annotations

import uvicorn

from app.core.settings import settings
from app.main import app


def main() -> None:
    # Passa o objeto `app` diretamente, não a string "app.main:app" — dentro
    # do executável congelado (PyInstaller) o import-by-string do uvicorn
    # falha ("Could not import module app.main") mesmo com o módulo
    # empacotado; import direto contorna a resolução de import do uvicorn.
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, reload=False)


if __name__ == "__main__":
    main()
