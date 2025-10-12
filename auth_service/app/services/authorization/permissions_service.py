from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
from app.db.models.permission import Permission
from app.schemas.permission import PermissionCreate
from sqlalchemy.orm import selectinload
from app.db.models.group import Group
from app.db.models.user_groups import user_group_table
from app.db.models.group_permissions import group_permission_table

class PermissionService:
    @staticmethod
    async def create_permission(data: PermissionCreate, db: AsyncSession):
        stmt = insert(Permission).values(name=data.name, description=data.description).returning(Permission)
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one()

    @staticmethod
    async def get_groups_with_permission(permission_id: int, db: AsyncSession):
        stmt = (
            select(Permission)
            .options(selectinload(Permission.groups))
            .where(Permission.id == permission_id)
        )
        result = await db.execute(stmt)
        permission = result.scalar_one_or_none()

        if not permission:
            return []  # O lanzar HTTP 404 si lo deseas

        return permission.groups
    
    @staticmethod
    async def get_user_permissions(user_id: int, db: AsyncSession) -> list[str]:
        stmt = (
            select(Permission)
            .join(group_permission_table, Permission.id == group_permission_table.c.permission_id)
            .join(Group, group_permission_table.c.group_id == Group.id)
            .join(user_group_table, Group.id == user_group_table.c.group_id)
            .where(user_group_table.c.user_id == user_id)
            .distinct()
        )
        result = await db.execute(stmt)
        permissions = result.scalars().all()
        return [p.name for p in permissions]