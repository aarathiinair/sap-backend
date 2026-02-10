from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional
from app.models.certificates import CertificateStatus

class CertificateBase(BaseModel):
    certificate_name: str
    expiration_date: datetime
    description: Optional[str] = None
    usage: Optional[str] = None
    impacted_servers: Optional[str] = None
    responsible_group: str
    teams_channel: str

    @field_validator('expiration_date', mode='before')
    @classmethod
    def to_local_naive(cls, value):
        if isinstance(value, str):
            # Parse the string (handles 'Z' or '+00:00')
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            dt = value
        return dt.astimezone().replace(tzinfo=None, microsecond=0)

class CertificateCreate(CertificateBase):
    pass

class CertificateUpdate(BaseModel):
    certificate_name: Optional[str] = None
    expiration_date: Optional[datetime] = None
    description: Optional[str] = None
    usage: Optional[str] = None
    impacted_servers: Optional[str] = None
    responsible_group: Optional[str] = None
    teams_channel: Optional[str] = None

class CertificateResponse(CertificateBase):
    id: int
    status: CertificateStatus
    calculated_status: CertificateStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CertificateListResponse(BaseModel):
    items: List[CertificateResponse]
    total_rows: int
    page: int
    page_size: int