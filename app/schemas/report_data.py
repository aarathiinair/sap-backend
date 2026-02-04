from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Any, Dict

class ReportRequest(BaseModel):
    # Core Fields
    source: str = Field("ControlUp", description="The data source (e.g., ControlUp, Certificates).")
    start_date: datetime = Field(..., description="Start datetime for filtering (inclusive).")
    end_date: datetime = Field(..., description="End datetime for filtering (inclusive).")
    
    # ControlUp Specific Filters
    filter_type: Optional[str] = Field(None, description="Filter by Type (Actionable/Informational).")
    filter_priority: Optional[str] = Field(None, description="Filter by Priority.")
    
    # Certificates Specific Filters
    responsible_group: Optional[str] = Field(None, description="Filter by the group responsible for the certificate.")
    
    # Pagination & Sorting
    page: int = Field(1, ge=1, description="Page number for pagination.")
    page_size: int = Field(20, ge=1, le=100000, description="Number of items per page.")
    sort_by: Optional[str] = Field(None, description="Field to sort by. If None, handler defaults apply.")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc or desc).")

class ReportResponse(BaseModel):
    """
    Schema for the paginated report response. 
    'data' is now a list of dictionaries to allow for dynamic columns based on source.
    """
    data: List[Dict[str, Any]] 
    total_rows: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        from_attributes = True