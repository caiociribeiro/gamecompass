"""Contrato, normalização e validação do catálogo de benchmarks.

Exibir o contrato: python scripts/hardware_catalog.py --describe
Processar CSV:     python scripts/hardware_catalog.py

Este módulo não coleta dados da internet e não altera o Neo4j.
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


def read_catalog(path: Path) -> list[dict[str, str | int]]:
    """Valida o conjunto completo antes de liberar a escrita do resultado."""
    records = []
    seen = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames != list(COLUMNS):
            raise ValueError("Cabeçalho esperado, nesta ordem: " + ",".join(COLUMNS))
        for row in reader:
            try:
                record = normalize_record(row)
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


def process_catalog(input_path: Path, output_path: Path) -> Counter:
    """Mantém a entrada intacta e substitui a saída apenas após validar tudo."""
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Entrada e saída devem ser arquivos diferentes.")
    records = read_catalog(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=output_path.parent,
            prefix=".hardware-", suffix=".tmp", delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(records)
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return Counter(row["component_type"] for row in records)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--describe", action="store_true", help="Exibe o contrato sem ler nem criar arquivos.")
    parser.add_argument("--input", type=Path, default=ROOT / "data/raw/hardware_benchmarks.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/hardware_benchmarks.csv")
    args = parser.parse_args(argv)
    if args.describe:
        print(json.dumps({
            "columns": list(COLUMNS), "benchmarks": BENCHMARKS,
            "passmark_score": "inteiro positivo", "collected_at": "ISO 8601 com fuso",
        }, ensure_ascii=False, indent=2))
        return 0
    try:
        counts = process_catalog(args.input, args.output)
    except (OSError, ValueError, UnicodeError, csv.Error) as exc:
        print(f"Erro no catálogo: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "ok", "CPU": counts["CPU"], "GPU": counts["GPU"],
        "output": str(args.output),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
