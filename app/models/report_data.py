import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db import Base

class ReportData(Base):
    __tablename__ = "report_data"
    report_data_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_id = Column(UUID(as_uuid=True), ForeignKey('emails.email_id'), nullable=False)
    sender = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    received_at = Column(DateTime, nullable=False)
    type = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    jira_ticket = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=True)
    assigned_to = Column(String, nullable=True)

    email = relationship("Email", back_populates="report_entry", uselist=False)