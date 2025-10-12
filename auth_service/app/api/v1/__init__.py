from fastapi import APIRouter
from app.api.v1.endpoints import status, auth, groups, permissions, user

api_router = APIRouter()
api_router.include_router(status.router)
api_router.include_router(auth.router)
api_router.include_router(groups.router)
api_router.include_router(permissions.router)
api_router.include_router(user.router)