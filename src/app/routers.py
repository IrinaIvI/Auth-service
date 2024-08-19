from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Annotated
from app.schemas import UserScheme, TokenScheme
from app.auth import Authentication

router = APIRouter(
    prefix='/auth_service',
)

@router.post('/registration', response_model=UserScheme)
def registration(user: Annotated[str, str, Depends(Authentication().registration)]):
    return user

@router.post('/authorisation', response_model=TokenScheme)
def authorisation(token: Annotated[str, str, Depends(Authentication().authorisation)]):
    return token

@router.get('/validate')
def validate(result: Annotated[int, str, Depends(Authentication().validate)]):
    return result


@router.get('/health/ready')
async def health_check():
    return JSONResponse(status_code=200, content={"message": "success"})

@router.post('/verify')
async def verify(user_id: int, photo: UploadFile = File(...)):
    auth = Authentication()
    await auth.producer.start()
    try:
        result = await auth.verify(user_id, photo)
    finally:
        await auth.producer.stop()
    return result

