"""Contas, sessões e perfil de jogo no Neo4j.

(:User)-[:HAS_SESSION]->(:Session) e (:User)-[:INTERACTED]->(:Game), uma única
relação por par com a reação (liked/disliked), o número de visualizações e as
datas. A recarga do catálogo só troca as arestas de gênero e tag, então as
interações sobrevivem. O perfil fica como propriedades do próprio
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
    """Formato da conta enviado ao navegador: sem hash da senha e sem e-mail (veja /me/account)."""
    hardware = None
    if row.get("hw_cpu") and row.get("hw_gpu") and row.get("hw_ram_gb") and row.get("hw_os"):
        hardware = {"cpuId": row["hw_cpu"], "gpuId": row["hw_gpu"], "ramGb": int(row["hw_ram_gb"]), "os": row["hw_os"]}
        if row.get("hw_windows_version"):
            hardware["windowsVersion"] = row["hw_windows_version"]
    return {"id": row["id"], "name": row["name"],
            "genres": list(row.get("genres") or []), "themes": list(row.get("themes") or []),
            "anchorIds": list(row.get("anchor_ids") or []), "hardware": hardware}


def interaction_from(row: dict) -> dict:
    """Formato público de uma interação: só o jogo, a reação, as visualizações e as datas."""
    rel = row["rel"]
    return {"gameId": row["game_id"], "title": row.get("title"), "reaction": rel.get("reaction"),
            "views": int(rel.get("views") or 0), "reactedAt": rel.get("reacted_at"),
            "firstViewedAt": rel.get("first_viewed_at"), "lastViewedAt": rel.get("last_viewed_at")}


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

    # Interações com jogos. O jogo precisa existir no grafo; o catálogo não é alterado.

    def record_view(self, *, user_id: str, game_id: str, now: int) -> dict | None:
        return self._interaction(
            "MATCH (u:User {id: $uid}), (g:Game {id: $gid}) MERGE (u)-[r:INTERACTED]->(g)"
            " ON CREATE SET r.views = 1, r.first_viewed_at = $now"
            " ON MATCH SET r.views = coalesce(r.views, 0) + 1"
            " SET r.last_viewed_at = $now RETURN g.id AS game_id, g.title AS title, r {.*} AS rel",
            uid=user_id, gid=game_id, now=now)

    def set_reaction(self, *, user_id: str, game_id: str, reaction: str | None, now: int) -> dict | None:
        return self._interaction(
            "MATCH (u:User {id: $uid}), (g:Game {id: $gid}) MERGE (u)-[r:INTERACTED]->(g)"
            " ON CREATE SET r.views = 0 SET r.reaction = $reaction, r.reacted_at = CASE WHEN $reaction IS NULL THEN NULL ELSE $now END"
            " RETURN g.id AS game_id, g.title AS title, r {.*} AS rel",
            uid=user_id, gid=game_id, reaction=reaction, now=now)

    def _interaction(self, query: str, **params) -> dict | None:
        rows = self._run(query, **params)
        if not rows:
            return None
        found = interaction_from(rows[0])
        if not found["reaction"] and not found["views"]:
            # Reação removida de um jogo nunca visto: não deixa uma relação vazia no grafo.
            self._run("MATCH (:User {id: $uid})-[r:INTERACTED]->(:Game {id: $gid}) DELETE r",
                      uid=params["uid"], gid=params["gid"])
        return found

    def list_interactions(self, user_id: str) -> list[dict]:
        rows = self._run(
            "MATCH (:User {id: $uid})-[r:INTERACTED]->(g:Game) RETURN g.id AS game_id, g.title AS title, r {.*} AS rel"
            " ORDER BY coalesce(r.reacted_at, r.last_viewed_at, 0) DESC, g.id", uid=user_id)
        return [interaction_from(row) for row in rows]

    def clear_interactions(self, user_id: str) -> int:
        rows = self._run("MATCH (:User {id: $uid})-[r:INTERACTED]->(:Game) DELETE r RETURN count(r) AS removed", uid=user_id)
        return int(rows[0]["removed"]) if rows else 0
