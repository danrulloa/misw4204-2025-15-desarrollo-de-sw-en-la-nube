# app/db/base.py
from app.db.base_class import Base  # ahora solo importa Base, no la define

# Fuerza la importación de todos los modelos para que Alembic los vea
from app.db.models import user, group, permission, group_permissions, user_groups, user_permissions,refreshToken,session

