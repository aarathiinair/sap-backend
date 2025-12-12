from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from app.db import Base
 

class SegregatedEmail(Base):
    __tablename__ = 'segregated_email'
    
    # Foreign Key linking to RawEmails
    email_id = Column(String(64), ForeignKey('raw_emails.email_id', ondelete='CASCADE'), primary_key=True)
    priority = Column(String(50), nullable=True) # e.g., 'High', 'Medium', 'Low'
    type = Column(String(50), nullable=True)     # e.g., 'Alert', 'Notification', 'Info'
    resource_name = Column(String(255), nullable=True)
    trigger_name = Column(String(255), nullable=True)
    
    inserted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(Boolean, default=True, nullable=False, comment="Indicates if segregation was successful and sent to the queue")
    
    # Relationship to the parent RawEmail
    raw_email = relationship("RawEmail", back_populates="segregation")
    
    def __repr__(self):
        return f"<SegregatedEmail(id='{self.email_id[:10]}...', type='{self.type}')>"
