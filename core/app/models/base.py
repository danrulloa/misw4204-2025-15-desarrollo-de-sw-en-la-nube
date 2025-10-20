"""
Modelo base para todas las entidades del sistema
Incluye campos comunes: id, created_at, updated_at
"""
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from datetime import datetime
import uuid


def generate_uuid():
    """Genera un UUID como string para usar como ID primario"""
    return str(uuid.uuid4())


class BaseModel(Base):
    """
    Clase base abstracta para todos los modelos
    Proporciona id, created_at y updated_at automáticamente
    """
    __abstract__ = True
    
    # Llave primaria UUID
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    
    # Timestamps automáticos
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

