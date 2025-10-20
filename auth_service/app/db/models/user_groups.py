from sqlalchemy import Column, Table, ForeignKey
from app.db.base import Base

user_group_table = Table(
    "user_groups",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("group_id", ForeignKey("groups.id"), primary_key=True),
)