from sqlalchemy import Column, Table, ForeignKey
from app.db.base import Base


user_permission_table = Table(
    "user_permissions",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)
