from typing import List
from app.schemas.group import GroupCreate, GroupOut, GroupWithUsers
from app.services.authorization.groups_service import GroupService
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()

@router.post("/group", response_model=GroupOut, status_code=201)
async def create_group(
    group_data: GroupCreate,
    db: AsyncSession = Depends(get_db)
):
    return await GroupService.create_group(group_data, db)

@router.get("/groups-with-users", response_model=List[GroupWithUsers])
async def list_groups_with_users(db: AsyncSession = Depends(get_db)):
    return await GroupService.get_all_groups_with_users(db)

@router.get("/groups/{group_id}/users", response_model=GroupWithUsers)
async def get_users_by_group(
    group_id: int = Path(..., title="ID del grupo"),
    db: AsyncSession = Depends(get_db)
):
    return await GroupService.get_group_with_users(group_id, db)
