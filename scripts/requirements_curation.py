"""Referências manuais por jogo para campos genéricos publicados na Steam.

Não cria aliases de famílias ou frequências. Cada regra vale para um único
AppID, plataforma, nível e texto original, e usa as notas do catálogo recebido.
"""

from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from hardware_catalog import MANUAL_SCORE_VERSION
from hardware_matcher import match_alternatives, normalize_name
from regex_parser import extract_hardware_text

FORMAT = "gamecompass_requirements_curation_v1"
PLATFORMS = ("Windows", "macOS", "Linux")


def read_curation(path: Path, catalog: dict) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if (not isinstance(data, dict) or data.get("schema_version") != FORMAT
        or not isinstance(data.get("rules"), list)):
        raise ValueError("Contrato de curadoria de requisitos inválido.")
    expected = {"id", "platform", "level", "component_type", "expected_query",
                "reference_models", "source_url", "reviewed_at", "notes"}
    result = {}
    for row in data["rules"]:
        if not isinstance(row, dict) or set(row) != expected:
            raise ValueError("Campos da referência manual inválidos.")
        if (not isinstance(row["id"], str) or not re.fullmatch(r"[1-9][0-9]{0,9}", row["id"])
            or row["platform"] not in PLATFORMS or row["level"] not in ("minimum", "recommended")
            or row["component_type"] not in ("CPU", "GPU")
            or any(not isinstance(row[k], str) or not row[k].strip()
                   for k in ("expected_query", "source_url", "reviewed_at", "notes"))):
            raise ValueError("Identificação ou justificativa da referência manual inválida.")
        source = urlsplit(row["source_url"])
        if (source.scheme != "https" or not source.hostname or source.username or source.password
            or source.port not in (None, 443) or any(c.isspace() for c in row["source_url"])):
            raise ValueError("Fonte da referência manual deve ser uma URL HTTPS válida.")
        date = datetime.fromisoformat(row["reviewed_at"].replace("Z", "+00:00"))
        if date.tzinfo is None or date.utcoffset() is None:
            raise ValueError("Data da referência manual deve conter fuso.")
        names = row["reference_models"]
        if (not isinstance(names, list) or not 1 <= len(names) <= 10
            or any(not isinstance(name, str) or not name.strip() for name in names)):
            raise ValueError("A referência manual deve identificar modelos canônicos.")
        keys = [(row["component_type"], normalize_name(name)) for name in names]
        if len(set(keys)) != len(keys) or any(key not in catalog for key in keys):
            raise ValueError("Modelo da referência manual repetido ou ausente no catálogo.")
        key = (row["id"], row["platform"], row["level"], row["component_type"])
        if key in result:
            raise ValueError("Referência manual repetida para o mesmo campo.")
        result[key] = row
    return result


def apply_curation(block: dict, appid: str, platform: str, level: str,
                   rules: dict, catalog: dict, aliases: dict) -> dict:
    """Preserva a extração original e aplica somente uma referência revisada."""
    result = deepcopy(block)
    for kind in ("CPU", "GPU"):
        rule = rules.get((appid, platform, level, kind))
        field = f"{kind.lower()}_score"
        if rule is None or result["requirements"].get(field) is not None:
            continue
        try:
            query = extract_hardware_text(result["text"], kind)
        except ValueError:
            query = None
        if query is None or normalize_name(query) != normalize_name(rule["expected_query"]):
            result["issues"].append(f"{kind}: texto mudou; referência manual precisa de revisão.")
            result["status"] = "needs_review"
            continue
        resolved = match_alternatives(" or ".join(rule["reference_models"]), kind,
                                      catalog, aliases, catalog_format="manual")
        if resolved["status"] != "resolved":
            result["issues"].append(f"{kind}: referência manual indisponível no catálogo atual.")
            result["status"] = "needs_review"
            continue
        result.setdefault("original_requirements", deepcopy(block["requirements"]))
        result.setdefault("original_issues", list(block["issues"]))
        result.setdefault("original_hardware", {})[kind] = deepcopy(block["hardware"].get(kind))
        result["hardware"][kind] = {**resolved, "query": query, "method": "manual_reference"}
        result["requirements"][field] = resolved["required_score"]
        result["issues"] = [issue for issue in result["issues"] if not issue.startswith(kind + ":")]
        result.setdefault("curation", []).append({
            "component_type": kind, "method": "manual_reference", "original_query": query,
            "reference_models": list(rule["reference_models"]), "source_url": rule["source_url"],
            "reviewed_at": rule["reviewed_at"], "notes": rule["notes"],
        })
    result["status"] = "needs_review" if result["issues"] else "resolved"
    return result


def validate_curated_block(block: dict, catalog: dict) -> None:
    """Confere que uma nota estimada continua ligada às referências preservadas."""
    items = block.get("curation", [])
    if not isinstance(items, list):
        raise ValueError("Curadoria processada inválida.")
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Curadoria processada inválida.")
        kind = item.get("component_type")
        names = item.get("reference_models")
        if (kind not in ("CPU", "GPU") or kind in seen or item.get("method") != "manual_reference"
            or not isinstance(names, list) or not names
            or any(not isinstance(name, str) for name in names)):
            raise ValueError("Referência manual processada inválida.")
        seen.add(kind)
        records = [catalog.get((kind, normalize_name(name))) for name in names]
        if any(not r or type(r.get("performance_score")) is not int
               or r["performance_score"] <= 0 or r.get("score_version") != MANUAL_SCORE_VERSION for r in records):
            raise ValueError("Referência manual processada sem classificação válida.")
        score = min(r["performance_score"] for r in records)
        if block["requirements"].get(f"{kind.lower()}_score") != score:
            raise ValueError("Nota estimada diverge dos modelos de referência.")
        if (not isinstance(item.get("original_query"), str)
            or extract_hardware_text(block["text"], kind) != item["original_query"]
            or not isinstance(block.get("original_requirements"), dict)
            or block["original_requirements"].get(f"{kind.lower()}_score") is not None):
            raise ValueError("Texto ou extração original da estimativa não foi preservado.")
