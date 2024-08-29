from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import Annotated

from app.auth import Authentication

router = APIRouter(
    prefix='/auth_service',
)

@router.get('/registration')
def registration(user: Annotated[str, str, Depends(Authentication().registration)]):
    return user

@router.post('/authorisation')
def authorisation(token: Annotated[str, str, Depends(Authentication().authorisation)]):
    return token

@router.get('/validate')
def validate(result: Annotated[str, Depends(Authentication().validate)]):
    return result

@router.get('/health/ready')
async def health_check():
    """Эндпоинт для проверки состояния сервиса."""
    return JSONResponse(status_code=200)
