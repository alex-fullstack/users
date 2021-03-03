import pytest
import aiopg.sa
from aioredis import create_pool, pool


@pytest.fixture
def postgres(request, loop, pg_params):
    async def init_postgres(conf, loop):
        engine = await aiopg.sa.create_engine(
            database=conf['database'],
            user=conf['user'],
            password=conf['password'],
            host=conf['host'],
            port=conf['port'],
            minsize=1,
            maxsize=2,
            loop=loop)
        return engine
    engine = loop.run_until_complete(init_postgres(pg_params, loop))

    def fin():
        engine.close()
        loop.run_until_complete(engine.wait_closed())
    request.addfinalizer(fin)
    return engine


@pytest.fixture
def redis(request, loop, redis_address):
    async def init_redis(loop, address):
        pool = await create_pool(
            address,
            minsize=5,
            maxsize=10,
            loop=loop)
        return pool
    pool = loop.run_until_complete(init_redis(loop, redis_address['address']))

    def fin():
        pool.close()
        loop.run_until_complete(pool.wait_closed())
    request.addfinalizer(fin)
    return pool
