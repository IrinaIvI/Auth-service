from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey
from common_base import Base

class User(Base):
    __tablename__ = "users_ivashko"

    id = Column(Integer, primary_key=True)
    login = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    verified = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, nullable=True, default=None)
    updated_at = Column(TIMESTAMP, nullable=True, default=None)

class UserToken(Base):
    __tablename__ = "usertoken_ivashko"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('ivashko_schema.users_ivashko.id'))
    token = Column(String, unique=True, nullable=False)
    is_valid = Column(Boolean, default=False)
    expiration_at = Column(TIMESTAMP, nullable=True, default=None)
    updated_at = Column(TIMESTAMP, nullable=True, default=None)
