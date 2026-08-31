# Módulo hello_world

**Categoria:** Examples
**Vendor:** TechForge
**Versão:** 1.0.0
**Status:** Referência / Validação de arquitetura

---

## Objetivo

Este módulo existe só pra validar a arquitetura de plugins da Fase 2.
Ele **não** é uma ferramenta funcional.

Demonstra:
- Um `manifest.yaml` válido com todos os campos obrigatórios.
- A estrutura de diretórios obrigatória (`backend/`, `frontend/`, `assets/`, `docs/`, `tests/`).
- O contrato do ponto de entrada do backend (`router`, lifecycle hooks).
- O contrato do ponto de entrada do frontend (export default, lifecycle hooks).
- Registro automático no ModuleRegistry na inicialização.
- Aparição na página de Módulos com status `INSTALLED`.

## O que ele NÃO faz

- Nenhuma lógica de negócio real.
- Nenhuma interação com banco de dados.
- Nenhuma chamada a API externa.
- Nenhuma renderização de UI (o componente de frontend é um stub).

## Ciclo de vida

| Evento       | Comportamento         |
|-------------|------------------|
| `install()` | No-op            |
| `enable()`  | No-op            |
| `disable()` | No-op            |
| `upgrade()` | No-op            |
| `health_check()` | Retorna `{status: "ok"}` |
| `uninstall()` | No-op          |

## Como usar como template

Copie este diretório inteiro pra `modules/installed/<id_do_seu_modulo>/`,
atualize o `manifest.yaml` e implemente os pontos de entrada de backend e frontend.
