from dataclasses import dataclass
from fastapi import HTTPException, UploadFile
from aiokafka import AIOKafkaProducer
import asyncio
import jwt
import os
from typing import Union
import shutil
import uuid


SECRET_KEY = str(os.environ.get('SECRET_KEY'))
ALGORITHM = 'HS256'
KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC = 'face_verification'

users = []


class Producer:
    """Класс для отправки сообщений в Kafka с использованием aiokafka."""

    def __init__(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKER)

    async def start(self):
        """Запускает продюсер."""
        await self.producer.start()

    async def stop(self):
        """Останавливает продюсер."""
        await self.producer.stop()

    async def send(self, topic: str, key: str, value: str):
        """Отправляет сообщение в Kafka."""
        try:
            await self.producer.send_and_wait(topic, key=key.encode(), value=value.encode())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при отправке сообщения в Kafka: {e}")


@dataclass
class User:
    """Класс пользователя."""

    login: str
    hashed_password: str
    token: str


class Authentication:
    """Класс аутентификации пользователя."""

    def __init__(self):
        self.producer = Producer()


    async def verify(self, user_id: int, photo: UploadFile) -> dict:
        """Сохраняет фото на диск и отправляет сообщение в Kafka."""
        # Генерация уникального имени файла для сохранения
        photo_filename = f"{uuid.uuid4()}.jpg"
        photo_path = os.path.join('photos', photo_filename)

        # Сохраняем фото на диск
        try:
            with open(photo_path, "wb") as buffer:
                shutil.copyfileobj(photo.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при сохранении фото: {e}")

        # Отправка сообщения в Kafka
        message = {
            'user_id': user_id,
            'photo_path': photo_path
        }
        await self.producer.send(KAFKA_TOPIC, key=str(user_id), value=str(message))

        return {"status": "accepted", "photo_path": photo_path}
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

    def validate(self, user_id: int, token: str) -> bool:
        """Проверка токена на валидность."""
        for user in users:
            if user.id == user_id:
                if user.token == token:
                    raise HTTPException(status_code=200, detail='OK')
            raise HTTPException(status_code=401, detail='Unauthorised')

