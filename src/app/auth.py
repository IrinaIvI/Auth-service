import os
import jwt

SECRET_KEY = os.environ['SECRET_KEY']
ALGORITHM = 'HS256'

users = {}


class Authentication:
    """Класс аутентификации пользователя."""

    def registration(self, login: str, password: str) -> dict:
        """Регистрация пользователя."""
        payload = {'user_login': login, 'password': password}
        token = jwt.encode(payload, SECRET_KEY, ALGORITHM)
        users[login] = token
        return {'token': token}

    def authorisation(self, login: str, password: str) -> dict:
        """Авторизация пользователя."""
        try:
            if login in users:
                payload = {'user_login': login, 'password': password}
                token = jwt.encode(payload, SECRET_KEY, ALGORITHM)
                if users.get(login, login) == token:
                    return {'token': token}
        except jwt.PyJWTError:
            return None
