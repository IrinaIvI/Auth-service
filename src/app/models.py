from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    login = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    verified = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=None)
    updated_at = Column(TIMESTAMP, default=None)

    account = relationship("Account", back_populates="user")
    user_tokens = relationship("UserToken", back_populates="user")
    face_data = relationship("UserFaceData", back_populates="user")

class UserToken(Base):
    __tablename__ = "user_token"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    token = Column(String, unique=True, nullable=False)
    is_valid = Column(Boolean, default=False)
    expiration_at = Column(TIMESTAMP, default=None)
    updated_at = Column(TIMESTAMP, default=None)

    user = relationship("User", back_populates="user_token")
