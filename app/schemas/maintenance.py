from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional
from app.models.maintenance import MaintenanceStatus

class MaintenanceBase(BaseModel):
    server_group: str = Field(..., description="The selected server group name (or 'Other').")
    comments: Optional[str] = Field(None, description="Additional comments or notes.")
    start_datetime: datetime = Field(..., description="Scheduled start date and time (UTC).")
    end_datetime: datetime = Field(..., description="Scheduled end date and time (UTC).")
    
    @field_validator('start_datetime', 'end_datetime', mode='before')
    @classmethod
    def strip_microseconds(cls, value):
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value.replace(microsecond=0)

# --- CREATE ---
class MaintenanceCreate(MaintenanceBase):
    servers: List[str] = Field(..., description="List of selected computer names.")
    other_server: Optional[str] = Field(None, description="Manual entry if 'Other' is selected.")

# --- UPDATE ---
class MaintenanceUpdate(BaseModel):
    server_group: Optional[str] = None
    server_name: Optional[str] = None
    other_server: Optional[str] = None
    comments: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    status: Optional[MaintenanceStatus] = None

# --- RESPONSE (Output to Frontend) ---
class MaintenanceResponse(MaintenanceBase):
    id: int
    server_name: Optional[str] = None 
    other_server: Optional[str] = None
    
    status: MaintenanceStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# --- LIST RESPONSE ---
class MaintenanceListResponse(BaseModel):
    items: List[MaintenanceResponse]
    total_rows: int
    page: int
    page_size: int