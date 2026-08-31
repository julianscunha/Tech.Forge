"""Secret Store — Fase 12 §11/§28.

Abstração trocável (Desktop usa o cofre nativo do SO via `keyring`; Server
poderá plugar outro backend depois, sem mudar quem consome). Sem
criptografia própria — a spec exige isso explicitamente.

`ModuleSecretStore` é a fachada por-módulo, isolada por `module_id`
fixado na construção (mesmo desenho do Module Storage API, Slice 5):
nunca é parâmetro de `get`/`set`/`delete`, então um módulo não tem como
ler ou escrever segredo de outro módulo.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

_SERVICE_NAMESPACE = "techforge"

# Valores de segredo já gravados nesta execução — usado só para redação em
# log (Fase 12 §28). Não é o armazenamento em si (isso é o keyring/SO).
_known_secret_values: set[str] = set()


class SecretStoreError(Exception):
    """Erro ao acessar o cofre de segredos — nunca vaza detalhe do backend nativo."""


class SecretStoreBackend(ABC):
    """Backend de baixo nível — recebe module_id explicitamente. Só
    `ModuleSecretStore` (isolamento estrutural) deve ser usado por módulos."""

    @abstractmethod
    def get(self, module_id: str, key: str) -> Optional[str]: ...

    @abstractmethod
    def set(self, module_id: str, key: str, value: str) -> None: ...

    @abstractmethod
    def delete(self, module_id: str, key: str) -> None: ...


def _qualified_key(module_id: str, key: str) -> str:
    return f"{module_id}:{key}"


class KeyringSecretStore(SecretStoreBackend):
    """Implementação Desktop — Windows Credential Manager / macOS Keychain /
    Secret Service (Linux), via a lib `keyring`."""

    def get(self, module_id: str, key: str) -> Optional[str]:
        import keyring
        try:
            return keyring.get_password(_SERVICE_NAMESPACE, _qualified_key(module_id, key))
        except Exception as exc:
            raise SecretStoreError(f"Falha ao ler segredo: {exc}") from exc

    def set(self, module_id: str, key: str, value: str) -> None:
        import keyring
        try:
            keyring.set_password(_SERVICE_NAMESPACE, _qualified_key(module_id, key), value)
        except Exception as exc:
            raise SecretStoreError(f"Falha ao gravar segredo: {exc}") from exc
        _known_secret_values.add(value)

    def delete(self, module_id: str, key: str) -> None:
        import keyring
        import keyring.errors
        try:
            keyring.delete_password(_SERVICE_NAMESPACE, _qualified_key(module_id, key))
        except keyring.errors.PasswordDeleteError:
            pass  # idempotente — já não existia
        except Exception as exc:
            raise SecretStoreError(f"Falha ao remover segredo: {exc}") from exc


_default_backend: SecretStoreBackend = KeyringSecretStore()


class ModuleSecretStore:
    """`context.secrets` — fachada isolada por módulo (Fase 12 §11).

    Lifecycle explícito (Fase 17 §22-26): `set()` só audita criação
    (primeira vez que a key existe); `rotate()` é o jeito nomeado de
    trocar um valor existente — antes disso era só "chamar `set()` de
    novo", sem distinção semântica nem evento de auditoria. Nenhum
    evento carrega o valor do segredo, só `module_id`/`key`."""

    def __init__(self, module_id: str, backend: Optional[SecretStoreBackend] = None):
        self._module_id = module_id
        self._backend = backend or _default_backend

    def get(self, key: str) -> Optional[str]:
        return self._backend.get(self._module_id, key)

    def set(self, key: str, value: str) -> None:
        from app.observability.events import event_bus

        is_new = self._backend.get(self._module_id, key) is None
        self._backend.set(self._module_id, key, value)
        if is_new:
            event_bus.publish("security.secret_created", module_id=self._module_id, key=key)

    def rotate(self, key: str, new_value: str) -> None:
        """Troca o valor de um segredo já existente. Levanta `SecretStoreError`
        se a key nunca foi criada — rotacionar o que não existe é um erro
        de uso, não um "criar silencioso" (use `set()` pra criar)."""
        from app.observability.events import event_bus

        if self._backend.get(self._module_id, key) is None:
            raise SecretStoreError(f"Cannot rotate non-existent secret: {key!r}")
        self._backend.set(self._module_id, key, new_value)
        event_bus.publish("security.secret_rotated", module_id=self._module_id, key=key)

    def delete(self, key: str) -> None:
        from app.observability.events import event_bus

        existed = self._backend.get(self._module_id, key) is not None
        self._backend.delete(self._module_id, key)
        if existed:
            event_bus.publish("security.secret_deleted", module_id=self._module_id, key=key)
