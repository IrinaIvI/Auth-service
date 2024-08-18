from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class UserScheme(BaseModel):
    """Схема пользователя."""

    login: str
    hashed_password: int
    verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    """Схема токена."""

    id: int
    user_id: int
    token: Optional[str | None]
    is_valid: bool = False
    expiration_at: datetime = None
    updated_at: datetime = None


