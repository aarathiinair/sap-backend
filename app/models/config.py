from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.db import Base
 
class Config(Base):
    __tablename__ = "configuration"
 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    job_frequency = Column(Integer, nullable=False)
    outlook_email = Column(String, nullable=False)
    jira_base_url = Column(String, nullable=False)
    jira_api_token = Column(String, nullable=False)

class WebhookMapping(Base):
    __tablename__ = "webhook_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel_name = Column(String, nullable=False)
    webhook_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)