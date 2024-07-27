import os
from dataclasses import dataclass
import jwt
from typing import Union
from fastapi import HTTPException
SECRET_KEY = str(os.environ.get('SECRET_KEY')) # переделать под yaml?
ALGORITHM = 'HS256'

users = []

@dataclass
class User:
    """Класс пользователя."""

    login: str
    hashed_password: str
    token: str

class Authentication:
    """Класс аутентификации пользователя."""

    def registration(self, login: str, password: str) -> User:
        """Регистрация пользователя."""
        payload = {'user_login': login, 'password': password}
        token = jwt.encode(payload, SECRET_KEY, ALGORITHM)
        hashed_password = hash(password)
        user = User(login, hashed_password, token)
        users.append(user)
        return user

    def authorisation(self, login: str, password: str) -> Union[str, bool]:
        """Авторизация пользователя."""
        try:
            for user in users:
                if user.login == login and user.hashed_password == hash(password):
                    return user.token
        except jwt.PyJWTError:
            return None

    def validate(self, token: str) -> bool:
        """Проверка токена на валидность."""
        for user in users:
            if user.token == token:
                raise HTTPException(status_code=200, detail='OK')
        raise HTTPException(status_code=401, detail='Unauthorised')

