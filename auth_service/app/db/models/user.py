from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    tenant_id = Column(Integer, nullable=False, index=True)

    sessions = relationship("Session", back_populates="user")
    groups = relationship("Group", secondary="user_groups", back_populates="users")
    permissions = relationship("Permission", secondary="user_permissions", back_populates="users")
