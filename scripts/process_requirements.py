"""Integra limpeza do HTML, normalização da RAM e matching de CPU/GPU.

Recebe um bloco de requisitos mínimos OU recomendados e imprime JSON.
Pendências de identificação recebem status needs_review.
"""

import argparse
import csv
import json
from pathlib import Path
import sys

from hardware_catalog import ROOT, read_catalog
from hardware_matcher import match_alternatives, normalize_name, read_aliases
from regex_parser import clean_html, extract_hardware_text, extract_ram_gb


def process_requirements(html: str, catalog: dict, aliases: dict) -> dict:
    """Processa cada campo e preserva resultados parciais para revisão."""
    issues = []
    requirements = {
        "ram_gb": None,
        "cpu_score": None,
        "gpu_score": None,
    }
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--text",
        required=True,
        help="Um bloco de requisitos em HTML ou texto.",
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
        records = read_catalog(args.catalog)
        catalog = {
            (row["component_type"], normalize_name(row["name"])): row
            for row in records
        }
        aliases = read_aliases(args.aliases, catalog)
        result = process_requirements(args.text, catalog, aliases)
    except (OSError, ValueError, UnicodeError, csv.Error) as exc:
        print(f"Erro no processamento: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())