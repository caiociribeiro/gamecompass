"""Cadastro, sessão e perfil do usuário. Toda rota de perfil usa só a sessão do cookie."""

import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from neo4j.exceptions import DriverError, Neo4jError

from .core.config import settings
from .schemas.auth import LoginInput, PasswordChangeInput, ProfilePatch, RegisterInput
from .services.auth import AttemptLimiter, hash_password, new_token, token_digest, verify_password
from .services.users import EmailTaken, UserStore, account_from

COOKIE = 'gc_session'
SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS'}
UNAVAILABLE = 'Não foi possível acessar as contas no Neo4j. Tente novamente em alguns instantes.'
limiter = AttemptLimiter()


def same_origin(request: Request):
    """Bloqueia escrita vinda de outro site; o cookie já é SameSite=Lax."""
    if request.method in SAFE_METHODS:
        return
    origin = request.headers.get('origin')
    if origin is None:
        return
    host = request.headers.get('host', '')
    allowed = {*settings.allowed_origins, f'{request.url.scheme}://{host}'}
    if origin.rstrip('/') not in allowed:
        raise HTTPException(403, 'Origem não autorizada para esta operação.')


router = APIRouter(prefix='/api', tags=['Conta'], dependencies=[Depends(same_origin)])


def store_of(request: Request) -> UserStore:
    return request.app.state.user_store


def database(call):
    try:
        return call()
    except (DriverError, Neo4jError, OSError) as exc:
        raise HTTPException(503, UNAVAILABLE) from exc


def start_session(request: Request, response: Response, user: dict) -> None:
    token = new_token()
    now = int(time.time())
    lifetime = settings.session_days * 86400
    database(lambda: store_of(request).create_session(
        user_id=user['id'], token_hash=token_digest(token), now=now, expires_at=now + lifetime))
    response.set_cookie(COOKIE, token, max_age=lifetime, httponly=True, samesite='lax',
                        secure=settings.session_cookie_secure, path='/')


def authenticated(request: Request) -> tuple[dict, str]:
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401, 'Entre na sua conta para continuar.')
    digest = token_digest(token)
    user = database(lambda: store_of(request).user_for_session(digest, int(time.time())))
    if user is None:
        raise HTTPException(401, 'Sessão expirada. Entre novamente.')
    return user, digest


def optional_user(request: Request) -> dict | None:
    """Conta da sessão, ou None sem sessão válida. Falha do banco continua sendo erro 503."""
    try:
        return authenticated(request)[0]
    except HTTPException as exc:
        if exc.status_code == 401:
            return None
        raise


def client_key(request: Request, scope: str) -> str:
    return f'{scope}:{request.client.host if request.client else "?"}'


@router.post('/auth/register', status_code=201)
def register(payload: RegisterInput, request: Request, response: Response):
    password_hash = hash_password(payload.password)
    try:
        user = database(lambda: store_of(request).create_user(
            name=payload.name, email=payload.email, password_hash=password_hash, now=int(time.time())))
    except EmailTaken:
        raise HTTPException(409, 'Já existe uma conta com esse e-mail.')
    start_session(request, response, user)
    return account_from(user)


@router.post('/auth/login')
def login(payload: LoginInput, request: Request, response: Response):
    store = store_of(request)
    key = f'{client_key(request, "login")}:{payload.email}'
    if database(lambda: limiter.blocked(store, key)):
        raise HTTPException(429, 'Muitas tentativas de entrada. Aguarde alguns minutos.')
    user = database(lambda: store.find_by_email(payload.email))
    valid = verify_password(user['password_hash'] if user else None, payload.password)
    if not user or not valid:
        database(lambda: limiter.fail(store, key))
        raise HTTPException(401, 'E-mail ou senha não conferem.')
    database(lambda: limiter.reset(store, key))
    start_session(request, response, user)
    return account_from(user)


@router.post('/auth/logout')
def logout(request: Request, response: Response):
    token = request.cookies.get(COOKIE)
    if token:
        database(lambda: store_of(request).delete_session(token_digest(token)))
    response.delete_cookie(COOKIE, path='/', httponly=True, samesite='lax', secure=settings.session_cookie_secure)
    return {'status': 'ok'}


@router.get('/auth/me')
def me(request: Request):
    user, _ = authenticated(request)
    return account_from(user)


@router.get('/me/account')
def account_details(request: Request):
    """Dados de contato da conta, pedidos só pela tela de Conta."""
    user, _ = authenticated(request)
    return {'email': user['email']}


@router.post('/auth/password')
def change_password(payload: PasswordChangeInput, request: Request):
    user, digest = authenticated(request)
    store = store_of(request)
    key = client_key(request, f'password:{user["id"]}')
    if database(lambda: limiter.blocked(store, key)):
        raise HTTPException(429, 'Muitas tentativas. Aguarde alguns minutos.')
    if not verify_password(user['password_hash'], payload.current):
        database(lambda: limiter.fail(store, key))
        raise HTTPException(400, 'A senha atual não confere.')
    database(lambda: limiter.reset(store, key))
    new_hash = hash_password(payload.next)
    database(lambda: store_of(request).set_password(
        user_id=user['id'], password_hash=new_hash, keep_token_hash=digest, now=int(time.time())))
    return {'status': 'ok'}


@router.patch('/me/profile')
def update_profile(payload: ProfilePatch, request: Request):
    user, _ = authenticated(request)
    changes = {field: getattr(payload, field) for field in payload.model_fields_set}
    if 'hardware' in changes and payload.hardware is not None:
        changes['hardware'] = payload.hardware.model_dump(exclude_none=True)
    if not changes:
        return account_from(user)
    updated = database(lambda: store_of(request).update_profile(user_id=user['id'], changes=changes, now=int(time.time())))
    if updated is None:
        raise HTTPException(401, 'Sessão expirada. Entre novamente.')
    return account_from(updated)
