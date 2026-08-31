"""URL base do Core, compartilhada por todos os comandos CLI.

Fase 18 Slice 4 — antes duplicada como `_CORE`/`_BASE` em 11 arquivos de
`commands/`; consolidada aqui pra eliminar o hardcode repetido (CLAUDE.md:
"nunca hardcodar URLs/portas/caminhos").
"""
CORE_BASE_URL = "http://127.0.0.1:8000/api/v1"
