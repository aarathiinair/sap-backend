from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from app.db import Base

class SegregatedIMCEmail(Base):
    __tablename__ = 'segregated_imc_email'
    
    # Foreign Key linking to RawEmails
    email_id = Column(String(64), ForeignKey('raw_emails.email_id', ondelete='CASCADE'), primary_key=True)
    priority = Column(String(50), nullable=True)
    type = Column(String(50), nullable=True)
    device = Column(String(255), nullable=True)

    inserted_at = Column(DateTime(timezone=False), default=lambda: datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[0:23], '%Y-%m-%d %H:%M:%S.%f'), nullable=False)
    status = Column(Boolean, default=True, nullable=False, comment="Indicates if segregation was successful and sent to the queue")
    
    # Relationship to the parent RawEmail
    raw_email = relationship("RawEmail", back_populates="segregation_imc")
    
    def __repr__(self):
        return f"<SegregatedIMCEmail(id='{self.email_id[:10]}...', type='{self.type}')>"