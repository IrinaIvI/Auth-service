from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, MetaData
from sqlalchemy.ext.declarative import declarative_base

metadata = MetaData(schema="auth_schema_ivashko")
Base = declarative_base(metadata=metadata)

class User(Base):
    __tablename__ = "users_ivashko"
    __table_args__ = {"schema": "auth_schema_ivashko"}

    id = Column(Integer, primary_key=True)
    login = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    verified = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, nullable=True, default=None)
    updated_at = Column(TIMESTAMP, nullable=True, default=None)


class UserToken(Base):
    __tablename__ = "usertoken_ivashko"
    __table_args__ = {"schema": "auth_schema_ivashko"}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('auth_schema_ivashko.users_ivashko.id'))
    token = Column(String, unique=True, nullable=False)
    is_valid = Column(Boolean, default=False)
    expiration_at = Column(TIMESTAMP, nullable=True, default=None)
    updated_at = Column(TIMESTAMP, nullable=True, default=None)

