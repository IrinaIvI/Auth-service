from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class UserScheme(BaseModel):
    """Схема пользователя."""

    login: str
    hashed_password: str
    verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class TokenScheme(BaseModel):
    """Схема токена."""
    
    token: Optional[str | None]


