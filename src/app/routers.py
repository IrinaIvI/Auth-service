from fastapi import APIRouter, Depends, UploadFile, File
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
    return JSONResponse(status_code=200, details='succes')

@router.post('/verify')
async def verify(user_id: int, photo: UploadFile = File(...)):
    auth = Authentication()
    await auth.producer.start()
    try:
        result = await auth.verify(user_id, photo)
    finally:
        await auth.producer.stop()
    return JSONResponse(content=result)
