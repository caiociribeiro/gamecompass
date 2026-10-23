"""Carrega um catálogo validado nos nós CPU e GPU do Neo4j.

Simulação: python scripts/load_hardware.py --input CAMINHO --dry-run
Carga:     python scripts/load_hardware.py --input CAMINHO
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

from hardware_catalog import ROOT, read_catalog


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


def prepare_payload(input_path: Path) -> dict[str, list[dict[str, str | int]]]:
    """Valida todo o CSV e separa apenas as propriedades do contrato do grafo."""
    records = read_catalog(input_path)
    payload: dict[str, list[dict[str, str | int]]] = {"CPU": [], "GPU": []}
    for record in records:
        if record["passmark_score"] > NEO4J_MAX_INTEGER:
            raise ValueError(f"Pontuação fora do limite inteiro do Neo4j: {record['name']}.")
        payload[record["component_type"]].append({
            "name": record["name"], "passmark_score": record["passmark_score"],
        })
    return payload


def create_constraints(tx: ManagedTransaction) -> None:
    """Executa operações de schema separadamente da transação dos dados."""
    for query in CONSTRAINT_QUERIES:
        tx.run(query).consume()


def write_hardware(
    tx: ManagedTransaction, payload: dict[str, list[dict[str, str | int]]],
) -> int:
    """CPUs e GPUs pertencem ao mesmo lote: falhar propaga o rollback."""
    nodes_created = 0
    for component_type in ("CPU", "GPU"):
        rows = payload[component_type]
        if rows:
            summary = tx.run(LOAD_QUERIES[component_type], rows=rows).consume()
            nodes_created += summary.counters.nodes_created
    return nodes_created


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=ROOT / "data/processed/hardware_benchmarks.csv",
        help="CSV completo, no contrato de hardware_catalog.py.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Valida e conta os registros sem conectar ao Neo4j.",
    )
    args = parser.parse_args(argv)

    # A validação completa ocorre antes da conexão, inclusive na carga real.
    try:
        payload = prepare_payload(args.input)
    except (OSError, ValueError, UnicodeError, csv.Error) as exc:
        print(f"Erro no catálogo: {exc}", file=sys.stderr)
        return 1

    report = {
        "status": "ok", "dry_run": args.dry_run,
        "CPU": len(payload["CPU"]), "GPU": len(payload["GPU"]),
        "input": str(args.input),
    }
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
                nodes_created = session.execute_write(write_hardware, payload)
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
