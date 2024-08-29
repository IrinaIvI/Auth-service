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

class Authentication:
    """Класс аутентификации пользователя."""

    def __init__(self):
        """Инициализация класса аутентификации."""
        self.producer = Producer()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка подлинности пароля."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """Создание токена."""
        to_encode = data.copy()
        expire = datetime.now() + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire})
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
            updated_at=datetime.now()
        )
        db.add(new_user)
        db.commit()

        return UserScheme(
            login=new_user.login,
            hashed_password=new_user.password,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at
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
        existing_token = db.query(UserToken).filter(UserToken.user_id == user.id, UserToken.is_valid).first()

        if existing_token:
            if existing_token.expiration_at > now:
                return TokenScheme(token=existing_token.token)
            db.query(UserToken).filter(UserToken.id == existing_token.id).update({
                UserToken.is_valid: False,
                UserToken.updated_at: now
            })
            db.commit()
            return TokenScheme(token=existing_token.token)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_token = self.create_access_token(data={"sub": user.login}, expires_delta=access_token_expires)
        new_user_token = UserToken(
            user_id=user.id,
            token=new_token,
            is_valid=True,
            expiration_at=now + access_token_expires,
            updated_at=now
        )
        db.add(new_user_token)
        db.commit()
        return TokenScheme(token=new_token)

    def validate(self, user_id: int, token: str, db: Annotated[Session, Depends(get_db)]) -> dict:
        """Проверка токена на валидность."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail='User not found')

        user_token = db.query(UserToken).filter(UserToken.user_id == user.id, UserToken.token == token).first()
        if user_token and user_token.is_valid:
            return {'status': 200, 'detail': 'OK'}

        return {'status': 401, 'detail': 'Unauthorized'}

    async def verify(self, user_id: int, photo: UploadFile = File(...)) -> dict:
        """Сохраняет фото на диск и отправляет сообщение в Kafka."""
        photo_directory = '/auth_photos'
        photo_filename = photo.filename

        if not photo_filename:
            raise HTTPException(status_code=400, detail='Имя файла отсутствует')

        photo_path = os.path.join(photo_directory, photo_filename)
        if not os.path.exists(photo_directory):
            try:
                os.makedirs(photo_directory)
            except OSError as e:
                raise HTTPException(status_code=500, detail=f'Ошибка создания директории: {e}')

        try:
            await self.producer.start()
            message = {
                'user_id': user_id,
                'photo_path': photo_path
            }
            await self.producer.send(KAFKA_TOPIC, key=json.dumps(user_id), value=message)
            return {'message': f'Сообщение {message} было отправлено'}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Ошибка при отправке сообщения в Kafka: {e}')
        finally:
            await self.producer.stop()
