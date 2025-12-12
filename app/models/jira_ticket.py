from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from sqlalchemy.orm import relationship
from app.db import Base
 
class JiraTicket(Base):
    __tablename__ = "jira_tickets"
 
    jira_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    jira_ticket_id = Column(String, nullable=False)
    machine = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    priority = Column(String, nullable=False)