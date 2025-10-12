from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(f"DATABASE_URL no está definida o es vacía. Valor recibido: {repr(DATABASE_URL)}")


# Crear motor asincrónico
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependencia para usar en FastAPI o scripts
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Inicializar la BD (crear tablas)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Cierre del engine (útil en shutdown de FastAPI)
async def close_db():
    await engine.dispose()
