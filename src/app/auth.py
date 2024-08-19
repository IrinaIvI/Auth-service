#from dataclasses import dataclass
from fastapi import Depends, HTTPException,  UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import jwt
import os
import os
import json
from app.producer import Producer, KAFKA_TOPIC
from app.schemas import UserScheme, TokenScheme
from datetime import datetime, timedelta
from app.models import User, UserToken
from typing import Annotated
from sqlalchemy.exc import NoResultFound
from passlib.context import CryptContext
import logging

logging.basicConfig(level=logging.INFO)

from app.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройки для JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5

class Authentication:
    """Класс аутентификации пользователя."""

    def __init__(self):
        self.producer = Producer()

    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def registration(self, login: str, password: str, db: Annotated[Session, Depends(get_db)]):
        """Регистрация пользователя."""
        if not login.strip() or not password.strip():
            raise HTTPException(status_code=400, detail='Неправильно введены данные')
        hashed_password = pwd_context.hash(password)
        sql = text("""
            INSERT INTO auth_schema_ivashko.users_ivashko (login, password, verified, created_at, updated_at)
            VALUES (:login, :password, :verified, :created_at, :updated_at)
            RETURNING id, login, password, verified, created_at, updated_at;
        """)
        result = db.execute(sql, {
            'login': login,
            'password': hashed_password,
            'verified': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        })
        db.commit()
        user_data = result.fetchone()
        user_id, user_login, user_password, user_verified, user_created_at, user_updated_at = user_data
        if user_data is None:
            raise HTTPException(status_code=500, detail='Ошибка при регистрации пользователя')
        user = UserScheme(
            login=user_login,
            hashed_password=user_password,
            verified=user_verified,
            created_at=user_created_at,
            updated_at=user_updated_at
        )
        return user

    def authorisation(self, login: str, password: str, db: Annotated[Session, Depends(get_db)]) -> TokenScheme:
        """Авторизация пользователя."""
        if not login.strip() or not password.strip():
            raise HTTPException(status_code=400, detail="Неправильно введены данные")
        try:
            user = db.query(User).filter(User.login == login).one()
            logging.info(f"Найден пользователь: {user}")
            if self.verify_password(password, user.password):
                existing_token = db.query(UserToken).filter(
                    UserToken.user_id == user.id,
                    UserToken.is_valid == True,
                    UserToken.expiration_at > datetime.now()
                ).first()
                if existing_token:
                    logging.info(f"Найден существующий токен для пользователя {user.login}: {existing_token.token}")
                    return TokenScheme(token=existing_token.token)
                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                token = self.create_access_token(
                    data={"sub": user.login}, expires_delta=access_token_expires
                )
                sql = text("""
                    INSERT INTO auth_schema_ivashko.usertoken_ivashko (user_id, token, is_valid, expiration_at, updated_at)
                    VALUES (:user_id, :token, :is_valid, :expiration_at, :updated_at)
                    RETURNING token;
                """)
                db.execute(sql, {
                    'user_id': user.id,
                    'token': token,
                    'is_valid': True,
                    'expiration_at': datetime.now() + access_token_expires,
                    'updated_at': datetime.now()
                })
                db.commit()
                return TokenScheme(token=token)
            else:
                raise HTTPException(status_code=401, detail="Неверный пароль")
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        except jwt.PyJWTError as e:
            logging.error(f"JWT ошибка: {e}")
            raise HTTPException(status_code=500, detail="Ошибка в обработке токена")

    def validate(self, id: int, token: str, db: Annotated[Session, Depends(get_db)]):
        """Проверка токена на валидность."""
        user = db.query(User).filter(User.id == id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_token = db.query(UserToken).filter(UserToken.user_id == user.id, UserToken.token == token).first()
        if user_token and user_token.is_valid:
            return {"status": 200, "detail": "OK"}
        return  {"status": 401, "detail": "Unauthorised"}

    async def verify(self, user_id: int, photo: UploadFile = File(...)) -> dict:
        """Сохраняет фото на диск и отправляет сообщение в Kafka."""
        photo_directory = '/photos'
        photo_filename = photo.filename
        if not photo_filename:
            raise HTTPException(status_code=400, detail="Имя файла отсутствует")
        photo_path = os.path.join(photo_directory, photo_filename)
        if not os.path.exists(photo_directory):
            os.makedirs(photo_directory)
        try:
            with open(photo_path, "wb") as buffer:
                content = await photo.read()
                buffer.write(content)
                buffer.flush()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при сохранении фото: {e}")
        try:
            await self.producer.start()
            message = {
                'user_id': user_id,
                'photo_path': photo_path
            }
            await self.producer.send(KAFKA_TOPIC, key=json.dumps(user_id), value=message)
            return {'message': f'Сообщение {message} было отправлено'}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при отправке сообщения в Kafka: {e}")
        finally:
            await self.producer.stop()



