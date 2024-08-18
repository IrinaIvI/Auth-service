#from dataclasses import dataclass
from fastapi import Depends, HTTPException,  UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
import jwt
import os
from typing import Union
import os
import json
from app.producer import Producer, KAFKA_TOPIC
from app.schemas import UserScheme, Token
from datetime import datetime
from app.models import User
from typing import Annotated

from app.database import get_db

SECRET_KEY = str(os.environ.get('SECRET_KEY'))
ALGORITHM = 'HS256'

class Authentication:
    """Класс аутентификации пользователя."""

    def __init__(self):
        self.producer = Producer()

    def registration(self, login: str, password: str, db: Annotated[Session, Depends(get_db)]):
        """Регистрация пользователя."""
        if not login.strip() or not password.strip():
            raise HTTPException(status_code=400, detail='Неправильно введены данные')
        result = db.execute(text("""CREATE SCHEMA auth_schema_ivashko;
                        CREATE TABLE auth_schema_ivashko.users_ivashko (
                        id SERIAL PRIMARY KEY,
                        login VARCHAR(255) NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        verified BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW());
                        INSERT INTO auth_schema_ivashko.users_ivashko (login, password, verified, created_at, updated_at)
            VALUES ('mike', 12345, False, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);"""))
        db.commit()
        return result


    def authorisation(self, login: str, password: str) -> Union[str, bool]:
        """Авторизация пользователя."""
        if not login.strip() or not password.strip():
            return 'Неправильно введены данные'
        else:
            try:
                for user in users: # запрос в бд
                    if user.login == login and user.hashed_password == hash(password):
                        return user.token
            except jwt.PyJWTError:
                return None

    def validate(self, token: str):
        """Проверка токена на валидность."""
        for user in users: # запрос в бд
                if user.token == token:
                    raise HTTPException(status_code=200, detail='OK')
        raise HTTPException(status_code=401, detail='Unauthorised')

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

