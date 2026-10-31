"""Coleta os jogos da seleção editorial sem sobrescrever snapshots existentes."""

import argparse
import json
from pathlib import Path
import sys
import time

from fetch_steam import fetch_app, save_snapshot
from game_catalog import ROOT, read_selection, sha256
from process_requirements import write_json_atomic


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, default=ROOT / "data/catalog/games.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true", help="Continua o mesmo lote sem refazer coletas válidas.")
    args = parser.parse_args(argv)
    try:
        selection = read_selection(args.selection)
        manifest = args.output_dir / "collection.json"
        digest = sha256(args.selection)
        if args.output_dir.exists():
            if not args.resume or not manifest.is_file():
                raise ValueError("Pasta já existe; use outra ou --resume para um lote iniciado por este script.")
            previous = json.loads(manifest.read_text())
            if not isinstance(previous, dict) or previous.get("selection_sha256") != digest:
                raise ValueError("A seleção mudou; inicie um novo lote de coletas.")
        else:
            args.output_dir.mkdir(parents=True)
            write_json_atomic(manifest, {"selection_sha256": digest, "status": "collecting", "issues": []})
        issues = []
        for row in selection["games"]:
            target = args.output_dir / row["id"]
            if target.exists():
                from extract_steam_requirements import extract_snapshot
                snapshot = extract_snapshot(target)
                if snapshot["id"] != row["id"]:
                    raise ValueError("Snapshot salvo com identificação divergente.")
                continue
            try:
                raw, metadata = fetch_app(row["id"], language="portuguese")
                save_snapshot(target, raw, metadata)
                print(json.dumps({"appid": row["id"], "title": metadata["title"], "status": "collected"}, ensure_ascii=False), flush=True)
            except (OSError, ValueError, UnicodeError) as exc:
                issues.append({"appid": row["id"], "message": str(exc)})
            time.sleep(0.4)
        result = {"selection_sha256": digest, "status": "partial" if issues else "ok", "games": len(selection["games"]), "issues": issues}
        write_json_atomic(manifest, result)
        print(json.dumps(result, ensure_ascii=False))
        return 2 if issues else 0
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"Erro na coleta de jogos: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
