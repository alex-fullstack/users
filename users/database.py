import aiopg.sa
from aioredis import create_pool, pool


async def init_db(app) -> None:
    conf = app['config']['postgres']
    engine = await aiopg.sa.create_engine(
        database=conf['database'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        minsize=conf['minsize'],
        maxsize=conf['maxsize'],
    )
    app['db'] = engine


async def close_db(app) -> None:
    app['db'].close()
    await app['db'].wait_closed()


async def init_cache(app) -> None:
    pool = await create_pool(
        'redis://localhost',
        minsize=5, maxsize=10)
    app['cache'] = pool


async def close_cache(app) -> None:
    app['cache'].close()
    await app['cache'].wait_closed()


async def update_cache(pool: pool.ConnectionsPool, *, key: str, value: str, timeout: int) -> None:
    with await pool as conn:
        await conn.execute('set', key, value)
        await conn.execute('expire', key, timeout)


async def remove_from_cache(pool: pool.ConnectionsPool, *, key: str) -> None:
    with await pool as conn:
        await conn.execute('del', key)


async def get_from_cache(pool: pool.ConnectionsPool, *, key: str) -> str:
    with await pool as conn:
        value = await conn.execute('get', key)
    return value
