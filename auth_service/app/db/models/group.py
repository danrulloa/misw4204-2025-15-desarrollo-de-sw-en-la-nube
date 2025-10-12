from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    users = relationship("User", secondary="user_groups", back_populates="groups", lazy="selectin")
    permissions = relationship("Permission",secondary="group_permissions", back_populates="groups", lazy="selectin")
