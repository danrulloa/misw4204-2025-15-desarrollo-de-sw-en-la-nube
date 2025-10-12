from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy import create_engine
from alembic import context

from app.db.base import Base  # importa tus modelos aquí
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata para autogenerar
target_metadata = Base.metadata

def get_url():
    url = os.getenv("ALEMBIC_DATABASE_URL")
    if not url:
        raise RuntimeError("ALEMBIC_DATABASE_URL no está definida")
    return url

def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = create_engine(
        get_url(),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
