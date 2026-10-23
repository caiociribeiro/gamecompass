"""Integra limpeza do HTML, normalização da RAM e matching de CPU/GPU.

Recebe um bloco de requisitos mínimos OU recomendados via --text ou --input.
Imprime JSON e permite salvá-lo com --output, preservando as entradas.
"""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from hardware_catalog import ROOT, read_catalog
from hardware_matcher import match_alternatives, normalize_name, read_aliases
from regex_parser import clean_html, extract_hardware_text, extract_ram_gb


def process_requirements(html: str, catalog: dict, aliases: dict) -> dict:
    """Processa cada campo e preserva resultados parciais para revisão."""
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

            result = match_alternatives(text, kind, catalog, aliases)
            hardware[kind] = result
            requirements[f"{kind.lower()}_score"] = result["required_score"]

            if result["status"] != "resolved":
                issues.append(f"{kind}: há alternativas não identificadas.")
        except ValueError as exc:
            issues.append(f"{kind}: {exc}")

    return {
        "status": "resolved" if not issues else "needs_review",
        "requirements": requirements,
        "issues": issues,
        "hardware": hardware,
        "text": clean_html(html),
    }


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
        default=ROOT / "data/processed/hardware_benchmarks.csv",
    )
    parser.add_argument(
        "--aliases",
        type=Path,
        help="JSON opcional com aliases revisados.",
    )
    args = parser.parse_args(argv)

    try:
        inputs = [
            path
            for path in (args.input, args.catalog, args.aliases)
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

        records = read_catalog(args.catalog)
        catalog = {
            (row["component_type"], normalize_name(row["name"])): row
            for row in records
        }
        aliases = read_aliases(args.aliases, catalog)

        result = process_requirements(html, catalog, aliases)
        result["source"] = {
            "input_path": (
                str(args.input) if args.input is not None else None
            ),
            "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
            "catalog_path": str(args.catalog),
            "catalog_sha256": hashlib.sha256(
                args.catalog.read_bytes()
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