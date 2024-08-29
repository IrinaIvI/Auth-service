from fastapi import Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Annotated
import jwt
import os
import json
from app.producer import Producer, KAFKA_TOPIC
from app.schemas import UserScheme, TokenScheme
from datetime import datetime, timedelta
from app.models import User, UserToken
from sqlalchemy.exc import NoResultFound
from passlib.context import CryptContext
from app.database import get_db

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = 'HS256'
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

    def registration(self, login: str, password: str, db: Annotated[Session, Depends(get_db)]) -> UserScheme:
        """Регистрация пользователя."""
        if not login.strip() or not password.strip():
            raise HTTPException(status_code=400, detail='Неправильно введены данные')
        hashed_password = pwd_context.hash(password)
        existing_user = db.query(User).filter(User.login == login).first()
        if existing_user:
            raise HTTPException(status_code=400, detail='Такой пользователь уже существует')
        new_user = User(login=login, password=hashed_password, created_at=datetime.now(), updated_at=datetime.now())
        db.add(new_user)
        db.commit()
        return UserScheme(login=new_user.login, hashed_password=new_user.password,
                        created_at=new_user.created_at, updated_at=new_user.updated_at)

    def authorisation(self, login: str, password: str, db: Annotated[Session, Depends(get_db)]) -> TokenScheme:
        """Авторизация пользователя."""
        if not login.strip() or not password.strip():
            raise HTTPException(status_code=400, detail="Неправильно введены данные")
        try:
            user = db.query(User).filter(User.login == login).one()
            if self.verify_password(password, user.password):
                existing_token = db.query(UserToken).filter(UserToken.user_id == user.id, UserToken.is_valid == True).first()
                now = datetime.now()

                if existing_token:
                    if existing_token.expiration_at > now:
                        return TokenScheme(token=existing_token.token)
                    else:
                        db.query(UserToken).filter(UserToken.id == existing_token.id).update({
                            UserToken.is_valid: False,
                            UserToken.updated_at: now,
                        })
                        db.commit()
                        return TokenScheme(token=existing_token.token)

                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                new_token = self.create_access_token(data={"sub": user.login},
                                                     expires_delta=access_token_expires
                                                     )
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
            else:
                raise HTTPException(status_code=401, detail="Неверный пароль")
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        except jwt.PyJWTError as e:
            raise HTTPException(status_code=500, detail="Ошибка в обработке токена")

    def validate(self, user_id: int, token: str, db: Annotated[Session, Depends(get_db)]):
        """Проверка токена на валидность."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_token = db.query(UserToken).filter(UserToken.user_id == user.id, UserToken.token == token).first()
        if user_token and user_token.is_valid:
            return {'status': 200, 'detail': 'OK'}
        return  {'status': 401, 'detail': 'Unauthorised'}

    async def verify(self, user_id: int, photo: UploadFile = File(...)) -> dict:
        """Сохраняет фото на диск и отправляет сообщение в Kafka."""
        photo_directory = '/auth_photos'
        photo_filename = photo.filename
        if not photo_filename:
            raise HTTPException(status_code=400, detail="Имя файла отсутствует")
        photo_path = os.path.join(photo_directory, photo_filename)
        try:
            if not os.path.exists(photo_path):
                os.makedirs(photo_path)
                print(f"Директория {photo_path} успешно создана")
            else:
                print(f"Директория {photo_path} Уже существует")
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка создания директории: {str(e)}")

        try:
            await self.producer.start()
            message = {
                'user_id': user_id,
                'photo_path': photo_path,
            }
            await self.producer.send(KAFKA_TOPIC, key=json.dumps(user_id), value=message)
            return {'message': f'Сообщение {message} было отправлено'}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при отправке сообщения в Kafka: {e}")
        finally:
            await self.producer.stop()
