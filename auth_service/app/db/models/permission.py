from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

# La tabla intermedia group_permissions se define en `group.py`

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)

    users = relationship("User", secondary="user_permissions", back_populates="permissions", lazy="selectin")
    groups = relationship("Group", secondary="group_permissions", back_populates="permissions", lazy="selectin")
