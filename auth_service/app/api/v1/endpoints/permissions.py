from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.permission import PermissionCreate, PermissionOut
from app.services.authorization.permissions_service import PermissionService
from app.db.session import get_db

router = APIRouter()

@router.post("/permissions", response_model=PermissionOut)
async def create_permission(
    data: PermissionCreate,
    db: AsyncSession = Depends(get_db)
):
    return await PermissionService.create_permission(data, db)
