"""Resume a cobertura dos requisitos; não simula aprovação de um computador."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from game_catalog import validate_catalog
from extract_steam_requirements import is_notes_only_requirement_text
from hardware_catalog import MANUAL_SCORE_VERSION
from hardware_matcher import normalize_name
from hardware_review import validate_manual_classification
from process_requirements import write_json_atomic


def review_catalog(data: dict, platform: str = "Windows") -> dict:
    validate_catalog(data)
    if platform not in ("Windows", "Linux", "macOS"):
        raise ValueError("Plataforma inválida.")
    rows, pending = [], {}
    totals = {level: Counter() for level in ("minimum", "recommended")}
    for game in data["games"]:
        levels = {}
        for level in totals:
            block = game["platforms"][platform][level]
            fields = {}
            notes_only = block is not None and is_notes_only_requirement_text(block["text"])
            if block is None or notes_only:
                status = "not_provided"
            else:
                for kind in ("CPU", "GPU"):
                    mapping = block.get("hardware", {})
                    if not isinstance(mapping, dict):
                        raise ValueError("Mapa de hardware inválido no bloco de requisitos.")
                    hardware = mapping.get(kind)
                    alternatives = hardware.get("alternatives", []) if isinstance(hardware, dict) else []
                    if not isinstance(alternatives, list) or any(not isinstance(a, dict) for a in alternatives):
                        raise ValueError("Lista de alternativas inválida.")
                    for alternative in alternatives:
                        if alternative.get("component_type") != kind or alternative.get("status") not in ("matched", "not_found"):
                            raise ValueError("Identificação de alternativa inválida.")
                        validate_manual_classification(alternative, Path(game["id"]), kind)
                    names = [a["name"] for a in alternatives
                        if a.get("status") == "matched" and a.get("score_status") == "classified"
                        and a.get("component_type") == kind and a.get("score_version") == MANUAL_SCORE_VERSION
                        and type(a.get("performance_score")) is int and a["performance_score"] > 0]
                    required = block["requirements"][f"{kind.lower()}_score"]
                    fields[kind] = {"status": "resolved" if required is not None else "has_known_alternative" if names else "needs_review",
                        "identified_models": names}
                    if fields[kind]["status"] == "needs_review":
                        fields[kind]["reason"] = (
                            "not_provided" if f"{kind}: campo ausente." in block["issues"] and hardware is None
                            else "unclassified" if any(a.get("score_status") == "pending" for a in alternatives)
                            else "unidentified" if alternatives else "unparsed")
                    for alternative in alternatives:
                        if alternative.get("score_status") != "classified":
                            query = alternative.get("query")
                            if not isinstance(query, str) or not query.strip():
                                raise ValueError("Alternativa pendente sem consulta de origem.")
                            item = pending.setdefault((kind, normalize_name(query)),
                                {"component_type": kind, "query": query, "sources": []})
                            item["sources"].append({"id": game["id"], "title": game["title"], "level": level})
                fields["RAM"] = {"status": "resolved" if block["requirements"]["ram_gb"] is not None else "needs_review"}
                fields["OS"] = {"status": "resolved" if block.get("os_text") else "needs_review"}
                if fields["RAM"]["status"] == "needs_review":
                    fields["RAM"]["reason"] = "not_provided" if "RAM: campo ausente." in block["issues"] else "unparsed"
                if fields["OS"]["status"] == "needs_review":
                    fields["OS"]["reason"] = "not_provided_or_unparsed"
                states = [field["status"] for field in fields.values()]
                status = "needs_review" if "needs_review" in states else "has_known_alternative" if "has_known_alternative" in states else "resolved"
            levels[level] = {"status": status, "fields": fields,
                **({"requirements_kind": "notes_only"} if notes_only else {}),
                "blocking_fields": [{"field": key, "reason": value["reason"]}
                                    for key, value in fields.items() if value["status"] == "needs_review"]}
            totals[level][status] += 1
        basis = any(level["status"] in ("resolved", "has_known_alternative") for level in levels.values())
        rows.append({"id": game["id"], "title": game["title"], "has_comparison_basis": basis, **levels})
    return {"platform": platform, "score_version": data["score_version"],
        "note": "Cobertura de dados; o atendimento depende do perfil, do SO e das alternativas suficientes.",
        "summary": {"games": len(rows), "with_comparison_basis": sum(r["has_comparison_basis"] for r in rows),
            "requiring_curation": sum(not r["has_comparison_basis"] for r in rows),
            "notes_only": {level: sum(row[level].get("requirements_kind") == "notes_only" for row in rows)
                           for level in totals},
            **{level: {key: totals[level][key] for key in ("resolved", "has_known_alternative", "needs_review", "not_provided")} for level in totals}},
        "pending_queries": [pending[key] for key in sorted(pending)], "games": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Salva o relatório opcional; sem este argumento, só imprime o resumo.")
    parser.add_argument("--platform", choices=("Windows", "Linux", "macOS"), default="Windows")
    args = parser.parse_args(argv)
    try:
        if args.output is not None and args.input.resolve() == args.output.resolve():
            raise ValueError("A saída deve ser diferente da entrada.")
        raw = args.input.read_bytes()
        result = review_catalog(json.loads(raw.decode("utf-8-sig")), args.platform)
        result["source"] = {"input_path": str(args.input), "input_sha256": hashlib.sha256(raw).hexdigest()}
        if args.output is not None:
            write_json_atomic(args.output, result)
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"Erro na revisão dos jogos: {exc}", file=sys.stderr)
        return 1
    summary = {"status": "ok", **result["summary"]}
    if args.output is not None:
        summary["output"] = str(args.output)
    else:
        summary["pending_games"] = [{"id": row["id"], "title": row["title"],
            "levels": {level: row[level]["blocking_fields"] for level in ("minimum", "recommended")
                       if row[level]["status"] == "needs_review"}}
            for row in result["games"] if any(row[level]["status"] == "needs_review" for level in ("minimum", "recommended"))]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
