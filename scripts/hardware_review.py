"""Reúne modelos não identificados e outras pendências dos requisitos."""

import argparse
import json
from pathlib import Path
import sys

from hardware_matcher import normalize_name
from process_requirements import write_json_atomic


def collect_review(paths: list[Path]) -> dict:
    """Agrupa consultas por tipo/nome e preserva suas origens."""
    pending = {}
    document_issues = []
    needs_review = False

    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if (
            not isinstance(data, dict)
            or data.get("status") not in ("resolved", "needs_review")
            or not isinstance(data.get("issues"), list)
            or any(not isinstance(issue, str) for issue in data["issues"])
            or not isinstance(data.get("hardware"), dict)
            or not {"CPU", "GPU"}.issubset(data["hardware"])
        ):
            raise ValueError(
                f"{path}: formato de requisitos processados inválido."
            )

        if data["status"] == "needs_review" or data["issues"]:
            needs_review = True
            document_issues.append({
                "path": str(path),
                "issues": data["issues"],
            })

        for kind in ("CPU", "GPU"):
            block = data["hardware"][kind]
            if block is None:
                if not data["issues"]:
                    raise ValueError(
                        f"{path}: {kind} ausente sem pendência registrada."
                    )
                continue

            if (
                not isinstance(block, dict)
                or block.get("component_type") != kind
                or block.get("status") not in ("resolved", "needs_review")
                or not isinstance(block.get("alternatives"), list)
                or not block["alternatives"]
            ):
                raise ValueError(f"{path}: bloco de {kind} inválido.")

            if block["status"] == "needs_review":
                needs_review = True

            for alternative in block["alternatives"]:
                if (
                    not isinstance(alternative, dict)
                    or alternative.get("component_type") != kind
                    or alternative.get("status") not in ("matched", "not_found")
                    or not isinstance(alternative.get("query"), str)
                    or not alternative["query"].strip()
                ):
                    raise ValueError(
                        f"{path}: alternativa de {kind} inválida."
                    )

                if alternative["status"] == "matched":
                    continue

                key = (kind, normalize_name(alternative["query"]))
                item = pending.setdefault(
                    key,
                    {
                        "component_type": kind,
                        "query": alternative["query"],
                        "sources": [],
                    },
                )
                if str(path) not in item["sources"]:
                    item["sources"].append(str(path))

    return {
        "status": "needs_review" if needs_review or pending else "resolved",
        "files_read": len(paths),
        "pending_models": [pending[key] for key in sorted(pending)],
        "document_issues": document_issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        inputs = [path.resolve() for path in args.input]
        if len(set(inputs)) != len(inputs):
            raise ValueError("Há arquivos de entrada repetidos.")
        if args.output.resolve() in inputs:
            raise ValueError(
                "A saída deve ser diferente de todas as entradas."
            )

        result = collect_review(args.input)
        write_json_atomic(args.output, result)
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"Erro no relatório de revisão: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())