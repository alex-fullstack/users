import pytest
from aiohttp import web

from users.middlewares import jwt_middleware
from users.routers import setup_routes
from users.settings import get_config


@pytest.fixture
async def client(aiohttp_client, init_app):
    app = init_app()
    return await aiohttp_client(app)


@pytest.fixture
def init_app(postgres, redis):
    app = web.Application(middlewares=[jwt_middleware])
    app['config'] = get_config()
    app['db'] = postgres
    app['cache'] = redis
    setup_routes(app)

    return app
