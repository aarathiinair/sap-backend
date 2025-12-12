from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.db import Base
 
class DuplicateEmail(Base):
    __tablename__ = "duplicate_emails"
 
    email_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(String, nullable=False)
    sender = Column(String, nullable=False)
    received_at = Column(DateTime, nullable=False)
    inserted_at = Column(DateTime, nullable=False)