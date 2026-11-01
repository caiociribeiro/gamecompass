"""Contrato de jogos reais: snapshots Steam, requisitos e tags editoriais."""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

from extract_steam_requirements import extract_snapshot, is_notes_only_requirement_text
from hardware_catalog import MANUAL_SCORE_VERSION, ROOT, read_catalog
from hardware_matcher import normalize_name, read_aliases
from process_requirements import process_requirements
from regex_parser import clean_html
from requirements_curation import apply_curation, read_curation, validate_curated_block

FORMAT = "steam_games_v1"
OWNER = "gamecompass_catalog_v1"
FIELDS = ("min_ram_gb", "min_cpu_score", "min_gpu_score", "rec_ram_gb", "rec_cpu_score", "rec_gpu_score")
PLATFORMS = {"windows": "Windows", "macos": "macOS", "linux": "Linux"}
EDITORIAL_GENRES = {"Plataforma", "Roguelike", "Tiro", "Puzzle"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_selection(path: Path) -> dict:
    selection = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(selection, dict) or selection.get("schema_version") != FORMAT:
        raise ValueError("Contrato da seleção de jogos inválido.")
    vocabulary = selection.get("tag_vocabulary")
    if (not isinstance(vocabulary, list) or not vocabulary
        or any(not isinstance(x, str) or not x.strip() or len(x) > 80 for x in vocabulary)
        or len(vocabulary) != len(set(vocabulary))):
        raise ValueError("Vocabulário de tags inválido.")
    rows = selection.get("games")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 250:
        raise ValueError("Seleção deve conter de 1 a 250 jogos.")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Registro de seleção inválido.")
        appid, tags = row.get("id"), row.get("tags")
        if not isinstance(appid, str) or not re.fullmatch(r"[1-9][0-9]{0,9}", appid) or appid in seen:
            raise ValueError("AppID inválido ou repetido na seleção.")
        if (not isinstance(tags, list) or any(not isinstance(x, str) or x not in vocabulary for x in tags)
            or len(tags) != len(set(tags)) or not isinstance(row.get("curation_notes"), str)
            or not row["curation_notes"].strip()):
            raise ValueError(f"Tags ou justificativa inválidas para {appid}.")
        genres = row.get("editorial_genres", [])
        if (not isinstance(genres, list) or any(not isinstance(x, str) or x not in EDITORIAL_GENRES for x in genres)
            or len(genres) != len(set(genres))
            or (genres and (not isinstance(row.get("genre_curation_notes"), str)
                            or not row["genre_curation_notes"].strip()))):
            raise ValueError(f"Categorias editoriais ou justificativa inválidas para {appid}.")
        seen.add(appid)
    return selection


def hardware_rows(catalog_path: Path) -> list[dict]:
    records = read_catalog(catalog_path, catalog_format="manual")
    return [{k: row[k] for k in ("component_type", "name", "performance_score", "score_version")} for row in records]


def hardware_digest(rows: list[dict]) -> str:
    ordered = sorted(rows, key=lambda row: (row["component_type"], row["name"]))
    return hashlib.sha256(json.dumps(ordered, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def build_catalog(snapshot_dir: Path, selection_path: Path, catalog_path: Path, aliases_path: Path,
                  curation_path: Path | None = None) -> dict:
    selection = read_selection(selection_path)
    records = read_catalog(catalog_path, catalog_format="manual")
    catalog = {(r["component_type"], normalize_name(r["name"])): r for r in records}
    aliases = read_aliases(aliases_path, catalog)
    curation_path = curation_path or ROOT / "data/catalog/requirements_curation.json"
    curation = read_curation(curation_path, catalog)
    games = []
    for row in selection["games"]:
        folder = snapshot_dir / row["id"]
        extracted = extract_snapshot(folder)
        raw = json.loads((folder / "appdetails.json").read_bytes())
        data = raw[row["id"]]["data"]
        metadata = json.loads((folder / "metadata.json").read_bytes())
        if extracted["id"] != row["id"] or data.get("type") != "game":
            raise ValueError(f"{row['id']}: a coleta não identifica um jogo base.")
        if metadata.get("country") != "br" or metadata.get("language") != "portuguese":
            raise ValueError("Use snapshots de jogos coletados em BR/português.")
        issues = list(extracted["issues"])
        platforms = {}
        for source_name, target_name in PLATFORMS.items():
            source = extracted["platforms"][source_name]
            target = {"native_support": source["native_support"]}
            for level in ("minimum", "recommended"):
                block = source[level]
                target[level] = None
                if block is not None:
                    processed = process_requirements(block["html"], catalog, aliases, catalog_format="manual")
                    processed = apply_curation(processed, row["id"], target_name, level, curation, catalog, aliases)
                    target[level] = {**processed, "os_text": block["os_text"]}
                    if is_notes_only_requirement_text(block["text"]):
                        target[level]["requirements_kind"] = "notes_only"
                    else:
                        issues.extend(f"{target_name}.{level}: {issue}" for issue in processed["issues"])
            platforms[target_name] = target
        price = data.get("price_overview")
        amount = None
        if data.get("is_free") is True:
            amount = 0.0
        elif isinstance(price, dict) and price.get("currency") == "BRL" and type(price.get("final")) is int and price["final"] >= 0:
            amount = price["final"] / 100.0
        if amount is None:
            issues.append("Preço em BRL não disponível nesta coleta.")
        descriptions = data.get("genres")
        genres = sorted({x["description"].strip() for x in descriptions
            if isinstance(x, dict) and isinstance(x.get("description"), str) and x["description"].strip()}) if isinstance(descriptions, list) else []
        if not genres:
            issues.append("Gêneros não informados pela Steam.")
        steam_genres = genres
        editorial_genres = row.get("editorial_genres", [])
        genres = sorted(set(steam_genres) | set(editorial_genres))
        developers = data.get("developers")
        date = data.get("release_date")
        year = re.search(r"\b(?:19|20)[0-9]{2}\b", str(date.get("date", ""))) if isinstance(date, dict) else None
        image = data.get("header_image")
        parsed = urlsplit(image) if isinstance(image, str) else None
        image = image if parsed and parsed.scheme == "https" and parsed.hostname and parsed.hostname.endswith((".steamstatic.com", ".steamcdn-a.akamaihd.net")) else None
        game = {
            "id": row["id"], "title": extracted["title"], "price": amount,
            "price_text": "Gratuito" if data.get("is_free") is True else price.get("final_formatted") if isinstance(price, dict) else None,
            "developer": ", ".join(x for x in developers if isinstance(x, str)) if isinstance(developers, list) else "",
            "year": int(year[0]) if year else None,
            "genres": genres, "themes": row["tags"], "themes_status": "classified",
            "genre_source": {"steam": steam_genres, "editorial": editorial_genres,
                "method": "gamecompass_genres_v1", "notes": row.get("genre_curation_notes", ""),
                "source_url": f"https://store.steampowered.com/app/{row['id']}/"},
            "summary": clean_html(data.get("short_description", "")) if isinstance(data.get("short_description"), str) else "",
            "image_url": image, "store_url": f"https://store.steampowered.com/app/{row['id']}/",
            "platforms": platforms, "source": extracted["source"],
            "tag_source": {"method": "gamecompass_editorial_v1", "source_url": f"https://store.steampowered.com/app/{row['id']}/", "notes": row["curation_notes"]},
            "issues": issues, "status": "needs_review" if issues else "resolved",
        }
        for level, prefix in (("minimum", "min"), ("recommended", "rec")):
            block = platforms["Windows"][level]
            req = block["requirements"] if block else {}
            game.update({f"{prefix}_{field}": req.get(field) for field in ("ram_gb", "cpu_score", "gpu_score")})
        games.append(game)
    hardware = hardware_rows(catalog_path)
    result = {"schema_version": FORMAT, "score_version": MANUAL_SCORE_VERSION, "currency": "BRL",
        "processed_at": datetime.now(timezone.utc).isoformat(), "catalog_sha256": sha256(catalog_path),
        "aliases_sha256": sha256(aliases_path), "selection_sha256": sha256(selection_path),
        "curation_sha256": sha256(curation_path),
        "hardware": hardware, "hardware_sha256": hardware_digest(hardware), "games": games}
    validate_catalog(result)
    return result


def validate_catalog(data: dict) -> None:
    if (not isinstance(data, dict) or data.get("schema_version") != FORMAT
        or data.get("score_version") != MANUAL_SCORE_VERSION or data.get("currency") != "BRL"):
        raise ValueError("Formato do catálogo processado inválido.")
    for key in ("catalog_sha256", "aliases_sha256", "selection_sha256", "hardware_sha256"):
        if not isinstance(data.get(key), str) or not re.fullmatch(r"[a-f0-9]{64}", data[key]):
            raise ValueError(f"Hash inválido: {key}.")
    rows = data.get("hardware")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Referência de hardware ausente.")
    seen_hardware = set()
    for row in rows:
        if (not isinstance(row, dict) or row.get("component_type") not in ("CPU", "GPU")
            or not isinstance(row.get("name"), str) or not row["name"].strip()
            or row.get("score_version") != MANUAL_SCORE_VERSION
            or (row.get("performance_score") is not None and (type(row["performance_score"]) is not int or not 0 < row["performance_score"] < 2**63))):
            raise ValueError("Referência de hardware inválida.")
        key = (row["component_type"], normalize_name(row["name"]))
        if key in seen_hardware:
            raise ValueError("Hardware repetido.")
        seen_hardware.add(key)
    if hardware_digest(rows) != data["hardware_sha256"]:
        raise ValueError("Hash do hardware divergente.")
    if "curation_sha256" in data and (not isinstance(data["curation_sha256"], str)
        or not re.fullmatch(r"[a-f0-9]{64}", data["curation_sha256"])):
        raise ValueError("Hash da curadoria inválido.")
    hardware_index = {(r["component_type"], normalize_name(r["name"])): r for r in rows}
    games = data.get("games")
    if not isinstance(games, list) or not 1 <= len(games) <= 250:
        raise ValueError("Catálogo deve conter de 1 a 250 jogos.")
    seen = set()
    for game in games:
        if not isinstance(game, dict) or not isinstance(game.get("id"), str) or not re.fullmatch(r"[1-9][0-9]{0,9}", game["id"]) or game["id"] in seen:
            raise ValueError("Jogo inválido ou repetido.")
        seen.add(game["id"])
        if not isinstance(game.get("title"), str) or not game["title"].strip():
            raise ValueError("Título inválido.")
        if game.get("price") is not None and (type(game["price"]) not in (float, int) or not math.isfinite(game["price"]) or game["price"] < 0):
            raise ValueError("Preço inválido.")
        for field in FIELDS:
            value = game.get(field)
            if field not in game or (value is not None and (type(value) is not int or not 0 < value < 2**63)):
                raise ValueError(f"Requisito inválido: {field}.")
        for field in ("genres", "themes"):
            names = game.get(field)
            if (not isinstance(names, list) or any(not isinstance(x, str) or not x.strip() or len(x) > 100 for x in names)
                or len(names) != len(set(names))):
                raise ValueError(f"Classificação inválida: {field}.")
        genre_source = game.get("genre_source")
        if genre_source is not None:
            if (not isinstance(genre_source, dict) or genre_source.get("method") != "gamecompass_genres_v1"
                or any(not isinstance(genre_source.get(key), list) or
                       any(not isinstance(name, str) or not name.strip() for name in genre_source[key])
                       for key in ("steam", "editorial"))
                or any(name not in EDITORIAL_GENRES for name in genre_source["editorial"])
                or set(game["genres"]) != set(genre_source["steam"]) | set(genre_source["editorial"])
                or (genre_source["editorial"] and (not isinstance(genre_source.get("notes"), str)
                                                 or not genre_source["notes"].strip()))):
                raise ValueError("Origem das categorias editoriais divergente dos gêneros.")
        if game.get("themes_status") != "classified" or not isinstance(game.get("platforms"), dict) or set(game["platforms"]) != set(PLATFORMS.values()):
            raise ValueError("Plataformas ou curadoria inválidas.")
        source = game.get("source")
        if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) for key in ("source_url", "collected_at", "response_sha256"))
            or not source["source_url"].startswith("https://store.steampowered.com/")
            or not re.fullmatch(r"[a-f0-9]{64}", source["response_sha256"])):
            raise ValueError("Origem do jogo inválida.")
        collected = datetime.fromisoformat(source["collected_at"].replace("Z", "+00:00"))
        if collected.tzinfo is None or collected.utcoffset() is None:
            raise ValueError("Data de coleta sem fuso.")
        for platform in game["platforms"].values():
            if not isinstance(platform, dict) or (platform.get("native_support") is not None and type(platform["native_support"]) is not bool):
                raise ValueError("Suporte nativo inválido.")
            for level in ("minimum", "recommended"):
                block = platform.get(level)
                if block is not None and (not isinstance(block, dict) or not isinstance(block.get("text"), str)
                    or not isinstance(block.get("requirements"), dict) or block.get("score_version") != MANUAL_SCORE_VERSION):
                    raise ValueError("Bloco de requisitos inválido.")
                if block is not None:
                    kind = block.get("requirements_kind")
                    if kind is not None and kind not in ("hardware", "notes_only"):
                        raise ValueError("Tipo de bloco de requisitos inválido.")
                    mapping = block.get("hardware", {})
                    if kind == "notes_only" and (
                        not is_notes_only_requirement_text(block["text"])
                        or block.get("os_text") is not None
                        or any(value is not None for value in block["requirements"].values())
                        or not isinstance(mapping, dict)
                        or any(value is not None for value in mapping.values())
                    ):
                        raise ValueError("Bloco marcado como observações contém requisitos de hardware.")
                    validate_curated_block(block, hardware_index)
                    for field in ("ram_gb", "cpu_score", "gpu_score"):
                        value = block["requirements"].get(field)
                        if field not in block["requirements"] or (value is not None and (type(value) is not int or not 0 < value < 2**63)):
                            raise ValueError("Pontuação ou memória inválida no bloco.")
        for level, prefix in (("minimum", "min"), ("recommended", "rec")):
            block = game["platforms"]["Windows"].get(level)
            values = block["requirements"] if block else {}
            if any(game[f"{prefix}_{field}"] != values.get(field) for field in ("ram_gb", "cpu_score", "gpu_score")):
                raise ValueError("Campos planos divergem dos requisitos Windows.")
