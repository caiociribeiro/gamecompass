"""Rotas de leitura para o frontend conectado."""

import re
from fastapi import APIRouter, HTTPException, Request
from neo4j.exceptions import DriverError, Neo4jError

from .core.config import settings
from .services.hardware import read_hardware, matching_context
from .services.steam import SteamError, normalize_game, selection

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
def games(request: Request, extra_appids: str = ""):
    extra = extra_appids.split(",") if extra_appids else []
    if len(extra) > 3 or any(not re.fullmatch(r"[1-9][0-9]{0,9}", appid) for appid in extra):
        raise HTTPException(422, "Informe até três AppIDs extras válidos.")
    try:
        appids = list(dict.fromkeys([*extra, *selection()]))[:30]
    except (OSError, ValueError) as exc:
        raise HTTPException(503, "A seleção de jogos não está disponível.") from exc
    context = context_or_pending(request)
    try:
        snapshots, issues = request.app.state.steam_client.get_many(appids)
        if not snapshots:
            raise HTTPException(503, "A Steam não retornou jogos. Tente novamente em alguns instantes.")
        return {"items": [normalize_game(snapshot, context) for snapshot in snapshots],
                "issues": issues, "source": "steam", "hardware_available": context is not None}
    except SteamError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc


@router.get("/games/{appid}")
def game(appid: str, request: Request):
    try:
        snapshot = request.app.state.steam_client.get(appid)
        return normalize_game(snapshot, context_or_pending(request))
    except SteamError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
