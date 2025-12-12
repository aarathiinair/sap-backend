from sqlalchemy import Column, String, Boolean, PrimaryKeyConstraint # NEW IMPORT
from app.db import Base
 
class TriggerList(Base):
    __tablename__ = "trigger_list"
 
    triggername = Column(String, primary_key=True, nullable=False)
    category = Column(String, primary_key=True, nullable=False)
    actionable = Column(Boolean, nullable=False)
    priority = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('triggername', 'category'),
        {},
    )