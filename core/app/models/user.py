"""
Modelo de Usuario/Jugador
Almacena la información de los jugadores registrados en la plataforma ANB
"""
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class User(BaseModel):
    """
    Modelo de usuario/jugador
    Representa a los jugadores aficionados que participan en ANB Rising Stars
    """
    __tablename__ = "users"
    
    # Campos de autenticación y perfil (usados por Frans para login/signup)
    username = Column(String(100), unique=True, nullable=False, index=True)  # Elegido por el usuario
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # Contraseña hasheada
    
    # Información personal del jugador
    first_name = Column(String(100), nullable=False)  # Nombre del jugador
    last_name = Column(String(100), nullable=False)   # Apellido del jugador
    city = Column(String(100), nullable=False, index=True)  # Para filtros de ranking
    country = Column(String(100), nullable=False)  # País del jugador
    
    # Relaciones con otras tablas
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def full_name(self):
        """Retorna el nombre completo del jugador"""
        return f"{self.first_name} {self.last_name}"

