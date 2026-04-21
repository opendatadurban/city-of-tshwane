from fastapi import APIRouter

from app.api.routes import login, users, utils, items, register, payments

api_router = APIRouter()
# api_router.include_router(login.router)
# api_router.include_router(register.router)
# api_router.include_router(users.router)
api_router.include_router(utils.router)
# api_router.include_router(items.router)
api_router.include_router(payments.router)