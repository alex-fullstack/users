import time

import pytest
import psycopg2
import redis
from pathlib import Path
from docker import APIClient
from alembic.command import upgrade as alembic_upgrade
from alembic.config import Config as AlembicConfig

TEMP_FOLDER = Path('/tmp') / 'users'


def pytest_addoption(parser):
    parser.addoption("--no-pull", action="store_true", default=False,
                     help=("Do not pull docker images"))


@pytest.fixture(scope='session')
def docker_pull(request):
    return not request.config.getoption("--no-pull")


@pytest.fixture(scope='session')
def session_id():
    """Unique session identifier, random string."""
    return 'x-session-id'


@pytest.fixture(scope='session')
def docker():
    docker = APIClient(version='auto')
    return docker


@pytest.fixture(scope='session')
def redis_address(redis_server):
    print(redis_server)
    return dict(**redis_server['address'])


@pytest.fixture(scope='session')
def redis_server(unused_port, container_starter):
    tag = "latest"
    image = 'redis:{}'.format(tag)

    internal_port = 6379
    host_port = unused_port()

    container = container_starter(image, 'cache', internal_port, host_port,
                                  None, None)

    address = dict(address='redis://localhost:'+str(host_port))

    def connect():
        pool = redis.ConnectionPool(host='localhost', port=host_port)
        conn = redis.Redis(connection_pool=pool)
        conn.ping()

    wait_for_container(connect, image, Exception)
    container['address'] = address
    return container


@pytest.fixture(scope='session')
def pg_params(pg_server):
    return dict(**pg_server['params'])


@pytest.fixture(scope='session')
def pg_server(unused_port, container_starter):
    tag = "13.1"
    image = 'postgres:{}'.format(tag)

    internal_port = 5432
    host_port = unused_port()
    environment = {'POSTGRES_USER': 'postgres',
                   'POSTGRES_PASSWORD': 'root',
                   'POSTGRES_DB': 'postgres'}
    #
    # volume = (str(TEMP_FOLDER / 'docker' / 'pg'),
    #           '/var/lib/postgresql/data')

    container = container_starter(image, 'db', internal_port, host_port,
                                  environment, None)

    params = dict(database='postgres',
                  user='postgres',
                  password='root',
                  host='localhost',
                  port=host_port)

    def connect():
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.close()
        conn.close()

    wait_for_container(connect, image, psycopg2.Error)
    container['params'] = params
    alembic_config = AlembicConfig('alembic.ini')
    alembic_config.set_main_option('sqlalchemy.url', f'postgresql://postgres:root@localhost:{container["port"]}/postgres')
    alembic_upgrade(alembic_config, 'head')
    return container


@pytest.fixture(scope='session')
def container_starter(request, docker, session_id, docker_pull):

    def f(image, name, internal_port, host_port, env=None, volume=None,
          command=None):
        if docker_pull:
            print("Pulling {} image".format(image))
            docker.pull(image)

        if volume is not None:
            host_vol, cont_vol = volume
            host_config = docker.create_host_config(
                port_bindings={internal_port: host_port},
                binds={host_vol: cont_vol})
            volumes = [cont_vol]
        else:
            host_config = docker.create_host_config(
                port_bindings={internal_port: host_port})
            volumes = None

        container = docker.create_container(
            image=image,
            name=name,
            ports=[internal_port],
            detach=True,
            environment=env,
            volumes=volumes,
            command=command,
            host_config=host_config)
        docker.start(container=container['Id'])

        def fin():
            docker.kill(container=container['Id'])
            docker.remove_container(container['Id'], v=True)

        request.addfinalizer(fin)
        container['port'] = host_port
        return container

    return f


def wait_for_container(callable, image, skip_exception):
    delay = 0.001
    for i in range(12):
        try:
            callable()
            break
        except skip_exception as e:
            print("Waiting image to start, last exception: {}".format(e))
            time.sleep(delay)
            delay *= 2
    else:
        pytest.fail("Cannot start {} server".format(image))
