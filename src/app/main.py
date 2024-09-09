from fastapi import FastAPI
from app.routers import router

app = FastAPI(title='Auth Service')
app.include_router(router)
