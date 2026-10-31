"""Valida snapshots Steam e prepara jogos, gêneros e tags para o grafo."""

import argparse
import csv
import json
from pathlib import Path
import sys

from game_catalog import ROOT, build_catalog
from process_requirements import write_json_atomic


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--selection", type=Path, default=ROOT / "data/catalog/games.json")
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/catalog/hardware_manual_v1.csv")
    parser.add_argument("--aliases", type=Path, default=ROOT / "data/catalog/hardware_aliases.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/games_manual_v1.json")
    args = parser.parse_args(argv)
    try:
        output = args.output.resolve()
        inputs = (args.selection, args.catalog, args.aliases)
        if output in [x.resolve() for x in inputs] or args.snapshot_dir.resolve() == output or args.snapshot_dir.resolve() in output.parents:
            raise ValueError("A saída deve ficar fora dos snapshots e ser diferente das entradas.")
        data = build_catalog(args.snapshot_dir, args.selection, args.catalog, args.aliases)
        write_json_atomic(args.output, data)
    except (OSError, ValueError, UnicodeError, csv.Error) as exc:
        print(f"Erro no processamento de jogos: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "ok", "games": len(data["games"]), "needs_review": sum(x["status"] == "needs_review" for x in data["games"]), "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
