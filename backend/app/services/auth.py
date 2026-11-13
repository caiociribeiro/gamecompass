"""Hash de senha, tokens de sessão e limite de tentativas."""

import hashlib
import secrets
import time

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()
# Hash descartável: login de e-mail inexistente gasta o mesmo tempo de um existente.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(24))


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(stored_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(stored_hash or _DUMMY_HASH, password) and stored_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    """O banco guarda só o SHA-256; o token original existe apenas no cookie."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AttemptLimiter:
    """Bloqueia uma chave (IP + e-mail, ou IP + conta) depois de `limit` falhas em `window_seconds`.

    As falhas ficam no repositório de contas (o Neo4j, na API real), e não na memória do processo:
    todos os processos da API (API_WORKERS) veem a mesma contagem e o bloqueio vale para todos.
    A chave é guardada como SHA-256, sem o e-mail nem o IP em texto.
    """

    def __init__(self, limit: int = 5, window_seconds: int = 300):
        self.limit, self.window = limit, window_seconds

    @staticmethod
    def _digest(key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def blocked(self, store, key: str) -> bool:
        now = time.time()
        return store.recent_failures(key=self._digest(key), since=now - self.window) >= self.limit

    def fail(self, store, key: str) -> None:
        now = time.time()
        store.add_failure(key=self._digest(key), now=now, since=now - self.window)

    def reset(self, store, key: str) -> None:
        store.clear_failures(key=self._digest(key))
