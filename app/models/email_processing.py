from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from sqlalchemy.orm import relationship
from app.db import Base
 
class EmailProcessing(Base):
    __tablename__ = "email_processing"
 
    process_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.email_id"), nullable=False)
    classification_result = Column(String, nullable=False)
    processed_at = Column(DateTime, nullable=False)
    machine_details = Column(String, nullable=False)
    extracted_details = Column(String, nullable=False)
    category = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    triggername = Column(String, nullable=True)

    email = relationship("Email", back_populates="processing_records")