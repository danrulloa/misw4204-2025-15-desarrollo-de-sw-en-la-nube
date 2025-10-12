from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime,timezone

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False) 
    created_at = Column(DateTime(timezone=True),default=datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True),default=datetime.now(timezone.utc), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    session = relationship("Session", back_populates="refresh_tokens")
