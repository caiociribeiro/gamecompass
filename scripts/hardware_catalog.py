"""Valida catálogos de hardware sem coletar dados nem alterar o Neo4j.

Índice manual: python scripts/hardware_catalog.py --format manual --describe

O formato passmark permanece como padrão nesta etapa da migração, para
preservar os scripts existentes. Não converte pontuações entre os formatos.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
COLUMNS = (
    "component_type", "name", "passmark_score", "benchmark",
    "source_url", "collected_at",
)
BENCHMARKS = {"CPU": "CPU Mark", "GPU": "G3D Mark"}
COMPONENT_TYPES = ("CPU", "GPU")
MANUAL_COLUMNS = (
    "component_type", "name", "performance_score", "score_version",
    "source_url", "collected_at", "notes",
)
MANUAL_SCORE_VERSION = "manual_v1"
SOURCE_DOMAINS = {
    "CPU": {"cpubenchmark.net", "www.cpubenchmark.net", "passmark.com", "www.passmark.com"},
    "GPU": {"videocardbenchmark.net", "www.videocardbenchmark.net", "passmark.com", "www.passmark.com"},
}
SCORE_PATTERN = re.compile(r"(?:[1-9][0-9]*|[1-9][0-9]{0,2}(?:,[0-9]{3})+)\Z")


def normalize_record(row: dict[str, str]) -> dict[str, str | int]:
    """Preserva o modelo e sua variante; normaliza apenas espaços e formato."""
    if set(row) != set(COLUMNS) or any(not isinstance(v, str) for v in row.values()):
        raise ValueError("Quantidade de colunas inválida; confira separadores e aspas do CSV.")
    component_type = row["component_type"].strip().upper()
    if component_type not in BENCHMARKS:
        raise ValueError("component_type deve ser CPU ou GPU.")
    name = " ".join(row["name"].split())
    if not name:
        raise ValueError("O nome do modelo está vazio.")
    benchmark = " ".join(row["benchmark"].split())
    if benchmark.casefold() != BENCHMARKS[component_type].casefold():
        raise ValueError(f"{component_type} exige a métrica {BENCHMARKS[component_type]}.")

    score_text = row["passmark_score"].strip()
    if not SCORE_PATTERN.fullmatch(score_text):
        raise ValueError("passmark_score deve ser inteiro positivo, sem aproximações ou decimais.")
    score = int(score_text.replace(",", ""))

    source_url = row["source_url"].strip()
    source = urlsplit(source_url)
    if (
        source.scheme != "https"
        or source.hostname not in SOURCE_DOMAINS[component_type]
        or source.username is not None
        or source.password is not None
        or source.port not in (None, 443)
    ):
        raise ValueError("source_url deve apontar para uma página HTTPS da fonte PassMark correspondente.")

    collected_at = datetime.fromisoformat(row["collected_at"].strip().replace("Z", "+00:00"))
    if collected_at.tzinfo is None or collected_at.utcoffset() is None:
        raise ValueError("collected_at deve incluir data, hora e fuso, por exemplo o sufixo Z para UTC.")

    return {
        "component_type": component_type,
        "name": name,
        "passmark_score": score,
        "benchmark": BENCHMARKS[component_type],
        "source_url": source_url,
        "collected_at": collected_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def normalize_manual_record(row: dict[str, str]) -> dict[str, str | int | None]:
    """Valida uma classificação manual; score vazio mantém a peça pendente."""
    if set(row) != set(MANUAL_COLUMNS) or any(
        not isinstance(value, str) for value in row.values()
    ):
        raise ValueError(
            "Quantidade de colunas inválida; confira separadores e aspas do CSV."
        )

    component_type = row["component_type"].strip().upper()
    if component_type not in COMPONENT_TYPES:
        raise ValueError("component_type deve ser CPU ou GPU.")

    name = " ".join(row["name"].split())
    if not name:
        raise ValueError("O nome do modelo está vazio.")

    score_text = row["performance_score"].strip()
    score = None
    if score_text:
        if not re.fullmatch(r"[1-9][0-9]*", score_text):
            raise ValueError(
                "performance_score deve ser inteiro positivo ou vazio "
                "quando a classificação estiver pendente."
            )
        score = int(score_text)

    score_version = row["score_version"].strip()
    if score_version != MANUAL_SCORE_VERSION:
        raise ValueError(f"score_version deve ser {MANUAL_SCORE_VERSION}.")

    source_url = row["source_url"].strip()
    source = urlsplit(source_url)
    if (
        source.scheme != "https"
        or not source.hostname
        or any(char.isspace() for char in source_url)
        or source.username is not None
        or source.password is not None
        or source.port not in (None, 443)
    ):
        raise ValueError("source_url deve ser uma URL HTTPS válida, sem credenciais.")

    collected_at = datetime.fromisoformat(
        row["collected_at"].strip().replace("Z", "+00:00")
    )
    if collected_at.tzinfo is None or collected_at.utcoffset() is None:
        raise ValueError("collected_at deve incluir data, hora e fuso.")

    notes = row["notes"].strip()
    if not notes:
        raise ValueError(
            "notes deve registrar a justificativa ou a pendência da classificação."
        )

    return {
        "component_type": component_type,
        "name": name,
        "performance_score": score,
        "score_version": score_version,
        "source_url": source_url,
        "collected_at": collected_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "notes": notes,
    }


def read_catalog(
    path: Path, *, catalog_format: str = "passmark",
) -> list[dict[str, str | int | None]]:
    """Valida o conjunto completo antes de liberar a escrita do resultado."""
    if catalog_format not in ("passmark", "manual"):
        raise ValueError("catalog_format deve ser passmark ou manual.")
    columns = MANUAL_COLUMNS if catalog_format == "manual" else COLUMNS
    normalize = normalize_manual_record if catalog_format == "manual" else normalize_record
    records = []
    seen = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames != list(columns):
            raise ValueError("Cabeçalho esperado, nesta ordem: " + ",".join(columns))
        for row in reader:
            try:
                record = normalize(row)
                key = (record["component_type"], record["name"].casefold())
                if key in seen:
                    raise ValueError("Modelo duplicado dentro do mesmo tipo de componente.")
                seen.add(key)
                records.append(record)
            except ValueError as exc:
                raise ValueError(f"Linha {reader.line_num}: {exc}") from exc
    if not records:
        raise ValueError("Catálogo vazio: forneça registros reais antes de processar.")
    return sorted(records, key=lambda row: (row["component_type"], row["name"].casefold()))


def process_catalog(
    input_path: Path, output_path: Path, *, catalog_format: str = "passmark",
) -> Counter:
    """Mantém a entrada intacta e substitui a saída apenas após validar tudo."""
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Entrada e saída devem ser arquivos diferentes.")
    records = read_catalog(input_path, catalog_format=catalog_format)
    columns = MANUAL_COLUMNS if catalog_format == "manual" else COLUMNS
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=output_path.parent,
            prefix=".hardware-", suffix=".tmp", delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(records)
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return Counter(row["component_type"] for row in records)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format", dest="catalog_format", choices=("passmark", "manual"),
        default="passmark",
        help="manual usa o novo índice; passmark preserva o formato antigo.",
    )
    parser.add_argument("--describe", action="store_true", help="Exibe o contrato sem ler nem criar arquivos.")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.describe:
        if args.catalog_format == "manual":
            print(json.dumps({
                "format": "manual",
                "columns": list(MANUAL_COLUMNS),
                "component_types": list(COMPONENT_TYPES),
                "performance_score": "inteiro positivo ou vazio (classificação pendente)",
                "score_version": MANUAL_SCORE_VERSION,
                "collected_at": "ISO 8601 com fuso",
                "notes": "justificativa ou pendência obrigatória",
            }, ensure_ascii=False, indent=2))
            return 0
        print(json.dumps({
            "columns": list(COLUMNS), "benchmarks": BENCHMARKS,
            "passmark_score": "inteiro positivo", "collected_at": "ISO 8601 com fuso",
        }, ensure_ascii=False, indent=2))
        return 0

    filename = (
        "hardware_manual_v1.csv" if args.catalog_format == "manual"
        else "hardware_benchmarks.csv"
    )
    input_path = args.input if args.input is not None else ROOT / "data/raw" / filename
    output_path = args.output if args.output is not None else ROOT / "data/processed" / filename
    try:
        counts = process_catalog(
            input_path, output_path, catalog_format=args.catalog_format,
        )
    except (OSError, ValueError, UnicodeError, csv.Error) as exc:
        print(f"Erro no catálogo: {exc}", file=sys.stderr)
        return 1
    report = {
        "status": "ok", "CPU": counts["CPU"], "GPU": counts["GPU"],
        "output": str(output_path),
    }
    if args.catalog_format == "manual":
        report.update(format="manual", score_version=MANUAL_SCORE_VERSION)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
