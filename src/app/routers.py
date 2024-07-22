from fastapi import APIRouter, Depends
from typing import Annotated

# from crud.crud import login_employee, get_current_employee
# from models.models import EmployeeModel
# from schemas.schemas import Token

router = APIRouter(
    prefix="/auth_service",
)


# @router.post('/login', response_model=Token)
# def login(token: Annotated[str, Depends(login_employee)]):
#     return Token(access_token=token)


# @router.get('/salary_date')
# def get_salary_date(employee: Annotated[EmployeeModel, Depends(get_current_employee)]) -> dict:
#     return {'salary': employee['salary'], 'raising_date': employee['raising_date']}
