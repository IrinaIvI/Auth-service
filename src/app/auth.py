import json
import os
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, UploadFile, File
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import Annotated

from app.database import get_db
from app.models import User, UserToken
from app.producer import Producer, KAFKA_TOPIC
from app.schemas import UserScheme, TokenScheme

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 5
DEFAULT_FILE = File(...)


class Authentication:
    """Класс аутентификации пользователя."""

    def __init__(self):
        """Инициализация класса аутентификации."""
        self.producer = Producer()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка подлинности пароля."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data_token: dict, expires_delta: timedelta = None) -> str:
        """Создание токена."""
        to_encode = data_token.copy()
        expire = datetime.now() + (expires_delta or timedelta(minutes=15))
        to_encode.update({'exp': expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def registration(self, login: str, password: str, db: Annotated[Session, Depends(get_db)]) -> UserScheme:
        """Регистрация пользователя."""
        if not login.strip() or not password.strip():
            raise HTTPException(status_code=400, detail='Неправильные данные')

        hashed_password = pwd_context.hash(password)
        if db.query(User).filter(User.login == login).first():
            raise HTTPException(status_code=400, detail='Такой пользователь уже существует')

        new_user = User(
            login=login,
            password=hashed_password,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(new_user)
        db.commit()

        return UserScheme(
            login=new_user.login,
            hashed_password=new_user.password,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
        )

    def authorisation(self, login: str, password: str, db: Annotated[Session, Depends(get_db)]) -> TokenScheme:
        """Авторизация пользователя."""
        if not login.strip() or not password.strip():
            raise HTTPException(status_code=400, detail='Неправильные данные')

        user = db.query(User).filter(User.login == login).one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail='Пользователь не найден')

        if not self.verify_password(password, user.password):
            raise HTTPException(status_code=401, detail='Неверный пароль')

        now = datetime.now()
        existing_token = db.query(UserToken).filter(
            UserToken.user_id == user.id,
            UserToken.is_valid,
        ).first()

        if existing_token:
            if existing_token.expiration_at > now:
                return TokenScheme(token=existing_token.token)
            db.query(UserToken).filter(
                UserToken.id == existing_token.id,
            ).update({
                UserToken.is_valid: False,
                UserToken.updated_at: now,
            })
            db.commit()
            return TokenScheme(token=existing_token.token)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_token = self.create_access_token(data_token={'sub': user.login}, expires_delta=access_token_expires)
        new_user_token = UserToken(
            user_id=user.id,
            token=new_token,
            is_valid=True,
            expiration_at=now + access_token_expires,
            updated_at=now,
        )
        db.add(new_user_token)
        db.commit()
        return TokenScheme(token=new_token)

    def validate(self, user_id: int, token: str, db: Annotated[Session, Depends(get_db)]) -> dict:
        """Проверка токена на валидность."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail='User not found')

        user_token = db.query(UserToken).filter(
            UserToken.user_id == user.id,
            UserToken.token == token,
        ).first()
        if user_token and user_token.is_valid:
            return {'status': 200, 'detail': 'OK'}

        return {'status': 401, 'detail': 'Unauthorized'}

    async def save_photo(self, photo: UploadFile, photo_directory: str) -> str:
        """Сохраняет фото на диск и возвращает путь к файлу."""
        photo_filename = photo.filename
        if not photo_filename:
            raise HTTPException(status_code=400, detail='Имя файла отсутствует')

        photo_path = os.path.join(photo_directory, photo_filename)
        if not os.path.exists(photo_directory):
            try:
                os.makedirs(photo_directory)
            except OSError as error_dir:
                raise HTTPException(status_code=500, detail=f'Ошибка создания директории: {error_dir}')

        with open(photo_path, 'wb') as buffer:
            buffer.write(await photo.read())

        return photo_path

    async def send_to_kafka(self, producer: Producer, topic: str, user_id: int, photo_path: str) -> None:
        """Отправляет сообщение с информацией о фото в Kafka."""
        try:
            await producer.start()
            message = {
                'user_id': user_id,
                'photo_path': photo_path,
            }
            await producer.send(topic, key=json.dumps(user_id), value=message)
            return {'message': f'Сообщение {message} было отправлено'}
        except Exception as error_kafka:
            raise HTTPException(status_code=500, detail=f'Ошибка при отправке сообщения в Kafka: {error_kafka}')
        finally:
            await producer.stop()

    async def verify(self, user_id: int, photo: UploadFile = DEFAULT_FILE) -> dict:
        """Сохраняет фото на диск и отправляет сообщение в Kafka."""
        photo_directory = '/auth_photos'
        photo_path = self.save_photo(photo, photo_directory)
        self.send_to_kafka(self.producer, KAFKA_TOPIC, user_id, photo_path)
