"""Deixa o Neo4j com o catálogo versionado no Git. Roda sozinho a cada `docker compose up`.

Fonte: data/catalog/hardware_manual_v1.csv (peças) e data/catalog/games_manual_v1.json (jogos já
processados a partir das coletas da Steam). As coletas brutas não são necessárias.

1. Se o banco já tem exatamente esse catálogo (mesmos jogos, mesmos hashes e mesmas notas de
   hardware), não grava nada.
2. Senão, carrega o hardware e os jogos com os carregadores de sempre (MERGE, idempotente).
3. Em seguida, remove jogos que saíram da seleção, exceto os que têm interação de alguma conta.

Contas, sessões e interações nunca são apagadas.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile

from neo4j import GraphDatabase
from neo4j.exceptions import DriverError, Neo4jError

from game_catalog import OWNER, ROOT
from hardware_catalog import process_catalog
from load_games import main as load_games_main
from load_hardware import main as load_hardware_main

CATALOG = ROOT / "data/catalog/hardware_manual_v1.csv"
GAMES = ROOT / "data/catalog/games_manual_v1.json"
HASHES = ("catalog_sha256", "aliases_sha256", "selection_sha256", "curation_sha256", "hardware_sha256")


def database_state(session, data: dict) -> dict:
    """Compara o que está no banco com o arquivo. Só lê."""
    stored = session.run(
        "MATCH (g:Game) WHERE g.catalog_format IS NOT NULL"
        " RETURN g.id AS id, [k IN $hashes | g[k]] AS hashes", hashes=list(HASHES)).data()
    expected_hashes = [data.get(key) for key in HASHES]
    expected_ids = {game["id"] for game in data["games"]}
    games_ok = ({row["id"] for row in stored} >= expected_ids
                and all(row["hashes"] == expected_hashes for row in stored if row["id"] in expected_ids))
    parts = session.run(
        "MATCH (h) WHERE (h:CPU OR h:GPU) AND h.score_version = $version"
        " RETURN labels(h)[0] AS kind, h.name AS name, h.performance_score AS score",
        version=data["score_version"]).data()
    found = {(row["kind"], row["name"]): row["score"] for row in parts}
    hardware_ok = all(found.get((row["component_type"], row["name"]), "ausente") == row["performance_score"]
                      for row in data["hardware"])
    stale = session.run("MATCH (g:Game) WHERE NOT g.id IN $ids RETURN count(g) AS n", ids=list(expected_ids)).single()["n"]
    return {"games_ok": games_ok, "hardware_ok": hardware_ok, "stale_games": stale}


def prune_stale_games(session, ids: list[str]) -> dict:
    """Jogos fora da seleção saem do grafo; os que têm interação ficam, para não apagar histórico."""
    removed = session.run(
        "MATCH (g:Game) WHERE NOT g.id IN $ids AND NOT (g)<-[:INTERACTED]-()"
        " DETACH DELETE g RETURN count(g) AS n", ids=ids).single()["n"]
    kept = session.run("MATCH (g:Game) WHERE NOT g.id IN $ids RETURN count(g) AS n", ids=ids).single()["n"]
    return {"removed_stale_games": removed, "kept_stale_games_with_interactions": kept}


def main(argv: list[str] | None = None) -> int:
    try:
        data = json.loads(GAMES.read_text(encoding="utf-8-sig"))
        password = os.getenv("NEO4J_PASSWORD", "")
        if not password:
            raise ValueError("Defina NEO4J_PASSWORD no ambiente.")
        ids = [game["id"] for game in data["games"]]
        with GraphDatabase.driver(os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                                  auth=(os.getenv("NEO4J_USER", "neo4j"), password), connection_timeout=10,
                                  # Num banco vazio o Neo4j avisa de rótulos que ainda não existem; não é erro.
                                  notifications_min_severity="OFF") as driver:
            driver.verify_connectivity()
            database = os.getenv("NEO4J_DATABASE", "neo4j")
            with driver.session(database=database) as session:
                state = database_state(session, data)
            report = {"status": "ok", "games": len(ids), "owner": OWNER, **state}
            if state["games_ok"] and state["hardware_ok"]:
                report["action"] = "catálogo já estava em dia"
            else:
                with tempfile.TemporaryDirectory() as tmp:
                    processed = Path(tmp) / "hardware_manual_v1.csv"
                    process_catalog(CATALOG, processed, catalog_format="manual")
                    if load_hardware_main(["--format", "manual", "--input", str(processed)]) != 0:
                        raise RuntimeError("A carga do hardware falhou (veja a mensagem acima).")
                if load_games_main(["--input", str(GAMES)]) != 0:
                    raise RuntimeError("A carga dos jogos falhou (veja a mensagem acima).")
                report["action"] = "catálogo carregado"
            if state["stale_games"]:
                with driver.session(database=database) as session:
                    report.update(prune_stale_games(session, ids))
        print(json.dumps(report, ensure_ascii=False), flush=True)
        return 0
    except (OSError, ValueError, RuntimeError, DriverError, Neo4jError) as exc:
        print(f"Erro ao preparar o catálogo no Neo4j ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
