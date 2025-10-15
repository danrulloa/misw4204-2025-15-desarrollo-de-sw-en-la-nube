import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

load_dotenv()

# Seguridad
ALGORITHM = os.environ["ALGORITHM"]
ACCESS_TOKEN_SECRET_KEY = os.environ["ACCESS_TOKEN_SECRET_KEY"]
REFRESH_TOKEN_SECRET_KEY = os.environ["REFRESH_TOKEN_SECRET_KEY"]
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ["TOKEN_EXPIRE"])
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.environ["REFRESH_TOKEN_EXPIRE"])

from app.core.security import pwd_context, oauth2_scheme
from app.db.models.session import Session
from app.db.models.refreshToken import RefreshToken
from app.db.models.user import User
from app.services.authentication.user_service import UserService



class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    async def get_user(email: str, db: AsyncSession) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def authenticate_user(email: str, password: str, db: AsyncSession) -> Optional[User]:
        user = await AuthService.get_user(email, db)
        if not user or not AuthService.verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "token_type": "access"
        })
        return jwt.encode(to_encode, ACCESS_TOKEN_SECRET_KEY, algorithm=ALGORITHM), expire

    @staticmethod
    def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "token_type": "refresh"
        })
        return jwt.encode(to_encode, REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM), expire

    @staticmethod
    async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(),
    ) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, ACCESS_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if not username:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = await AuthService.get_user(username, db)
        if user is None:
            raise credentials_exception
        return user

    @staticmethod
    def has_permission(permission: str):
        def wrapper(user: User = Depends(AuthService.get_current_user)):
            if not any(p.name == permission for p in user.permissions):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
            return True
        return wrapper

    @staticmethod
    async def is_token_active(refresh_token: str, db: AsyncSession) -> RefreshToken:
        result = await db.execute(select(RefreshToken).filter_by(token=refresh_token))
        token = result.scalars().first()

        if not token or not token.is_active or token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            if token:
                token.is_active = False
                token.session.is_active = False
                await db.commit()
            raise HTTPException(status_code=401, detail="Refresh token expired or invalid")

        return token

    @staticmethod
    async def renew_access_token(
        refresh_token: str,
        db: AsyncSession,
        expires_delta: Optional[timedelta] = None,
    ) -> tuple[str, datetime]:
        await AuthService.is_token_active(refresh_token, db)

        try:
            payload = jwt.decode(refresh_token, REFRESH_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = await UserService.get_user_by_username(username, db)
        permissions = await UserService.get_user_permissions(user.id, db)
        permission_names = [p.name for p in permissions]

        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "tenant_id": user.tenant_id,
            "permissions": permission_names
        }

        return AuthService.create_access_token(token_data, expires_delta)

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: int,
        access_token: str,
        refresh_token: str,
        access_expires_at: datetime,
        refresh_expires_at: datetime,
    ) -> Session:
        session = Session(
            user_id=user_id,
            session_token=access_token,
            refresh_token=refresh_token,
            refresh_expires_at=refresh_expires_at,
            session_expires_at=access_expires_at,
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )
        db.add(session)
        await db.flush()

        refresh_entry = RefreshToken(
            session_id=session.id,
            token=refresh_token,
            created_at=datetime.now(timezone.utc),
            expires_at=refresh_expires_at,
            is_active=True,
        )
        db.add(refresh_entry)
        await db.commit()

        return session
