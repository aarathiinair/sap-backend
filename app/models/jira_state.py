from datetime import datetime, timedelta
from typing import Optional
import enum

from sqlalchemy import Column, Integer, String, DateTime

from app.db import Base

class JiraState(Base):
    __tablename__ = 'jira_state'
    
    jira_ticket_id = Column(String, primary_key=True)
    certificate_name = Column(String, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    ticket_created_on = Column(DateTime, default=datetime.utcnow)