from datetime import datetime, timedelta
from typing import Dict

from aiohttp.web import Request, Response, HTTPForbidden, Application
from aiopg.sa.result import RowProxy
import jwt
from aiohttp_validate import validate
from aiopg.sa.connection import SAConnection


from .database import update_cache, get_from_cache, remove_from_cache
from .decorators import serialise_to_json, login_required
from .resources import get_auth, get_user, create_user, update_user
from .utils import get_token


@serialise_to_json(fields=['id', 'email', 'is_active', 'first_name', 'last_name', 'bio'])
@login_required
async def profile(request: Request):
    return await get_user(request.app['db'], request.match_info['user_id'])


@validate(
    request_schema={
        'type': 'object',
        'properties': {
            'email': {'type': 'string'},
            'password': {'type': 'string'},
            'first_name': {'type': 'string'},
            'last_name': {'type': 'string'},
            'bio': {'type': 'string'},
        },
        'required': ['email', 'password', 'first_name', 'last_name'],
        'additionalProperties': False
    }
)
async def registration(valid_data: dict, request: Request):

    @serialise_to_json(fields='__all__')
    async def get_new_user(conn: SAConnection, reg_data: dict) -> Response:
        user_id = await create_user(conn, reg_data)
        return await get_user(conn, user_id)

    return await get_new_user(request.app['db'], valid_data)


@validate(
    request_schema={
        'type': 'object',
        'properties': {
            'first_name': {'type': 'string'},
            'last_name': {'type': 'string'},
            'bio': {'type': 'string'},
        },
        'additionalProperties': False,
        'minProperties': 1
    }
)
@login_required
async def change_profile(valid_data: Dict[str, str], request: Request):

    @serialise_to_json(fields='__all__')
    async def get_changed_profile(conn: SAConnection, user_id: int) -> Response:
        return await get_user(conn, user_id)

    user_id = request.match_info['user_id']
    db = request.app['db']
    await update_user(db, user_id, valid_data)
    return await get_changed_profile(db, user_id)


@validate(
    request_schema={
        'type': 'object',
        'properties': {
            'email': {'type': 'string'},
            'password': {'type': 'string'},
        },
        'required': ['email', 'password'],
        'additionalProperties': False
    }
)
async def login(valid_data: Dict[str, str], request: Request) -> Response:
    refresh_token = ''

    @serialise_to_json(fields='__all__')
    async def get_access_token(app: Application, credentials: Dict[str, str]) -> Dict[str, str]:
        nonlocal refresh_token
        auth: RowProxy = await get_auth(app['db'], credentials)
        user_id = auth.user_id
        config = app['config']['jwt']
        access_token = get_token(
            payload={
                'user': user_id,
                'exp': datetime.utcnow() + timedelta(minutes=config.get('access_token_living_minutes')),
            },
            secret=config.get('secret'),
            algorithm=config.get('algorithm'))

        refresh_token_living_seconds = config.get('refresh_token_living_days') * 24 * 3600
        refresh_token = get_token(
            payload={'user': user_id},
            secret=config.get('secret'),
            algorithm=config.get('algorithm'))
        await update_cache(
            app['cache'],
            key=access_token,
            value=refresh_token,
            timeout=refresh_token_living_seconds)
        return dict(access_token=access_token)

    response: Response = await get_access_token(request.app, valid_data)
    response.set_cookie('sessionID', refresh_token, httponly=True)
    return response


@validate(
    request_schema={
        'type': 'object',
        'properties': {
            'token': {'type': 'string'},
        },
        'required': ['token'],
        'additionalProperties': False
    }
)
async def prolong(data: Dict[str, str], request: Request) -> Response:

    @serialise_to_json(fields='__all__')
    async def get_access_token(app: Application, session_id, access_token: str) -> Dict[str, str]:
        refresh_token = await get_from_cache(app['cache'], key=access_token)
        if isinstance(refresh_token, bytes):
            refresh_token = refresh_token.decode('utf8')
        if not refresh_token or session_id != refresh_token:
            raise HTTPForbidden(reason='Session has expired')

        config = app['config']['jwt']
        payload = jwt.decode(refresh_token, config.get('secret'), algorithm=config.get('algorithm'))
        new_access_token = get_token(
            payload={
                'user': payload.get('user'),
                'exp': datetime.utcnow() + timedelta(minutes=config.get('access_token_living_minutes')),
            },
            secret=config.get('secret'),
            algorithm=config.get('algorithm'))

        return dict(access_token=new_access_token)

    return get_access_token(request.app, request.cookies.get('sessionID'), data.get('token'))


@serialise_to_json(fields='__all__')
@login_required
async def logout(request: Request):
    access_token = request['token']
    await remove_from_cache(request.app['cache'], key=access_token)
    return dict(logout=True)
