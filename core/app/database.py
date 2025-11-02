# app/database.py
from typing import AsyncGenerator
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from app.config import settings

# Usar la configuración centralizada en settings
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,           # Aumentar de default (5) a 20 para concurrencia
    max_overflow=10,        # Permitir burst de conexiones
    pool_timeout=30,        # Timeout razonable
    pool_pre_ping=True,     # Health checks de conexiones
    future=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()

# Dependencia para FastAPI
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
