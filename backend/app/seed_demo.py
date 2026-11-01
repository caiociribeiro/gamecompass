"""Cria (ou atualiza) uma conta de demonstração a partir do .env.

Uso: docker compose run --rm --no-deps api python -m app.seed_demo
A senha vem de DEMO_PASSWORD e nunca é impressa nem guardada no código.
"""

import os
import sys
import time

from neo4j import GraphDatabase
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.auth import RegisterInput
from app.services.auth import hash_password
from app.services.users import EmailTaken, UserStore


def seed(store, *, name: str, email: str, password: str) -> str:
    """Retorna 'criada' ou 'atualizada'. Repetir o comando é seguro."""
    data = RegisterInput(name=name, email=email, password=password)
    now = int(time.time())
    password_hash = hash_password(data.password)
    try:
        store.create_user(name=data.name, email=data.email, password_hash=password_hash, now=now)
        return "criada"
    except EmailTaken:
        user = store.find_by_email(data.email)
        # Redefine a senha e encerra sessões antigas; o perfil de jogo é preservado.
        store.set_password(user_id=user["id"], password_hash=password_hash, keep_token_hash="", now=now)
        return "atualizada"


def main() -> int:
    email, password = os.getenv("DEMO_EMAIL", ""), os.getenv("DEMO_PASSWORD", "")
    if not email or not password:
        print("Defina DEMO_EMAIL e DEMO_PASSWORD no .env (senha com 8 a 128 caracteres).", file=sys.stderr)
        return 2
    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        result = seed(UserStore(driver, settings.neo4j_database), name=os.getenv("DEMO_NAME", "Demo"),
                      email=email, password=password)
    except ValidationError:
        print("DEMO_EMAIL, DEMO_NAME ou DEMO_PASSWORD inválidos (senha com 8 a 128 caracteres).", file=sys.stderr)
        return 2
    finally:
        driver.close()
    print(f"Conta de demonstração {result}: {email.strip().lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
