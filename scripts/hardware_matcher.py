"""Associa um modelo ao catálogo por nome exato ou alias explícito.

Cada consulta recebe um único modelo. Campos com alternativas serão
tratados em uma próxima etapa. Ausência de match retorna score nulo.
"""

import argparse
import csv
import json
from pathlib import Path
import sys

from hardware_catalog import BENCHMARKS, ROOT, read_catalog


def normalize_name(name: str) -> str:
    """Uniformiza espaços e caixa, preservando variantes, números e sufixos."""
    return " ".join(name.split()).casefold()


def read_aliases(path: Path | None, catalog: dict) -> dict:
    """Valida todos os aliases antes da consulta; cada destino deve existir."""
    if path is None:
        return {}

    rows = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(rows, list):
        raise ValueError("O arquivo de aliases deve conter uma lista JSON.")

    aliases = {}
    expected = {"component_type", "alias", "canonical_name"}

    for position, row in enumerate(rows, start=1):
        if (
            not isinstance(row, dict)
            or set(row) != expected
            or any(
                not isinstance(value, str) or not value.strip()
                for value in row.values()
            )
        ):
            raise ValueError(
                f"Alias {position}: campos obrigatórios inválidos."
            )

        kind = row["component_type"].strip().upper()
        if kind not in BENCHMARKS:
            raise ValueError(
                f"Alias {position}: component_type deve ser CPU ou GPU."
            )

        key = (kind, normalize_name(row["alias"]))
        target = (kind, normalize_name(row["canonical_name"]))

        if target not in catalog:
            raise ValueError(
                f"Alias {position}: modelo canônico ausente no catálogo."
            )

        if key in aliases or (key in catalog and key != target):
            raise ValueError(
                f"Alias {position}: nome duplicado ou conflito com o catálogo."
            )

        aliases[key] = target

    return aliases


def match_hardware(
    name: str,
    component_type: str,
    catalog: dict,
    aliases: dict,
) -> dict:
    """Consulta um índice validado; um modelo desconhecido mantém score None."""
    kind = component_type.strip().upper()

    if kind not in BENCHMARKS:
        raise ValueError("component_type deve ser CPU ou GPU.")
    if not name.strip():
        raise ValueError("Informe um nome de modelo.")

    key = (kind, normalize_name(name))
    record = catalog.get(key)
    method = "exact" if record is not None else None

    if record is None and key in aliases:
        record = catalog[aliases[key]]
        method = "alias"

    return {
        "status": "matched" if record is not None else "not_found",
        "component_type": kind,
        "query": name,
        "name": record["name"] if record is not None else None,
        "passmark_score": (
            record["passmark_score"] if record is not None else None
        ),
        "method": method,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--catalog",
        type=Path,
        default=ROOT / "data/processed/hardware_benchmarks.csv",
    )
    parser.add_argument(
        "--aliases",
        type=Path,
        help="JSON opcional com aliases revisados.",
    )
    parser.add_argument(
        "--type",
        dest="component_type",
        choices=BENCHMARKS,
        required=True,
    )
    parser.add_argument("--name", required=True)
    args = parser.parse_args(argv)

    try:
        records = read_catalog(args.catalog)

        catalog = {
            (row["component_type"], normalize_name(row["name"])): row
            for row in records
        }

        aliases = read_aliases(args.aliases, catalog)
        result = match_hardware(
            args.name,
            args.component_type,
            catalog,
            aliases,
        )
    except (OSError, ValueError, UnicodeError, csv.Error) as exc:
        print(f"Erro no matching: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())