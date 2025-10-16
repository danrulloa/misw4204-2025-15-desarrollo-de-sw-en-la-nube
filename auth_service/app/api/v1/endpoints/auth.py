from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate
from app.services.authentication.auth_service import AuthService
from app.services.authentication.user_service import UserService
from app.db.session import get_db
from datetime import timedelta
from app.db.models.session import Session
from dotenv import load_dotenv
from app.services.authorization.permissions_service import PermissionService
import os

from sqlalchemy import select

load_dotenv()  

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ["TOKEN_EXPIRE"])
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.environ["REFRESH_TOKEN_EXPIRE"])


router = APIRouter()

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # 1. Autenticar usuario
    user = await AuthService.authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 2. Configurar tiempos de expiración
    expires_delta_access = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expires_delta_refresh = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    # 3. Obtener permisos como strings
    permissions = await PermissionService.get_user_permissions(user.id, db)

    # 4. Crear access y refresh tokens
    access_token, access_expiration = AuthService.create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "tenant_id": user.tenant_id,
            "permissions": permissions,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "city": user.city or ""
        },
        expires_delta=expires_delta_access
    )
    refresh_token, refresh_expiration = AuthService.create_refresh_token(
        data={
            "sub": user.email,
            "user_id": user.id
        },
        expires_delta=expires_delta_refresh 
    )

    # 5. Guardar sesión
    await AuthService.create_session(
        db=db,
        user_id=user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        access_expires_at=access_expiration,
        refresh_expires_at=refresh_expiration,
    )

    # 6. Respuesta
    return {
        "access_token": access_token,
        "expires_in_access": access_expiration.isoformat(),
        "refresh_token": refresh_token,
        "expires_in_refresh": refresh_expiration.isoformat(),
        "token_type": "Bearer"
    }


@router.post("/signup")
#Cuando se finalize el desarrollo se debe ajustar el nivel de seguridad del registro
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_user = await UserService.create_user(user_data, db)
        return {"email": new_user.email, "message":"Usuario creado exitosamente","user_id":new_user.id}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    
@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    # 1. Validar existencia de la sesión
    result = await db.execute(
        select(Session).where(Session.refresh_token == refresh_token)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=401, detail="Sesión no encontrada para el refresh token")

    # 2. Renovar access token
    expires_delta_access = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token, access_expiration = await AuthService.renew_access_token(
        refresh_token, db=db, expires_delta=expires_delta_access
    )

    # 3. Actualizar la sesión con el nuevo token
    session.session_token = new_access_token
    session.session_expires_at = access_expiration
    await db.commit()

    return {
        "access_token": new_access_token,
        "expires_in": access_expiration.isoformat(),
        "token_type": "Bearer"
    }