from sqlalchemy import Column, String, DateTime,Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime , timezone 

class RawEmail(Base):
    __tablename__ = 'raw_emails'
    
    # Primary Key, generated from hash, CHAR(64) is efficient for SHA-256
    email_id = Column(String(64), primary_key=True, unique=True, index=True) 
    sender = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    email_path = Column(String, nullable=False, comment="Local path to the saved .msg file")
    
    # datetime objects should always be timezone-aware (using UTC)
    received_at = Column(DateTime(timezone=True), nullable=False)
    
    # Tracking for when the record was inserted
    inserted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(Boolean, default=True, nullable=False, comment="Indicates if the email is sent to the queue or not")
    
    # Relationships back to the processing tables (Lazy loading is default)
    segregation = relationship("SegregatedEmail", back_populates="raw_email", uselist=False, cascade="all, delete-orphan")
    segregation_prtg = relationship("SegregatedPRTGEmail", back_populates="raw_email", uselist=False, cascade="all, delete-orphan")
    segregation_imc = relationship("SegregatedIMCEmail", back_populates="raw_email", uselist=False, cascade="all, delete-orphan")
    segregation_microsoft = relationship("SegregatedMicrosoftEmail", back_populates="raw_email", uselist=False, cascade="all, delete-orphan")
    segregation_sap = relationship("SegregatedSAPEmail", back_populates="raw_email", uselist=False, cascade="all, delete-orphan")
    segregation_gms = relationship("SegregatedGMSEmail", back_populates="raw_email", uselist=False, cascade="all, delete-orphan")
    summary = relationship("SummaryTable", back_populates="raw_email", uselist=False, cascade="all, delete-orphan")
    jira_entry = relationship("JiraEntry", back_populates="raw_email", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RawEmail(id='{self.email_id[:10]}...', subject='{self.subject[:30]}')>"
