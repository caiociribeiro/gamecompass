"""Rotas de leitura para o frontend conectado."""

import json
import re
from fastapi import APIRouter, HTTPException, Query, Request
from neo4j.exceptions import DriverError, Neo4jError

from .core.config import settings
from .services.hardware import ROOT, read_hardware, matching_context
from .services.steam import SteamError, game_preview, normalize_game
from .services.game_graph import read_graph_games, refresh_requirements

router = APIRouter(prefix="/api", tags=["Catálogo"])


@router.get("/hardware")
def hardware(request: Request):
    try:
        return read_hardware(request.app.state.neo4j_driver, settings.neo4j_database)
    except (DriverError, Neo4jError, OSError, ValueError) as exc:
        raise HTTPException(503, "Não foi possível consultar o catálogo de hardware no Neo4j.") from exc


def context_or_pending(request):
    try:
        return matching_context(read_hardware(request.app.state.neo4j_driver, settings.neo4j_database))
    except (DriverError, Neo4jError, OSError, ValueError):
        return None


@router.get("/games")
def games(request: Request, appids: str = ""):
    identifiers = appids.split(",") if appids else []
    if len(identifiers) > 30 or any(not re.fullmatch(r"[1-9][0-9]{0,9}", appid) for appid in identifiers):
        raise HTTPException(422, "Informe até trinta identificadores válidos.")
    if not identifiers:
        return {"items": [], "issues": [], "source": "steam", "hardware_available": None}
    return game_collection(request, list(dict.fromkeys(identifiers)))


def game_collection(request, appids):
    context = context_or_pending(request)
    try:
        stored = []
        issues = []
        try:
            stored = read_graph_games(request.app.state.neo4j_driver, settings.neo4j_database, ids=appids)
        except (DriverError, Neo4jError, OSError, ValueError):
            issues.append({"appid": "", "message": "Catálogo de jogos indisponível no Neo4j; consulta direta à Steam."})
        by_id = {game["id"]: refresh_requirements(game, context) for game in stored}
        missing = [appid for appid in appids if appid not in by_id]
        snapshots, steam_issues = request.app.state.steam_client.get_many(missing) if missing else ([], [])
        issues.extend(steam_issues)
        by_id.update({str(snapshot.data["steam_appid"]): normalize_game(snapshot, context) for snapshot in snapshots})
        if not by_id:
            raise HTTPException(503, "A Steam não retornou jogos. Tente novamente em alguns instantes.")
        source = "mixed" if stored and snapshots else "neo4j" if stored else "steam"
        return {"items": [by_id[appid] for appid in appids if appid in by_id],
                "issues": issues, "source": source, "hardware_available": context is not None}
    except SteamError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc


@router.get("/games/search")
def search_games(request: Request, q: str = Query(min_length=2, max_length=100)):
    try:
        return request.app.state.steam_client.search(q)
    except SteamError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc


@router.get("/games/anchors")
def anchor_suggestions(request: Request):
    """Seleção editorial de nomes e capas; não seleciona âncoras nem lê hardware."""
    try:
        selection = json.loads((ROOT / "data/catalog/anchor_suggestions.json").read_text(encoding="utf-8"))
        appids = selection.get("appids") if isinstance(selection, dict) else None
        if (not isinstance(appids, list) or not 1 <= len(appids) <= 12
            or any(not isinstance(appid, str) or not re.fullmatch(r"[1-9][0-9]{0,9}", appid) for appid in appids)
            or len(set(appids)) != len(appids)):
            raise ValueError("Seleção de jogos inválida.")
    except (OSError, ValueError, UnicodeError) as exc:
        raise HTTPException(503, "As sugestões de âncoras estão indisponíveis. Use a busca pelo nome.") from exc
    try:
        snapshots, issues = request.app.state.steam_client.get_many(appids)
        if not snapshots:
            raise HTTPException(503, "Não foi possível carregar as sugestões da Steam. Tente novamente.")
        return {"items": [{**game_preview(snapshot), "source": snapshot.source} for snapshot in snapshots],
                "issues": issues, "source": "steam", "selection": "editorial"}
    except SteamError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc


def named_filters(value):
    if not value:
        return []
    parts = [part.strip() for part in value.split(",")]
    if len(parts) > 20 or any(not part or len(part) > 80 for part in parts):
        raise HTTPException(422, "Filtros de gênero ou temática inválidos.")
    return list(dict.fromkeys(parts))


@router.get("/games/discover")
def discover_games(request: Request, anchor_ids: str = Query(default="", max_length=40),
    genres: str = Query(default="", max_length=1600), tags: str = Query(default="", max_length=1600)):
    anchors = anchor_ids.split(",") if anchor_ids else []
    if len(anchors) > 3 or any(not re.fullmatch(r"[1-9][0-9]{0,9}", appid) for appid in anchors):
        raise HTTPException(422, "Informe até três âncoras válidas.")
    genre_names, tag_names = named_filters(genres), named_filters(tags)
    graph_issue = None
    try:
        stored = read_graph_games(request.app.state.neo4j_driver, settings.neo4j_database,
            anchors=anchors, genres=genre_names, tags=tag_names, related=bool(anchors or genre_names or tag_names))
        if stored:
            context = context_or_pending(request)
            return {"items": [refresh_requirements(game, context) for game in stored], "issues": [],
                "source": "neo4j", "hardware_available": context is not None,
                "candidate_source": {"type": "neo4j", "relationships": ["HAS_GENRE", "HAS_TAG"]}}
        graph_issue = "Não há jogos relacionados catalogados; usando candidatos da Steam."
    except (DriverError, Neo4jError, OSError, ValueError):
        graph_issue = "Catálogo de jogos indisponível no Neo4j; usando candidatos da Steam."
    try:
        featured = request.app.state.steam_client.featured()
        if not featured["appids"]:
            return {"items": [], "issues": [], "source": "steam", "hardware_available": None}
        result = game_collection(request, featured["appids"])
        result["candidate_source"] = featured["source"]
        result["issues"].append({"appid": "", "message": graph_issue})
        return result
    except SteamError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc


@router.get("/games/{appid}")
def game(appid: str, request: Request):
    if not re.fullmatch(r"[1-9][0-9]{0,9}", appid):
        raise HTTPException(422, "Identificador de jogo inválido.")
    try:
        try:
            stored = read_graph_games(request.app.state.neo4j_driver, settings.neo4j_database, ids=[appid])
        except (DriverError, Neo4jError, OSError, ValueError):
            stored = []
        if stored:
            return refresh_requirements(stored[0], context_or_pending(request))
        snapshot = request.app.state.steam_client.get(appid)
        return normalize_game(snapshot, context_or_pending(request))
    except SteamError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
