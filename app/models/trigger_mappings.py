from sqlalchemy import Column, String, DateTime,Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from sqlalchemy.orm import relationship
from app.db import Base

class TriggerMapping(Base):
    __tablename__ = "trigger_mappings"
   
    id = Column(Integer, primary_key=True, autoincrement=True)
    trigger_name = Column(String(500), nullable=False, index=True)
    category = Column(String(100), nullable=True)
    priority = Column(String(50), nullable=True)
    actionable = Column(String(50), nullable=True)
    recommended_action = Column(Text, nullable=True)
    jira_group = Column(String(255), nullable=True)
    team = Column(String(100), nullable=False, index=True)
    department = Column(String(100), nullable=True)
    responsible_persons = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<TriggerMapping(trigger='{self.trigger_name[:40]}...', team='{self.team}')>"

class TriggerCategory(Base):
    __tablename__ = "trigger_categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(100), nullable=False, unique=True, index=True)

    def __repr__(self):
        return f"<TriggerCategory(category='{self.category}')>"