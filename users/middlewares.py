import re
import jwt
from aiohttp import web, hdrs

request_property = ...


@web.middleware
async def jwt_middleware(request, handler):

    if request.method == hdrs.METH_OPTIONS:
        return await handler(request)

    global request_property
    conf = request.app['config']['jwt']
    request_property = conf.get('request_property')
    if 'Authorization' in request.headers:
        try:
            scheme, token = request.headers.get(
                'Authorization'
            ).strip().split(' ')
        except ValueError:
            raise web.HTTPForbidden(
                reason='Invalid authorization header',
            )

        if not re.match(conf.get('auth_scheme'), scheme):
            raise web.HTTPForbidden(reason='Invalid token scheme')

        if not token:
            raise web.HTTPUnauthorized(reason='Missing authorization token')
        else:
            if not isinstance(token, bytes):
                token = token.encode()
            try:
                payload = jwt.decode(token, conf.get('secret'), algorithms=[conf.get('algorithm')])
            except jwt.InvalidTokenError as exc:
                msg = 'Invalid authorization token, ' + str(exc)
                raise web.HTTPUnauthorized(reason=msg)
            except jwt.ExpiredSignatureError:
                raise web.HTTPForbidden(reason='Token is expired')
            request[request_property] = payload
            request['token'] = token

    elif request.get(request_property) is not None:
        request[request_property] = None

    return await handler(request)
