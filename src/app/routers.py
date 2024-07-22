from fastapi import APIRouter, Depends
from typing import Annotated, Union

from app.auth import Authentication, User

router = APIRouter(
    prefix="/auth_service",
)

@router.post('/registration')
def registration(user: Annotated[str, str, Depends(Authentication().registration)]):
    return user

@router.get('/authorisation')
def authorisation(token: Annotated[str, str, Depends(Authentication().authorisation)]):
    return token

@router.get('/validate')
def validate(result: Annotated[str, str, Depends(Authentication().validate)]):
    return result
