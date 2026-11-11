"""Visualizações e reações (curtir/não curtir) do usuário da sessão em jogos do catálogo."""

import time

from fastapi import APIRouter, Depends, HTTPException, Request

from .auth_routes import authenticated, database, same_origin, store_of
from .schemas.auth import ReactionInput
from .schemas.recommendations import SteamID

router = APIRouter(prefix='/api/me', tags=['Interações'], dependencies=[Depends(same_origin)])
NOT_IN_CATALOG = 'Esse jogo não está no catálogo do GameCompass.'


@router.get('/interactions')
def interactions(request: Request):
    user, _ = authenticated(request)
    return {'items': database(lambda: store_of(request).list_interactions(user['id']))}


@router.post('/games/{appid}/view')
def view(appid: SteamID, request: Request):
    user, _ = authenticated(request)
    found = database(lambda: store_of(request).record_view(user_id=user['id'], game_id=appid, now=int(time.time())))
    if found is None:
        raise HTTPException(404, NOT_IN_CATALOG)
    return found


@router.put('/games/{appid}/reaction')
def reaction(appid: SteamID, payload: ReactionInput, request: Request):
    user, _ = authenticated(request)
    found = database(lambda: store_of(request).set_reaction(
        user_id=user['id'], game_id=appid, reaction=payload.reaction, now=int(time.time())))
    if found is None:
        raise HTTPException(404, NOT_IN_CATALOG)
    return found


@router.delete('/interactions')
def clear(request: Request):
    user, _ = authenticated(request)
    return {'removed': database(lambda: store_of(request).clear_interactions(user['id']))}
