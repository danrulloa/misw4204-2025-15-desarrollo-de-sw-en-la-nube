from sqlalchemy import insert, select
from app.db.models.group import Group
from app.db.models.group_permissions import group_permission_table
from app.schemas.group import GroupCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status


class GroupService:
    @staticmethod
    async def create_group(data: GroupCreate, db: AsyncSession):
        # Crear grupo
        new_group = Group(name=data.name)
        db.add(new_group)
        await db.flush()  # Necesario para obtener el ID antes del commit

        # Asociar permisos
        if data.permission_ids:
            stmt = insert(group_permission_table).values([
                {"group_id": new_group.id, "permission_id": pid}
                for pid in data.permission_ids
            ])
            await db.execute(stmt)

        await db.commit()
        await db.refresh(new_group)
        return new_group
    
    @staticmethod
    async def get_group_permissions(group_id: int, db: AsyncSession):
        stmt = (
            select(Group)
            .options(selectinload(Group.permissions))
            .where(Group.id == group_id)
        )
        result = await db.execute(stmt)
        group = result.scalar_one_or_none()

        if not group:
            return []  # O lanzar HTTP 404 si lo deseas

        return group.permissions
    
    @staticmethod
    async def get_all_groups_with_users(db: AsyncSession):
        result = await db.execute(select(Group).options(selectinload(Group.users)))
        return result.scalars().all()
    
    @staticmethod
    async def get_group_with_users(group_id: int, db: AsyncSession):
        stmt = select(Group).options(selectinload(Group.users)).where(Group.id == group_id)
        result = await db.execute(stmt)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grupo con ID {group_id} no encontrado"
            )

        return group
