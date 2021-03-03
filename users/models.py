from sqlalchemy import Boolean, Column, Integer, String, Unicode, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import EmailType
from passlib.hash import pbkdf2_sha256

Base = declarative_base()


class Auth(Base):  # type: ignore
    __tablename__ = 'credentials'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(EmailType(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    @staticmethod
    def check_password(raw_pass: str, pass_hash: str) -> bool:
        return pbkdf2_sha256.verify(raw_pass, pass_hash)

    @staticmethod
    def get_pass_hash(raw_pass: str):
        return pbkdf2_sha256.hash(raw_pass)


class User(Base):  # type: ignore
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    email = Column(EmailType(128), unique=True, index=True, nullable=False)
    first_name = Column(Unicode(255), nullable=False)
    last_name = Column(Unicode(255), nullable=False)
    bio = Column(Unicode(255))
    is_active = Column(Boolean, default=False)
