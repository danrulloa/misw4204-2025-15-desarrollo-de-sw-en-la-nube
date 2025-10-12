"""
Configuración de la conexión a la base de datos PostgreSQL
Módulo temporal - será reemplazado por Frans con integración de Alembic
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Crear engine de conexión a PostgreSQL
# pool_pre_ping=True valida las conexiones antes de usarlas
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Crear session factory para manejar transacciones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para los modelos ORM
Base = declarative_base()


def get_db():
    """
    Dependencia que proporciona una sesión de base de datos para FastAPI
    Se encarga de abrir y cerrar la sesión automáticamente
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

