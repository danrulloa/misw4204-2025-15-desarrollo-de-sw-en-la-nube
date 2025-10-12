from typing import List
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.permission import PermissionOut
from app.schemas.group import GroupOut
from app.db.session import get_db
from app.services.authentication.user_service import UserService
from app.services.authorization.groups_service import GroupService
from app.schemas.group import GroupWithUsers

router = APIRouter()


@router.get("/{user_id}/permissions", response_model=list[PermissionOut])
async def get_user_permissions_endpoint(
    user_id: int = Path(..., title="ID del usuario"),
    db: AsyncSession = Depends(get_db)
):
    return await UserService.get_user_permissions(user_id, db)


@router.get("/{user_id}/groups", response_model=list[GroupOut])
async def get_user_groups_endpoint(
    user_id: int = Path(..., title="ID del usuario"),
    db: AsyncSession = Depends(get_db)
):
    return await UserService.get_user_groups(user_id, db)


@router.post("/{user_id}/groups/{group_id}", status_code=201)
async def assign_user_to_group_endpoint(
    user_id: int = Path(..., title="ID del usuario"),
    group_id: int = Path(..., title="ID del grupo"),
    db: AsyncSession = Depends(get_db)
):
    await UserService.assign_user_to_group(user_id, group_id, db)
    return {"detail": f"Usuario {user_id} asignado al grupo {group_id}"}



