from dataclasses import dataclass
from fastapi import HTTPException
import jwt
import os
from typing import Union
from fastapi import UploadFile, File
import os
import json
from app.producer import Producer, KAFKA_TOPIC

SECRET_KEY = str(os.environ.get('SECRET_KEY'))
ALGORITHM = 'HS256'

users = []

@dataclass
class User:
    """Класс пользователя."""

    login: str
    hashed_password: str
    token: str
    verified: bool = False


class Authentication:
    """Класс аутентификации пользователя."""

    def __init__(self):
        self.producer = Producer()

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

    def registration(self, login: str, password: str) -> User:
        """Регистрация пользователя."""
        if not login.strip() or not password.strip():
            return 'Неправильно введены данные'

        payload = {'user_login': login, 'password': password}
        token = jwt.encode(payload, SECRET_KEY, ALGORITHM)
        hashed_password = hash(password)
        user = User(login, hashed_password, token)
        users.append(user)
        return user

    def authorisation(self, login: str, password: str) -> Union[str, bool]:
        """Авторизация пользователя."""
        if not login.strip() or not password.strip():
            return 'Неправильно введены данные'
        else:
            try:
                for user in users:
                    if user.login == login and user.hashed_password == hash(password):
                        return user.token
            except jwt.PyJWTError:
                return None

    def validate(self, token: str):
        """Проверка токена на валидность."""
        for user in users:
                if user.token == token:
                    raise HTTPException(status_code=200, detail='OK')
        raise HTTPException(status_code=401, detail='Unauthorised')

