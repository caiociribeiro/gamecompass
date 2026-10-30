"""Integra limpeza do HTML, normalização da RAM e matching de CPU/GPU.

Recebe um bloco de requisitos mínimos OU recomendados via --text ou --input.
Imprime JSON e permite salvá-lo com --output, preservando as entradas.
Use --format manual para processar o novo índice e registrar sua versão.
"""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from hardware_catalog import MANUAL_SCORE_VERSION, ROOT, read_catalog
from hardware_matcher import match_alternatives, normalize_name, read_aliases
from regex_parser import clean_html, extract_hardware_text, extract_ram_gb


def process_requirements(
    html: str, catalog: dict, aliases: dict, *, catalog_format: str = "passmark",
) -> dict:
    """Processa cada campo e preserva resultados parciais para revisão."""
    if catalog_format not in ("passmark", "manual"):
        raise ValueError("catalog_format deve ser passmark ou manual.")
    issues = []
    requirements = {"ram_gb": None, "cpu_score": None, "gpu_score": None}
    hardware = {"CPU": None, "GPU": None}

    try:
        requirements["ram_gb"] = extract_ram_gb(html)
        if requirements["ram_gb"] is None:
            issues.append("RAM: campo ausente.")
    except ValueError as exc:
        issues.append(f"RAM: {exc}")

    for kind in ("CPU", "GPU"):
        try:
            text = extract_hardware_text(html, kind)
            if text is None:
                issues.append(f"{kind}: campo ausente.")
                continue

            result = match_alternatives(
                text, kind, catalog, aliases, catalog_format=catalog_format,
            )
            hardware[kind] = result
            requirements[f"{kind.lower()}_score"] = result["required_score"]

            if result["status"] != "resolved":
                if any(item["status"] == "not_found" for item in result["alternatives"]):
                    issues.append(f"{kind}: há alternativas não identificadas.")
                if catalog_format == "manual" and any(
                    item["score_status"] == "pending"
                    for item in result["alternatives"]
                ):
                    issues.append(f"{kind}: há alternativas sem classificação de desempenho.")
        except ValueError as exc:
            issues.append(f"{kind}: {exc}")

    output = {
        "status": "resolved" if not issues else "needs_review",
        "requirements": requirements,
        "issues": issues,
        "hardware": hardware,
        "text": clean_html(html),
    }
    if catalog_format == "manual":
        output.update(catalog_format="manual", score_version=MANUAL_SCORE_VERSION)
    return output


def write_json_atomic(path: Path, result: dict) -> None:
    """Substitui a saída somente depois de gerar um JSON completo."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=".requirements-", dir=path.parent
    ) as directory:
        temporary = Path(directory) / "result.json"
        temporary.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format", dest="catalog_format", choices=("passmark", "manual"),
        default="passmark", help="Formato do catálogo; manual usa o novo índice.",
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--text",
        help="Um bloco de requisitos em HTML ou texto.",
    )
    source.add_argument(
        "--input",
        type=Path,
        help="Arquivo UTF-8 com um bloco de requisitos.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Caminho opcional do JSON processado.",
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
    args = parser.parse_args(argv)

    try:
        filename = (
            "hardware_manual_v1.csv" if args.catalog_format == "manual"
            else "hardware_benchmarks.csv"
        )
        catalog_path = args.catalog if args.catalog is not None else ROOT / "data/processed" / filename
        inputs = [
            path
            for path in (args.input, catalog_path, args.aliases)
            if path is not None
        ]

        if args.output is not None and any(
            args.output.resolve() == path.resolve()
            for path in inputs
        ):
            raise ValueError(
                "A saída deve ser diferente da entrada, "
                "do catálogo e dos aliases."
            )

        input_bytes = (
            args.input.read_bytes()
            if args.input is not None
            else args.text.encode("utf-8")
        )
        html = input_bytes.decode("utf-8-sig")

        records = read_catalog(catalog_path, catalog_format=args.catalog_format)
        catalog = {
            (row["component_type"], normalize_name(row["name"])): row
            for row in records
        }
        aliases = read_aliases(args.aliases, catalog)

        result = process_requirements(
            html, catalog, aliases, catalog_format=args.catalog_format,
        )
        result["source"] = {
            "input_path": (
                str(args.input) if args.input is not None else None
            ),
            "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
            "catalog_path": str(catalog_path),
            "catalog_sha256": hashlib.sha256(
                catalog_path.read_bytes()
            ).hexdigest(),
            "aliases_path": (
                str(args.aliases) if args.aliases is not None else None
            ),
            "aliases_sha256": (
                hashlib.sha256(args.aliases.read_bytes()).hexdigest()
                if args.aliases is not None
                else None
            ),
        }

        if args.output is not None:
            write_json_atomic(args.output, result)

    except (OSError, ValueError, UnicodeError, csv.Error) as exc:
        print(f"Erro no processamento: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())