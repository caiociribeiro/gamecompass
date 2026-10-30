"""Associa modelos ao catálogo por nome exato ou alias explícito.

Use --alternatives para separar modelos ligados por 'ou' ou 'or'.
Cada alternativa mantém sua identificação e sua pontuação.
Use --format manual para consultar performance_score no índice manual_v1.
"""

import argparse
import csv
import json
from pathlib import Path
import sys
import re

from hardware_catalog import COMPONENT_TYPES, MANUAL_SCORE_VERSION, ROOT, read_catalog


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
        if kind not in COMPONENT_TYPES:
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
    *,
    catalog_format: str = "passmark",
) -> dict:
    """Consulta um índice validado; um modelo desconhecido mantém score None."""
    kind = component_type.strip().upper()

    if catalog_format not in ("passmark", "manual"):
        raise ValueError("catalog_format deve ser passmark ou manual.")
    if kind not in COMPONENT_TYPES:
        raise ValueError("component_type deve ser CPU ou GPU.")
    if not name.strip():
        raise ValueError("Informe um nome de modelo.")

    key = (kind, normalize_name(name))
    record = catalog.get(key)
    method = "exact" if record is not None else None

    if record is None and key in aliases:
        record = catalog[aliases[key]]
        method = "alias"

    result = {
        "status": "matched" if record is not None else "not_found",
        "component_type": kind,
        "query": name,
        "name": record["name"] if record is not None else None,
        "method": method,
    }
    if catalog_format == "manual":
        if record is not None and record.get("score_version") != MANUAL_SCORE_VERSION:
            raise ValueError(f"O modelo deve usar score_version {MANUAL_SCORE_VERSION}.")
        score = record["performance_score"] if record is not None else None
        if score is not None and (type(score) is not int or score <= 0):
            raise ValueError("performance_score deve ser inteiro positivo ou None.")
        result.update(
            performance_score=score,
            score_version=record["score_version"] if record is not None else None,
            score_status=(
                "not_found" if record is None
                else "pending" if score is None else "classified"
            ),
        )
    else:
        result["passmark_score"] = record["passmark_score"] if record is not None else None
    return result

def split_alternatives(text: str) -> list[str]:
    """Separa alternativas explícitas, preservando o texto de cada modelo."""
    parts = re.split(
        r"\b(?:ou|or)\b",
        text,
        flags=re.IGNORECASE,
    )
    parts = [part.strip() for part in parts]

    if any(not part for part in parts):
        raise ValueError("Há uma alternativa vazia no requisito.")

    return parts


def match_alternatives(
    text: str,
    component_type: str,
    catalog: dict,
    aliases: dict,
    *,
    catalog_format: str = "passmark",
) -> dict:
    """Calcula o limite somente se todas as alternativas estiverem avaliadas."""
    kind = component_type.strip().upper()

    results = [
        match_hardware(name, kind, catalog, aliases, catalog_format=catalog_format)
        for name in split_alternatives(text)
    ]

    score_key = "performance_score" if catalog_format == "manual" else "passmark_score"
    resolved = all(
        result["status"] == "matched" and result[score_key] is not None
        for result in results
    )

    required_score = None
    if resolved:
        required_score = min(
            result[score_key]
            for result in results
        )

    output = {
        "status": "resolved" if resolved else "needs_review",
        "component_type": kind,
        "query": text,
        "required_score": required_score,
        "alternatives": results,
    }
    if catalog_format == "manual":
        output["score_version"] = MANUAL_SCORE_VERSION
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format", dest="catalog_format", choices=("passmark", "manual"),
        default="passmark", help="Formato do catálogo; manual usa o novo índice.",
    )

    parser.add_argument(
        "--catalog",
        type=Path,
    )
    parser.add_argument(
        "--aliases",
        type=Path,
        help="JSON opcional com aliases revisados.",
    )
    parser.add_argument(
        "--type",
        dest="component_type",
        choices=COMPONENT_TYPES,
        required=True,
    )
    parser.add_argument("--name", required=True)
    parser.add_argument(
        "--alternatives",
        action="store_true",
        help="Consulta alternativas separadas por 'ou' ou 'or'.",
    )
    args = parser.parse_args(argv)

    try:
        filename = (
            "hardware_manual_v1.csv" if args.catalog_format == "manual"
            else "hardware_benchmarks.csv"
        )
        catalog_path = args.catalog if args.catalog is not None else ROOT / "data/processed" / filename
        records = read_catalog(catalog_path, catalog_format=args.catalog_format)

        catalog = {
            (row["component_type"], normalize_name(row["name"])): row
            for row in records
        }

        aliases = read_aliases(args.aliases, catalog)
        if args.alternatives:
            result = match_alternatives(
                args.name,
                args.component_type,
                catalog,
                aliases,
                catalog_format=args.catalog_format,
            )
        else:
            result = match_hardware(
                args.name,
                args.component_type,
                catalog,
                aliases,
                catalog_format=args.catalog_format,
            )
    except (OSError, ValueError, UnicodeError, csv.Error) as exc:
        print(f"Erro no matching: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())