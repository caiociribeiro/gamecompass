"""Coleta, valida, processa e opcionalmente carrega todo o catálogo selecionado.

Sem --load, não abre conexão com o Neo4j. Coletas válidas são reutilizadas
com --fetch; um lote interrompido pode ser retomado com o mesmo comando.
"""

import argparse
import csv
import json
from pathlib import Path
import sys
import time

from fetch_games import main as fetch_main
from game_catalog import ROOT, build_catalog, read_selection
from hardware_catalog import process_catalog, read_catalog
from hardware_matcher import normalize_name, read_aliases
from load_games import main as load_games_main
from load_hardware import main as load_hardware_main
from process_requirements import write_json_atomic
from requirements_curation import read_curation
from review_game_requirements import review_catalog
from reuse_snapshots import reuse_snapshots


def require_success(stage: str, code: int) -> None:
    if code != 0:
        raise ValueError(f"Etapa {stage} falhou (código {code}); as próximas etapas não foram executadas.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--fetch", action="store_true", help="Coleta ou retoma o lote Steam antes de processar.")
    parser.add_argument("--reuse-snapshot-dir", type=Path,
                        help="Com --fetch, copia coletas verificadas de um lote anterior para a pasta nova.")
    parser.add_argument("--load", action="store_true", help="Carrega hardware e jogos no Neo4j após validar os dois.")
    parser.add_argument("--attempts", type=int, choices=range(1, 6), default=3,
                        help="Número máximo de tentativas para concluir uma coleta parcial.")
    parser.add_argument("--selection", type=Path, default=ROOT / "data/catalog/games.json")
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/catalog/hardware_manual_v1.csv")
    parser.add_argument("--aliases", type=Path, default=ROOT / "data/catalog/hardware_aliases.json")
    parser.add_argument("--curation", type=Path, default=ROOT / "data/catalog/requirements_curation.json")
    parser.add_argument("--processed-dir", type=Path, default=None,
        help="Pasta das saídas. Sem ela, o hardware vai para data/processed e os jogos para "
             "data/catalog/games_manual_v1.json, o arquivo versionado que o serviço catalog carrega.")
    args = parser.parse_args(argv)
    try:
        hardware_output = (args.processed_dir or ROOT / "data/processed") / "hardware_manual_v1.csv"
        games_output = (args.processed_dir / "games_manual_v1.json" if args.processed_dir
                        else ROOT / "data/catalog/games_manual_v1.json")
        inputs = {p.resolve() for p in (args.selection, args.catalog, args.aliases, args.curation)}
        snapshot = args.snapshot_dir.resolve()
        protected_snapshots = [snapshot]
        if args.reuse_snapshot_dir is not None:
            protected_snapshots.append(args.reuse_snapshot_dir.resolve())
        for output in (hardware_output, games_output):
            if output.resolve() in inputs or any(output.resolve() == root or root in output.resolve().parents
                                                  for root in protected_snapshots):
                raise ValueError("As saídas devem ser diferentes das entradas e ficar fora dos snapshots.")
        read_selection(args.selection)
        records = read_catalog(args.catalog, catalog_format="manual")
        index = {(r["component_type"], normalize_name(r["name"])): r for r in records}
        read_aliases(args.aliases, index)
        read_curation(args.curation, index)
        if args.reuse_snapshot_dir is not None:
            if not args.fetch:
                raise ValueError("Use --fetch junto de --reuse-snapshot-dir para completar o novo lote.")
            reused = reuse_snapshots(args.reuse_snapshot_dir, args.snapshot_dir, args.selection)
            print(json.dumps({"status": "ok", "stage": "reuse", "snapshots_reused": reused}, ensure_ascii=False), flush=True)
        if args.fetch:
            for attempt in range(args.attempts):
                code = fetch_main(["--selection", str(args.selection), "--output-dir", str(args.snapshot_dir), "--resume"])
                if code != 2 or attempt + 1 == args.attempts:
                    require_success("coleta Steam", code)
                    break
                time.sleep(2 * (attempt + 1))
        # Valida todos os snapshots antes de substituir saídas ou abrir o banco.
        data = build_catalog(args.snapshot_dir, args.selection, args.catalog, args.aliases, args.curation)
        coverage = review_catalog(data)["summary"]
        counts = process_catalog(args.catalog, hardware_output, catalog_format="manual")
        write_json_atomic(games_output, data)
        load_args = ["--input", str(games_output), "--catalog", str(args.catalog),
                     "--aliases", str(args.aliases), "--curation", str(args.curation)]
        require_success("validação da carga", load_games_main([*load_args, "--dry-run"]))
        if args.load:
            require_success("carga do hardware", load_hardware_main([
                "--format", "manual", "--input", str(hardware_output)]))
            require_success("carga dos jogos", load_games_main(load_args))
        result = {"status": "ok", "loaded": args.load, "games": len(data["games"]),
            "CPU": counts["CPU"], "GPU": counts["GPU"],
            "windows_comparison_basis": coverage["with_comparison_basis"],
            "windows_needs_curation": coverage["requiring_curation"],
            "games_with_manual_references": sum(any(block and block.get("curation")
                for block in (g["platforms"]["Windows"][level] for level in ("minimum", "recommended")))
                for g in data["games"]), "output": str(games_output)}
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return 0
    except (OSError, ValueError, UnicodeError, csv.Error) as exc:
        print(f"Erro na atualização do catálogo: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
