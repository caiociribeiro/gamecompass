"""Contas, sessões e perfil de jogo no Neo4j.

(:User)-[:HAS_SESSION]->(:Session). O perfil fica como propriedades do próprio
User; os jogos âncora são ids Steam, sem relacionamento com :Game, para que a
recarga do catálogo não afete contas.
"""

import threading
import uuid

from neo4j.exceptions import ConstraintError

SCHEMA = (
    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
    "CREATE CONSTRAINT user_email IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE",
    "CREATE CONSTRAINT session_token IF NOT EXISTS FOR (s:Session) REQUIRE s.token_hash IS UNIQUE",
)


class EmailTaken(Exception):
    pass


def account_from(row: dict) -> dict:
    """Formato público da conta; nunca inclui o hash da senha."""
    hardware = None
    if row.get("hw_cpu") and row.get("hw_gpu") and row.get("hw_ram_gb") and row.get("hw_os"):
        hardware = {"cpuId": row["hw_cpu"], "gpuId": row["hw_gpu"], "ramGb": int(row["hw_ram_gb"]), "os": row["hw_os"]}
        if row.get("hw_windows_version"):
            hardware["windowsVersion"] = row["hw_windows_version"]
    return {"id": row["id"], "name": row["name"], "email": row["email"],
            "genres": list(row.get("genres") or []), "themes": list(row.get("themes") or []),
            "anchorIds": list(row.get("anchor_ids") or []), "hardware": hardware}


def profile_properties(changes: dict) -> dict:
    """Converte campos do perfil em propriedades; None remove a propriedade no Neo4j."""
    props: dict = {}
    if "name" in changes:
        props["name"] = changes["name"]
    for field, prop in (("genres", "genres"), ("themes", "themes"), ("anchorIds", "anchor_ids")):
        if field in changes:
            props[prop] = list(changes[field])
    if "hardware" in changes:
        hardware = changes["hardware"] or {}
        props.update(hw_cpu=hardware.get("cpuId"), hw_gpu=hardware.get("gpuId"), hw_ram_gb=hardware.get("ramGb"),
                     hw_os=hardware.get("os"), hw_windows_version=hardware.get("windowsVersion"))
    return props


class UserStore:
    def __init__(self, driver, database: str):
        self.driver, self.database = driver, database
        self._schema_ready = False
        self._lock = threading.Lock()

    def _run(self, query: str, **params) -> list[dict]:
        with self.driver.session(database=self.database) as session:
            return session.run(query, **params).data()

    def ensure_schema(self) -> None:
        if self._schema_ready:
            return
        with self._lock:
            if self._schema_ready:
                return
            for statement in SCHEMA:
                self._run(statement)
            self._schema_ready = True

    def create_user(self, *, name: str, email: str, password_hash: str, now: int) -> dict:
        self.ensure_schema()
        try:
            rows = self._run(
                "CREATE (u:User {id: $id, name: $name, email: $email, password_hash: $hash, created_at: $now,"
                " genres: [], themes: [], anchor_ids: []}) RETURN u {.*} AS user",
                id=str(uuid.uuid4()), name=name, email=email, hash=password_hash, now=now)
        except ConstraintError as exc:
            raise EmailTaken(email) from exc
        return rows[0]["user"]

    def find_by_email(self, email: str) -> dict | None:
        rows = self._run("MATCH (u:User {email: $email}) RETURN u {.*} AS user", email=email)
        return rows[0]["user"] if rows else None

    def create_session(self, *, user_id: str, token_hash: str, now: int, expires_at: int) -> None:
        self.ensure_schema()
        self._run("MATCH (:User {id: $uid})-[:HAS_SESSION]->(old:Session) WHERE old.expires_at <= $now DETACH DELETE old",
                  uid=user_id, now=now)
        rows = self._run(
            "MATCH (u:User {id: $uid}) CREATE (u)-[:HAS_SESSION]->(s:Session {token_hash: $hash, created_at: $now,"
            " expires_at: $exp}) RETURN s.token_hash AS hash", uid=user_id, hash=token_hash, now=now, exp=expires_at)
        if not rows:
            raise LookupError("Usuário inexistente.")

    def user_for_session(self, token_hash: str, now: int) -> dict | None:
        rows = self._run(
            "MATCH (u:User)-[:HAS_SESSION]->(s:Session {token_hash: $hash}) WHERE s.expires_at > $now"
            " RETURN u {.*} AS user", hash=token_hash, now=now)
        return rows[0]["user"] if rows else None

    def delete_session(self, token_hash: str) -> None:
        self._run("MATCH (s:Session {token_hash: $hash}) DETACH DELETE s", hash=token_hash)

    def set_password(self, *, user_id: str, password_hash: str, keep_token_hash: str, now: int) -> None:
        """Troca o hash e encerra as demais sessões da conta."""
        self._run("MATCH (u:User {id: $uid}) SET u.password_hash = $hash, u.password_changed_at = $now",
                  uid=user_id, hash=password_hash, now=now)
        self._run("MATCH (:User {id: $uid})-[:HAS_SESSION]->(s:Session) WHERE s.token_hash <> $keep DETACH DELETE s",
                  uid=user_id, keep=keep_token_hash)

    def update_profile(self, *, user_id: str, changes: dict, now: int) -> dict | None:
        rows = self._run("MATCH (u:User {id: $uid}) SET u += $props, u.profile_updated_at = $now RETURN u {.*} AS user",
                         uid=user_id, props=profile_properties(changes), now=now)
        return rows[0]["user"] if rows else None
