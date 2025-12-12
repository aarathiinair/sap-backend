from sqlalchemy import Column, String
from app.db import Base
 
class ErrorCodeMapping(Base):
    __tablename__ = "error_code_mapping"
 
    error_code = Column(String, primary_key=True, unique=True, nullable=False)
    machine = Column(String, nullable=False)
    description = Column(String, nullable=False)