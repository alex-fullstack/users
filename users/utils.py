# utils.py
from typing import Union

import trafaret as t
import jwt

TRAFARET = t.Dict({
    t.Key('postgres'):
        t.Dict({
            'database': t.String(),
            'user': t.String(),
            'password': t.String(),
            'host': t.String(),
            'port': t.Int(),
            'minsize': t.Int(),
            'maxsize': t.Int(),
        }),
    t.Key('host'): t.IP,
    t.Key('port'): t.Int(),
    t.Key('jwt'):
        t.Dict({
            'secret': t.String(),
            'algorithm': t.String(),
            'request_property': t.String(),
            'auth_scheme': t.String(),
            'access_token_living_minutes': t.Int(),
            'refresh_token_living_days': t.Int(),
        }),
})


def get_token(*, payload: dict, secret: Union[str, bytes], algorithm: str) -> str:
    encoded_token = jwt.encode(
        payload,
        secret,
        algorithm=algorithm)
    return encoded_token.decode('utf8')
