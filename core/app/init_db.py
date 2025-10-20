"""Script para inicializar las tablas de la base de datos"""
from app.database import engine, Base
from app.models import Video, Vote  # noqa: F401

def init_db():
    """Crea todas las tablas en la base de datos"""
    print("Creando tablas en la base de datos...")
    print(f"Conectando a: {engine.url}")

    Base.metadata.create_all(bind=engine)

    print("Base de datos inicializada correctamente")
    print("Tablas creadas: videos, votes")


if __name__ == "__main__":
    init_db()

