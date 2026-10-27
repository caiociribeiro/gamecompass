"""Carrega um catálogo validado nos nós CPU e GPU do Neo4j.

Simulação: python scripts/load_hardware.py --input CAMINHO --dry-run
Carga:     python scripts/load_hardware.py --input CAMINHO

Use --format manual para gravar performance_score e score_version.
No lote manual, notas vazias removem notas anteriores e ficam pendentes.
Somente os modelos presentes no CSV são migrados.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import sys

from neo4j import GraphDatabase, ManagedTransaction
from neo4j.exceptions import DriverError, Neo4jError

from hardware_catalog import MANUAL_SCORE_VERSION, ROOT, read_catalog


NEO4J_MAX_INTEGER = 2**63 - 1
CONSTRAINT_QUERIES = (
    "CREATE CONSTRAINT gamecompass_cpu_name IF NOT EXISTS "
    "FOR (c:CPU) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT gamecompass_gpu_name IF NOT EXISTS "
    "FOR (g:GPU) REQUIRE g.name IS UNIQUE",
)
LOAD_QUERIES = {
    "CPU": """
        UNWIND $rows AS row
        MERGE (c:CPU {name: row.name})
        SET c.passmark_score = row.passmark_score
    """,
    "GPU": """
        UNWIND $rows AS row
        MERGE (g:GPU {name: row.name})
        SET g.passmark_score = row.passmark_score
    """,
}
MANUAL_LOAD_QUERIES = {
    "CPU": """
        UNWIND $rows AS row
        MERGE (c:CPU {name: row.name})
        SET c.performance_score = row.performance_score,
            c.score_version = row.score_version
        REMOVE c.passmark_score
    """,
    "GPU": """
        UNWIND $rows AS row
        MERGE (g:GPU {name: row.name})
        SET g.performance_score = row.performance_score,
            g.score_version = row.score_version
        REMOVE g.passmark_score
    """,
}
LEGACY_GUARD_QUERIES = {
    "CPU": """
        UNWIND $rows AS row
        MATCH (c:CPU {name: row.name})
        WHERE c.score_version IS NOT NULL OR c.performance_score IS NOT NULL
        RETURN c.name AS name LIMIT 1
    """,
    "GPU": """
        UNWIND $rows AS row
        MATCH (g:GPU {name: row.name})
        WHERE g.score_version IS NOT NULL OR g.performance_score IS NOT NULL
        RETURN g.name AS name LIMIT 1
    """,
}


class CatalogMigrationError(ValueError):
    """Impede que uma carga antiga reintroduza pontuações após a migração."""


def prepare_payload(
    input_path: Path, *, catalog_format: str = "passmark",
) -> dict[str, list[dict[str, str | int | None]]]:
    """Valida todo o CSV e separa apenas as propriedades do contrato do grafo."""
    records = read_catalog(input_path, catalog_format=catalog_format)
    payload: dict[str, list[dict[str, str | int | None]]] = {"CPU": [], "GPU": []}
    score_key = "performance_score" if catalog_format == "manual" else "passmark_score"
    for record in records:
        score = record[score_key]
        if score is not None and score > NEO4J_MAX_INTEGER:
            raise ValueError(f"Pontuação fora do limite inteiro do Neo4j: {record['name']}.")
        row = {"name": record["name"], score_key: score}
        if catalog_format == "manual":
            row["score_version"] = record["score_version"]
        payload[record["component_type"]].append(row)
    return payload


def create_constraints(tx: ManagedTransaction) -> None:
    """Executa operações de schema separadamente da transação dos dados."""
    for query in CONSTRAINT_QUERIES:
        tx.run(query).consume()


def write_hardware(
    tx: ManagedTransaction, payload: dict[str, list[dict[str, str | int | None]]],
    *, catalog_format: str = "passmark",
) -> int:
    """CPUs e GPUs pertencem ao mesmo lote: falhar propaga o rollback."""
    if catalog_format not in ("passmark", "manual"):
        raise ValueError("catalog_format deve ser passmark ou manual.")
    queries = MANUAL_LOAD_QUERIES if catalog_format == "manual" else LOAD_QUERIES
    nodes_created = 0
    for component_type in ("CPU", "GPU"):
        rows = payload[component_type]
        if rows:
            if catalog_format == "passmark":
                migrated = tx.run(LEGACY_GUARD_QUERIES[component_type], rows=rows).single()
                if migrated is not None:
                    raise CatalogMigrationError(
                        "A carga PassMark não pode sobrescrever um modelo já migrado "
                        "para o índice manual."
                    )
            summary = tx.run(queries[component_type], rows=rows).consume()
            nodes_created += summary.counters.nodes_created
    return nodes_created


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format", dest="catalog_format", choices=("passmark", "manual"),
        default="passmark", help="Formato do catálogo; manual usa o novo índice.",
    )
    parser.add_argument(
        "--input", type=Path,
        help="CSV completo, no contrato de hardware_catalog.py.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Valida e conta os registros sem conectar ao Neo4j.",
    )
    args = parser.parse_args(argv)

    # A validação completa ocorre antes da conexão, inclusive na carga real.
    try:
        filename = (
            "hardware_manual_v1.csv" if args.catalog_format == "manual"
            else "hardware_benchmarks.csv"
        )
        input_path = args.input if args.input is not None else ROOT / "data/processed" / filename
        payload = prepare_payload(input_path, catalog_format=args.catalog_format)
    except (OSError, ValueError, UnicodeError, csv.Error) as exc:
        print(f"Erro no catálogo: {exc}", file=sys.stderr)
        return 1

    report = {
        "status": "ok", "dry_run": args.dry_run,
        "CPU": len(payload["CPU"]), "GPU": len(payload["GPU"]),
        "input": str(input_path),
    }
    if args.catalog_format == "manual":
        rows = payload["CPU"] + payload["GPU"]
        report.update(
            format="manual", score_version=MANUAL_SCORE_VERSION,
            classified=sum(row["performance_score"] is not None for row in rows),
            pending=sum(row["performance_score"] is None for row in rows),
        )
    if args.dry_run:
        print(json.dumps(report, ensure_ascii=False))
        return 0

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    if not password:
        print("Defina NEO4J_PASSWORD no ambiente.", file=sys.stderr)
        return 1

    try:
        with GraphDatabase.driver(
            uri, auth=(user, password), connection_timeout=10,
            connection_acquisition_timeout=15, max_transaction_retry_time=10,
        ) as driver:
            driver.verify_connectivity()
            with driver.session(database=database) as session:
                session.execute_write(create_constraints)
                nodes_created = session.execute_write(
                    write_hardware, payload, catalog_format=args.catalog_format,
                )
    except CatalogMigrationError as exc:
        print(f"Falha na migração: {exc}", file=sys.stderr)
        return 1
    except (DriverError, Neo4jError, OSError, ValueError) as exc:
        print(
            f"Falha na carga ({type(exc).__name__}). Confira o serviço neo4j, "
            "as credenciais, o banco e possíveis conflitos nas constraints.",
            file=sys.stderr,
        )
        return 1

    report.update(database=database, nodes_created=nodes_created)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
