"""Lê somente o índice manual carregado no Neo4j, sem escrever no grafo."""

import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(os.getenv("GAMECOMPASS_ROOT", Path(__file__).resolve().parents[3]))
PIPELINE = ROOT / "scripts"
if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))

from hardware_catalog import MANUAL_SCORE_VERSION, read_catalog
from hardware_matcher import normalize_name, read_aliases
from process_requirements import process_requirements
from regex_parser import clean_html
from extract_steam_requirements import extract_os_text


QUERY = """
CALL () {
    MATCH (h:CPU) WHERE h.score_version = $version
    RETURN 'CPU' AS component_type, h.name AS name,
           h.performance_score AS performance_score, h.score_version AS score_version
    UNION ALL
    MATCH (h:GPU) WHERE h.score_version = $version
    RETURN 'GPU' AS component_type, h.name AS name,
           h.performance_score AS performance_score, h.score_version AS score_version
}
RETURN component_type, name, performance_score, score_version
ORDER BY component_type, name
"""


def read_hardware(driver, database: str) -> dict:
    def query(tx):
        return tx.run(QUERY, version=MANUAL_SCORE_VERSION).data()

    with driver.session(database=database, default_access_mode="READ") as session:
        rows = session.execute_read(query)

    result = {"CPU": [], "GPU": [], "score_version": MANUAL_SCORE_VERSION, "source": "neo4j"}
    seen = set()
    for row in rows:
        kind, name, score = row["component_type"], row["name"], row["performance_score"]
        if (
            kind not in ("CPU", "GPU") or not isinstance(name, str) or not name.strip()
            or row["score_version"] != MANUAL_SCORE_VERSION
            or (score is not None and (type(score) is not int or score <= 0))
        ):
            raise ValueError("O catálogo manual no Neo4j contém um registro inválido.")
        key = (kind, normalize_name(name))
        if key in seen:
            raise ValueError("Há nomes duplicados após a normalização do catálogo.")
        seen.add(key)
        vendor = next((v for v in ("Intel", "AMD", "NVIDIA") if name.startswith(v + " ")), "Outro")
        result[kind].append({
            "id": name, "name": name, "vendor": vendor,
            "performance_score": score, "score_version": row["score_version"],
        })
    return result


def matching_context(hardware: dict) -> dict:
    """Usa as notas do banco; os arquivos versionados validam apenas aliases."""
    catalog_path = ROOT / "data/catalog/hardware_manual_v1.csv"
    aliases_path = ROOT / "data/catalog/hardware_aliases.json"
    records = read_catalog(catalog_path, catalog_format="manual")
    identities = {(r["component_type"], normalize_name(r["name"])): r for r in records}
    aliases = read_aliases(aliases_path, identities)
    catalog = {
        (kind, normalize_name(part["name"])): {**part, "component_type": kind}
        for kind in ("CPU", "GPU") for part in hardware[kind]
    }
    # Uma identidade ainda não carregada permanece desconhecida no banco.
    aliases = {key: target for key, target in aliases.items() if target in catalog}
    return {
        "catalog": catalog, "aliases": aliases,
        "catalog_sha256": hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
        "aliases_sha256": hashlib.sha256(aliases_path.read_bytes()).hexdigest(),
        "hardware_sha256": hashlib.sha256(json.dumps(hardware, sort_keys=True).encode()).hexdigest(),
    }


def requirements_block(html: object, context: dict | None) -> dict | None:
    if not isinstance(html, str) or not html.strip():
        return None
    text = clean_html(html)
    if not text or all(line.lower().strip(": ") in ("minimum", "recommended", "mínimos", "recomendados") for line in text.splitlines()):
        return None
    if context is None:
        result = process_requirements(html, {}, {}, catalog_format="manual")
        result["issues"].append("Catálogo de hardware indisponível para esta consulta.")
        result["status"] = "needs_review"
    else:
        result = process_requirements(html, context["catalog"], context["aliases"], catalog_format="manual")
    try:
        os_text = extract_os_text(text)
    except ValueError as exc:
        os_text = None
        result["issues"].append(str(exc))
        result["status"] = "needs_review"
    # O texto será exibido como texto React, sem injetar HTML da Steam.
    return {"text": text, "os_text": os_text, "status": result["status"],
            "requirements": result["requirements"], "issues": result["issues"],
            "hardware": result["hardware"], "score_version": MANUAL_SCORE_VERSION}
