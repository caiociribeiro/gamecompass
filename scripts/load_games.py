"""Carrega Game, Genre e Tag; preserva os demais nós e relações do banco."""

import argparse
import csv
import json
import os
from pathlib import Path
import sys

from neo4j import GraphDatabase
from neo4j.exceptions import DriverError, Neo4jError

from game_catalog import FORMAT, FIELDS, OWNER, ROOT, hardware_rows, sha256, validate_catalog

CONSTRAINTS = (
    "CREATE CONSTRAINT gamecompass_game_id IF NOT EXISTS FOR (g:Game) REQUIRE g.id IS UNIQUE",
    "CREATE CONSTRAINT gamecompass_genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
    "CREATE CONSTRAINT gamecompass_tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",
)
HARDWARE_QUERIES = {
    kind: f"""UNWIND $rows AS row
        OPTIONAL MATCH (h:{kind} {{name: row.name}})
        RETURN row.name AS expected, h.name AS name, h.performance_score AS performance_score,
               h.score_version AS score_version"""
    for kind in ("CPU", "GPU")
}
WRITE_QUERY = """
UNWIND $rows AS row
MERGE (g:Game {id: row.id})
SET g += row.properties
WITH g, row
OPTIONAL MATCH (g)-[old:HAS_GENRE|HAS_TAG]->()
WHERE old.source = $owner
WITH g, row, collect(old) AS previous
FOREACH (edge IN previous | DELETE edge)
FOREACH (name IN row.genres |
    MERGE (genre:Genre {name: name})
    MERGE (g)-[:HAS_GENRE {source: $owner}]->(genre)
)
FOREACH (name IN row.tags |
    MERGE (tag:Tag {name: name})
    MERGE (g)-[:HAS_TAG {source: $owner}]->(tag)
)
"""


def prepare_payload(data: dict) -> list[dict]:
    validate_catalog(data)
    rows = []
    for game in data["games"]:
        properties = {key: game[key] for key in ("title", "price", *FIELDS)}
        properties.update(catalog_format=FORMAT, score_version=data["score_version"],
            hardware_sha256=data["hardware_sha256"], catalog_sha256=data["catalog_sha256"],
            aliases_sha256=data["aliases_sha256"], selection_sha256=data["selection_sha256"],
            source_url=game["source"]["source_url"], collected_at=game["source"]["collected_at"],
            catalog_json=json.dumps(game, ensure_ascii=False, allow_nan=False))
        rows.append({"id": game["id"], "properties": properties, "genres": game["genres"], "tags": game["themes"]})
    return rows


def create_constraints(tx):
    for query in CONSTRAINTS:
        tx.run(query).consume()


def write_games(tx, data: dict, rows: list[dict]) -> dict:
    # A carga não utiliza uma pontuação CSV divergente do catálogo da aplicação.
    for kind in ("CPU", "GPU"):
        expected = {row["name"]: row for row in data["hardware"] if row["component_type"] == kind}
        found = tx.run(HARDWARE_QUERIES[kind], rows=list(expected.values())).data()
        if len(found) != len(expected) or any(
            row["name"] != row["expected"]
            or row["score_version"] != expected[row["expected"]]["score_version"]
            or row["performance_score"] != expected[row["expected"]]["performance_score"]
            for row in found
        ):
            raise ValueError("Carregue no Neo4j o mesmo catálogo manual usado no processamento dos jogos.")
    summary = tx.run(WRITE_QUERY, rows=rows, owner=OWNER).consume()
    return {"nodes_created": summary.counters.nodes_created, "relationships_created": summary.counters.relationships_created}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/processed/games_manual_v1.json")
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/catalog/hardware_manual_v1.csv")
    parser.add_argument("--aliases", type=Path, default=ROOT / "data/catalog/hardware_aliases.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        rows = prepare_payload(data)
        if data["catalog_sha256"] != sha256(args.catalog) or data["aliases_sha256"] != sha256(args.aliases):
            raise ValueError("Catálogo ou aliases mudaram. Reprocesse os jogos antes da carga.")
        if data["hardware"] != hardware_rows(args.catalog):
            raise ValueError("Referência de hardware divergente do CSV.")
        report = {"status": "ok", "dry_run": args.dry_run, "games": len(rows),
            "genres": len({name for row in rows for name in row["genres"]}),
            "tags": len({name for row in rows for name in row["tags"]}),
            "needs_review": sum(game["status"] == "needs_review" for game in data["games"])}
        if args.dry_run:
            print(json.dumps(report, ensure_ascii=False))
            return 0
        password = os.getenv("NEO4J_PASSWORD", "")
        if not password:
            raise ValueError("Defina NEO4J_PASSWORD no ambiente.")
        with GraphDatabase.driver(os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), password), connection_timeout=10,
            connection_acquisition_timeout=15, max_transaction_retry_time=10) as driver:
            driver.verify_connectivity()
            database = os.getenv("NEO4J_DATABASE", "neo4j")
            with driver.session(database=database) as session:
                session.execute_write(create_constraints)
                counts = session.execute_write(write_games, data, rows)
        report.update(database=database, **counts)
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (OSError, ValueError, UnicodeError, csv.Error, DriverError, Neo4jError) as exc:
        print(f"Erro na carga de jogos ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
