from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, text
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Identidad / credenciales
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Perfil
    first_name = Column(String(100), nullable=False)
    last_name  = Column(String(100), nullable=False)
    country    = Column(String(100), nullable=True)
    city       = Column(String(100), nullable=True)

    # Estado / metadatos
    is_active  = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Multitenancy
    tenant_id  = Column(Integer, nullable=False, server_default=text("0"), index=True)

    # Relaciones
    sessions    = relationship("Session", back_populates="user")
    groups      = relationship("Group", secondary="user_groups", back_populates="users")
    permissions = relationship("Permission", secondary="user_permissions", back_populates="users")