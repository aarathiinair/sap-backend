from pydantic import BaseModel
from typing import List, Optional


class SapSystemBase(BaseModel):
    system_number: str
    system_id: Optional[str] = None
    system_name: Optional[str] = None
    system_role: Optional[str] = None
    deployment_model: Optional[str] = None
    installation_name: Optional[str] = None
    installation_number: Optional[str] = None
    software_product: Optional[str] = None
    priority_level: Optional[str] = None


class SapSystemCreate(SapSystemBase):
    pass


class SapSystemUpdate(BaseModel):
    system_id: Optional[str] = None
    system_name: Optional[str] = None
    system_role: Optional[str] = None
    deployment_model: Optional[str] = None
    installation_name: Optional[str] = None
    installation_number: Optional[str] = None
    software_product: Optional[str] = None
    priority_level: Optional[str] = None


class SapSystemResponse(SapSystemBase):
    class Config:
        from_attributes = True


class SapSystemListResponse(BaseModel):
    items: List[SapSystemResponse]
    total_rows: int
    page: int
    page_size: int