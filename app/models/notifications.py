from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True, nullable=False)
    text = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    read = Column(Boolean, nullable=False, default=False)
    user_id = Column(UUID(as_uuid=True))