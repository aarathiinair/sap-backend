from sqlalchemy import Column, String, DateTime,ForeignKey,Text,Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from app.db import Base
 

class SummaryTable(Base):
    __tablename__ = 'summary_table'
    
    # Foreign Key linking to RawEmails
    email_id = Column(String(64), ForeignKey('raw_emails.email_id', ondelete='CASCADE'), primary_key=True)
    summary = Column(Text, nullable=False, comment="Text Blob for the AI-generated summary")
    
    inserted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(Boolean, default=True, nullable=False, comment="Indicates if summarization was successful and sent to the queue")
    
    # Relationship to the parent RawEmail
    raw_email = relationship("RawEmail", back_populates="summary")
    
    def __repr__(self):
        return f"<SummaryTable(id='{self.email_id[:10]}...', summary_len={len(self.summary)})>"
