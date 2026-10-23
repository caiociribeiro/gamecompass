"""Verifica a conexão da camada de dados, sem inserir ou alterar registros.

Na raiz do projeto: docker compose run --rm data
"""

import json
import os
import sys

from neo4j import GraphDatabase
from neo4j.exceptions import DriverError, Neo4jError


def main() -> int:
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
            with driver.session(database=database, default_access_mode="READ") as session:
                record = session.run("RETURN 1 AS status").single(strict=True)
                if record is None or record["status"] != 1:
                    print("Resposta inesperada do Neo4j.", file=sys.stderr)
                    return 1
    except (DriverError, Neo4jError, OSError, ValueError) as exc:
        print(
            f"Falha de conexão ({type(exc).__name__}). "
            "Confira o serviço neo4j e as variáveis de ambiente.",
            file=sys.stderr,
        )
        return 1

    print(json.dumps({"status": "ok", "database": database, "query_result": 1}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
