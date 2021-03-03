import pytest
import socket


@pytest.fixture(scope='session')
def unused_port():
    def f():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]
    return f


pytest_plugins = [
    'tests.fixtures.fixture_docker',
    'tests.fixtures.fixture_db',
    'tests.fixtures.fixture_client'
]
