"""Hash de senha, tokens de sessão e limite de tentativas."""

import hashlib
import secrets
import threading
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
    """Limite simples por processo. Reinicia com a API; suficiente para o protótipo.

    Com N processos (API_WORKERS), cada um conta as falhas sozinho: o bloqueio pode demorar
    até N vezes mais tentativas para valer em todos.
    """

    def __init__(self, limit: int = 5, window_seconds: int = 300):
        self.limit, self.window = limit, window_seconds
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str, now: float) -> list[float]:
        recent = [moment for moment in self._failures.get(key, []) if now - moment < self.window]
        if recent:
            self._failures[key] = recent
        else:
            self._failures.pop(key, None)
        return recent

    def blocked(self, key: str) -> bool:
        with self._lock:
            return len(self._recent(key, time.monotonic())) >= self.limit

    def fail(self, key: str) -> None:
        with self._lock:
            now = time.monotonic()
            self._recent(key, now)
            self._failures.setdefault(key, []).append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)
