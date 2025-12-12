from sqlalchemy import Column, String, DateTime, BigInteger,ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime,timezone
from sqlalchemy.orm import relationship
from app.db import Base
 

class JiraEntry(Base):
    __tablename__ = 'jira_table'
    
    # Auto-incrementing Primary Key
    jira_id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign Key linking to RawEmails
    email_id = Column(String(64), ForeignKey('raw_emails.email_id', ondelete='CASCADE'), nullable=False, index=True)
    
    jiraticket_id = Column(String(50), unique=True, nullable=False) # e.g., 'PROJ-1234'
    assigned_to = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, comment="JIRA creation time")
    
    inserted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationship to the parent RawEmail
    raw_email = relationship("RawEmail", back_populates="jira_entry")
    
    def __repr__(self):
        return f"<JiraEntry(id='{self.jira_id}', ticket='{self.jiraticket_id}')>"
