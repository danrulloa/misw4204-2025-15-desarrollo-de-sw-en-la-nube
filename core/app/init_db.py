"""
Script para inicializar las tablas de la base de datos
Crea todas las tablas definidas en los modelos SQLAlchemy

Uso: python -m app.init_db
"""
from app.database import engine, Base
from app.models import User, Video, Vote

def init_db():
    """
    Crea todas las tablas en la base de datos PostgreSQL
    Si las tablas ya existen, no hace nada
    """
    print("Creando tablas en la base de datos...")
    print(f"Conectando a: {engine.url}")
    
    # Importar todos los modelos antes de crear las tablas
    # Esto asegura que Base.metadata tenga todos los modelos registrados
    Base.metadata.create_all(bind=engine)
    
    print("Base de datos inicializada correctamente")
    print("Tablas creadas: users, videos, votes")


if __name__ == "__main__":
    init_db()

