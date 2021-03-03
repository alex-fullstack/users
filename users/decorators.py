from functools import wraps
from typing import List, Callable, TypeVar, Union
from aiohttp.web import json_response, Response, View, BaseRequest, HTTPUnauthorized, HTTPForbidden
from aiopg.sa.engine import Engine

from users import middlewares
from users.database import get_from_cache
from users.errors import HttpError


def resource(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(db: Engine, *args, **kwargs):
        async with db.acquire() as conn:
            return await func(conn, *args, **kwargs)
    return wrapper


def serialise_to_json(*, fields: Union[str, List[str]] = '__all__') -> Callable:
    def json_result(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                keys = result.keys() if fields == '__all__' else fields
                data = {key: result[key] for key in keys}
                return json_response(status=200, data=data)
            except HttpError as e:
                return json_response(status=e.status, data={'message': str(e)})

        return wrapper
    return json_result


def login_required(func):
    @wraps(func)
    async def wrapped(*args, **kwargs):
        if middlewares.request_property is ...:
            raise RuntimeError('Incorrect usage of decorator.'
                               'Please initialize middleware first')
        request = args[-1]

        if isinstance(request, View):
            request = request.request

        if not isinstance(request, BaseRequest):  # pragma: no cover
            raise RuntimeError(
                'Incorrect usage of decorator.'
                'Expect web.BaseRequest as an argument')

        if not request.get(middlewares.request_property):
            raise HTTPUnauthorized(reason='Authorization required')

        session_id = (await get_from_cache(request.app['cache'], key=request['token']))
        if not session_id or session_id.decode('utf8') != request.cookies.get('sessionID'):
            raise HTTPForbidden(reason='Session has expired')

        return await func(*args, **kwargs)
    return wrapped
