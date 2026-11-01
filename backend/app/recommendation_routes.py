"""Cálculo autoritativo de recomendações e comparação de um jogo."""

from fastapi import APIRouter, HTTPException, Request
from neo4j.exceptions import DriverError, Neo4jError

from .core.config import settings
from .catalog_routes import context_or_pending, game_collection, discover_collection, load_game
from .schemas.recommendations import ComparisonInput, RecommendationInput, SteamID
from .services.hardware import read_hardware, matching_context, MANUAL_SCORE_VERSION
from .services.recommendation_engine import ENGINE_VERSION, MIN_AFFINITY, build_recommendations, describe_match

router = APIRouter(prefix='/api', tags=['Recomendações'])


def calculation_context(request, profile):
    if profile.hardware is None:
        context = context_or_pending(request)
        hardware = {'CPU': [], 'GPU': []}
        return hardware, context
    try:
        hardware = read_hardware(request.app.state.neo4j_driver, settings.neo4j_database)
        context = matching_context(hardware)
    except (DriverError, Neo4jError, OSError, ValueError) as exc:
        raise HTTPException(503, 'Não foi possível consultar o hardware para calcular a comparação.') from exc
    for kind, identifier in [('CPU', profile.hardware.cpuId), ('GPU', profile.hardware.gpuId)]:
        if not any(part['id'] == identifier for part in hardware[kind]):
            raise HTTPException(422, f'A peça de {kind} não está mais no catálogo. Selecione novamente seu hardware.')
    return hardware, context


def selected_anchors(request, profile, context):
    if not profile.anchorIds:
        return [], []
    result = game_collection(request, profile.anchorIds, context=context)
    actual = {game['id'] for game in result['items']}
    if any(identifier not in actual for identifier in profile.anchorIds):
        raise HTTPException(503, 'Não foi possível consultar todos os jogos âncora. Tente novamente.')
    return result['items'], result['issues']


def calculation_metadata(context):
    return {'engine_version': ENGINE_VERSION, 'minimum_affinity': MIN_AFFINITY,
        'score_version': MANUAL_SCORE_VERSION,
        'hardware_sha256': context['hardware_sha256'] if context else None,
        'curation_sha256': context['curation_sha256'] if context else None}


@router.post('/recommendations')
def recommendations(profile: RecommendationInput, request: Request):
    hardware, context = calculation_context(request, profile)
    anchors, issues = selected_anchors(request, profile, context)
    candidates = discover_collection(request, profile.anchorIds, profile.genres, profile.themes, context=context)
    # O grafo/Steam resolve o conteúdo. Dados de jogos e scores não vêm do corpo HTTP.
    by_id = {game['id']: game for game in candidates['items']}
    by_id.update({game['id']: game for game in anchors})
    result = build_recommendations(profile.model_dump(), list(by_id.values()), hardware)
    return {**result, 'anchors': anchors, 'issues': [*issues, *candidates['issues']],
        'source': candidates.get('source', 'steam'), 'calculation': calculation_metadata(context)}


@router.post('/games/{appid}/comparison')
def comparison(appid: SteamID, profile: ComparisonInput, request: Request):
    hardware, context = calculation_context(request, profile)
    anchors, issues = selected_anchors(request, profile, context)
    game = load_game(request, appid, context=context)
    games = list({item['id']: item for item in [*anchors, game]}.values())
    return {'match': describe_match(profile.model_dump(), game, games, hardware),
            'issues': issues, 'calculation': calculation_metadata(context)}
