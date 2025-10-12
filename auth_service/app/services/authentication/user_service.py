from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.db.models.user import User
from app.db.models.group import Group
from app.db.models.permission import Permission
from app.db.models.group_permissions import group_permission_table
from app.db.models.user_groups import user_group_table
from app.schemas.user import UserCreate



class UserService:
    @staticmethod
    async def create_user(user_data: UserCreate, db: AsyncSession):
        from app.services.authentication.auth_service import AuthService
        # Verificar si el usuario ya existe
        query = select(User).where(
            (User.username == user_data.username) | (User.email == user_data.email)
        )
        result = await db.execute(query)
        existing_user = result.scalar()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )

        # Hashear la contraseña
        hashed_password = AuthService.get_password_hash(user_data.password)

        # Crear la instancia del usuario
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            tenant_id=user_data.tenant
        )

        # Asignar grupo por defecto si existe
        default_group_result = await db.execute(select(Group).where(Group.name == "user"))
        default_group = default_group_result.scalar()
        if default_group:
            new_user.groups.append(default_group)

        db.add(new_user)
        try:
            await db.commit()
            await db.refresh(new_user)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user due to database error"
            )

        return new_user

    @staticmethod
    async def get_user_permissions(user_id: int, db: AsyncSession):
        stmt = (
            select(Permission)
            .join(group_permission_table, Permission.id == group_permission_table.c.permission_id)
            .join(Group, group_permission_table.c.group_id == Group.id)
            .join(user_group_table, Group.id == user_group_table.c.group_id)
            .where(user_group_table.c.user_id == user_id)
            .distinct()
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_user_groups(user_id: int, db: AsyncSession):
        stmt = (
            select(Group)
            .join(user_group_table, Group.id == user_group_table.c.group_id)
            .where(user_group_table.c.user_id == user_id)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def assign_user_to_group(user_id: int, group_id: int, db: AsyncSession):
        user = await db.get(User, user_id)
        group = await db.get(Group, group_id)

        if not user or not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario o grupo no encontrado"
            )

        # Verificar si ya existe la relación
        exists_stmt = select(user_group_table).where(
            user_group_table.c.user_id == user_id,
            user_group_table.c.group_id == group_id
        )
        result = await db.execute(exists_stmt)
        if result.first():
            return  # Ya existe, idempotente

        # Insertar relación
        stmt = insert(user_group_table).values(user_id=user_id, group_id=group_id)
        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def get_user_by_username(username: str, db: AsyncSession) -> User:
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return user