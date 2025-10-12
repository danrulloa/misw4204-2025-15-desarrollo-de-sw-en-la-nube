from sqlalchemy import Column, Table, ForeignKey
from app.db.base import Base


group_permission_table = Table(
    "group_permissions",
    Base.metadata,
    Column("group_id", ForeignKey("groups.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)
