from typing import Dict

from aiopg.sa.connection import SAConnection
from aiopg.sa.result import RowProxy
from psycopg2.errors import UniqueViolation

from users.decorators import resource
from users.errors import UserNotFoundError, WrongCredentialsError, UserCreateError
from users.models import User, Auth


@resource
async def get_user(conn: SAConnection, user_id: int) -> RowProxy:
    user = User.__table__
    result = await conn.execute(user.select().where(user.c.id == user_id))
    user_record = await result.first()
    if not user_record:
        raise UserNotFoundError(user_id)
    return user_record


@resource
async def get_auth(conn: SAConnection, credentials: Dict[str, str]) -> RowProxy:
    email = credentials.get('email', '')
    auth = Auth.__table__
    result = await conn.execute(auth.select().where(auth.c.email == email))
    auth_record = await result.first()
    if not auth_record or not Auth.check_password(credentials.get('password', ''), auth_record.hashed_password):
        raise WrongCredentialsError(email)

    return auth_record


@resource
async def create_user(conn: SAConnection, reg_data: dict) -> int:
    password = reg_data.pop('password', '')
    email = reg_data.get('email', '')
    users = User.__table__
    try:
        result = await conn.execute(users.insert().values(**reg_data))
    except UniqueViolation:
        raise UserCreateError(email)

    created_user = await result.first()
    user_id = created_user.id
    credentials = Auth.__table__
    await conn.execute(credentials.insert().values(
        email=email,
        hashed_password=Auth.get_pass_hash(password),
        user_id=user_id
    ))

    return user_id


@resource
async def update_user(conn: SAConnection, user_id: int, valid_profile_data: dict) -> None:
    users = User.__table__
    await conn.execute(users.update().values(**valid_profile_data).where(users.c.id == user_id))
