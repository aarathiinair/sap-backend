from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List, Optional
import uuid

class ReportRequest(BaseModel):
    start_date: datetime = Field(..., description="Start datetime for filtering (inclusive).")
    end_date: datetime = Field(..., description="End datetime for filtering (inclusive).")
    filter_type: Optional[str] = Field(None, description="Filter by Type (Actionable/Informational).")
    filter_priority: Optional[str] = Field(None, description="Filter by Priority (High/Medium/Low).")
    page: int = Field(1, ge=1, description="Page number for pagination.")
    page_size: int = Field(10, ge=1, le=100000, description="Number of items per page.")
    sort_by: Optional[str] = Field("received_at", description="Field to sort by (e.g., received_at, type, priority, timestamp).")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc or desc).")

class ReportDataRow(BaseModel):
    email_id: uuid
    sender: str
    subject: str
    received_at: datetime
    type: str
    priority: str
    jiraticket_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    assigned_to: Optional[str] = None
    teams_channel: Optional[str] = None
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
 
class ReportResponse(BaseModel):
    """Schema for the paginated report response."""
    data: List[ReportDataRow]
    total_rows: int
    page: int
    page_size: int
    total_pages: int