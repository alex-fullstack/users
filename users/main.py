import logging
import sys

from aiohttp import web

from users.database import init_db, close_db, close_cache, init_cache
from users.middlewares import jwt_middleware
from users.routers import setup_routes
from users.settings import get_config


async def init_app(argv=None):
    app = web.Application(middlewares=[jwt_middleware])
    app['config'] = get_config(argv)

    app.on_startup.append(init_db)
    app.on_cleanup.append(close_db)

    app.on_startup.append(init_cache)
    app.on_cleanup.append(close_cache)

    setup_routes(app)

    return app


def main(argv):
    logging.basicConfig(level=logging.DEBUG)

    app = init_app(argv)

    config = get_config(argv)
    web.run_app(app, host=config['host'], port=config['port'])


if __name__ == '__main__':
    main(sys.argv[1:])
