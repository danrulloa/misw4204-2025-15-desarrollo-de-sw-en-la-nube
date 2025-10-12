from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, func, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime,timezone

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(Text, nullable=False)  # antes era String(255)
    refresh_token = Column(Text, nullable=False)  # antes era String(255)
    session_expires_at = Column(DateTime(timezone=True),default=datetime.now(timezone.utc), nullable=False)
    refresh_expires_at = Column(DateTime(timezone=True),default=datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="sessions")
    refresh_tokens = relationship("RefreshToken", back_populates="session", cascade="all, delete-orphan")
