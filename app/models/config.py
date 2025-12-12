from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.db import Base
 
class Config(Base):
    __tablename__ = "configuration"
 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    job_frequency = Column(Integer, nullable=False)
    outlook_email = Column(String, nullable=False)
    jira_base_url = Column(String, nullable=False)
    jira_api_token = Column(String, nullable=False)
    teams_webhook = Column(String, nullable=False)
 
    # relationship
    user = relationship("User", back_populates="configs")