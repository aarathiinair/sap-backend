from datetime import datetime
from typing import Optional

from app.db import Base
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, event
from sqlalchemy.orm import Mapped, relationship
 
import enum

def get_utc_now_no_micro():
    return datetime.utcnow().replace(microsecond=0)

class MaintenanceStatus(enum.Enum):
    SCHEDULED = "Scheduled"
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
 
class Maintenance(Base):
    __tablename__ = "maintenance_windows"
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    server_group: Mapped[str] = Column(String, nullable=False)
    server_name: Mapped[Optional[str]] = Column(String, nullable=True)
    other_server: Mapped[Optional[str]] = Column(String, nullable=True)
    comments: Mapped[Optional[str]] = Column(String, nullable=True)
    start_datetime: Mapped[datetime] = Column(DateTime, nullable=False)
    end_datetime: Mapped[datetime] = Column(DateTime, nullable=False)
    status: Mapped[str] = Column(SQLEnum(MaintenanceStatus), 
                                     default=MaintenanceStatus.SCHEDULED, 
                                     nullable=False)
    
    created_at: Mapped[datetime] = Column(DateTime, default=get_utc_now_no_micro, nullable=False)
    updated_at: Mapped[datetime] = Column(DateTime, default=get_utc_now_no_micro, onupdate=get_utc_now_no_micro, nullable=False)
 
    def __repr__(self):
        return f"<Maintenance(id={self.id}, group='{self.server_group}', server='{self.server_name}', status='{self.status}')>"
 
@event.listens_for(Maintenance, 'load')
def update_maintenance_status(target, context):
    now = datetime.utcnow()
    
    if target.status == MaintenanceStatus.COMPLETED.value:
        return 
        
    if target.start_datetime <= now and target.end_datetime >= now:
        target.status = MaintenanceStatus.ONGOING.value
    elif target.end_datetime < now:
        target.status = MaintenanceStatus.COMPLETED.value
    elif target.start_datetime > now:
        target.status = MaintenanceStatus.SCHEDULED.value