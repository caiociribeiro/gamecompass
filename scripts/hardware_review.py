"""Reúne modelos desconhecidos e classificações manuais pendentes.

Não mistura documentos dos formatos manual e passmark no mesmo relatório.
"""

import argparse
import json
from pathlib import Path
import sys

from hardware_catalog import MANUAL_SCORE_VERSION
from hardware_matcher import normalize_name
from process_requirements import write_json_atomic


def validate_manual_classification(alternative: dict, path: Path, kind: str) -> str:
    """Confere se identidade, nota e estado de classificação são coerentes."""
    if (
        "passmark_score" in alternative
        or not {"performance_score", "score_version", "score_status"}.issubset(alternative)
    ):
        raise ValueError(f"{path}: classificação de {kind} inválida.")

    score = alternative["performance_score"]
    score_status = alternative["score_status"]
    if alternative["status"] == "not_found":
        if (
            score_status != "not_found" or score is not None
            or alternative["score_version"] is not None
            or alternative.get("name") is not None
        ):
            raise ValueError(f"{path}: modelo desconhecido de {kind} com classificação inválida.")
        return score_status

    if (
        alternative["score_version"] != MANUAL_SCORE_VERSION
        or not isinstance(alternative.get("name"), str)
        or not alternative["name"].strip()
    ):
        raise ValueError(f"{path}: identificação ou versão de {kind} inválida.")
    if score is None:
        if score_status != "pending":
            raise ValueError(f"{path}: {kind} sem nota deve estar pendente.")
    elif type(score) is not int or score <= 0 or score_status != "classified":
        raise ValueError(f"{path}: nota ou estado de classificação de {kind} inválido.")
    return score_status


def collect_review(paths: list[Path]) -> dict:
    """Agrupa consultas por tipo/nome e preserva suas origens."""
    pending = {}
    pending_classifications = {}
    document_format = None
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

        current_format = data.get("catalog_format", "passmark")
        if current_format not in ("passmark", "manual"):
            raise ValueError(f"{path}: catalog_format inválido.")
        if current_format == "manual" and data.get("score_version") != MANUAL_SCORE_VERSION:
            raise ValueError(f"{path}: score_version deve ser {MANUAL_SCORE_VERSION}.")
        if current_format == "passmark" and "score_version" in data:
            raise ValueError(f"{path}: score_version exige catalog_format manual.")
        if document_format is not None and document_format != current_format:
            raise ValueError("Não misture documentos manuais e PassMark no mesmo relatório.")
        document_format = current_format

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

            if current_format == "manual" and block.get("score_version") != MANUAL_SCORE_VERSION:
                raise ValueError(f"{path}: versão do bloco de {kind} inválida.")

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

                if current_format == "manual":
                    score_status = validate_manual_classification(alternative, path, kind)
                    if score_status != "classified":
                        if block["status"] != "needs_review" or block.get("required_score") is not None:
                            raise ValueError(f"{path}: {kind} pendente com limite resolvido.")
                        needs_review = True
                    if score_status == "pending":
                        key = (kind, normalize_name(alternative["name"]))
                        item = pending_classifications.setdefault(key, {
                            "component_type": kind,
                            "name": alternative["name"],
                            "queries": [],
                            "sources": [],
                        })
                        if alternative["query"] not in item["queries"]:
                            item["queries"].append(alternative["query"])
                        if str(path) not in item["sources"]:
                            item["sources"].append(str(path))
                elif any(key in alternative for key in ("performance_score", "score_status", "score_version")):
                    raise ValueError(f"{path}: classificação manual sem metadados do formato.")

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

    result = {
        "status": "needs_review" if needs_review or pending or pending_classifications else "resolved",
        "files_read": len(paths),
        "pending_models": [pending[key] for key in sorted(pending)],
        "document_issues": document_issues,
    }
    if document_format == "manual":
        result.update(
            catalog_format="manual",
            score_version=MANUAL_SCORE_VERSION,
            pending_classifications=[pending_classifications[key] for key in sorted(pending_classifications)],
        )
    return result


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