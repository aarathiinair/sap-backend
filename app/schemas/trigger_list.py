from pydantic import BaseModel, ConfigDict
from typing import Optional

class TriggerMappingBase(BaseModel):
    trigger_name: str
    category: Optional[str] = None
    priority: Optional[str] = None
    actionable: Optional[str] = None
    jira_group: Optional[str] = None
    recommended_action: Optional[str] = None
    team: str
    department: Optional[str] = None
    responsible_persons: Optional[str] = None

class TriggerMappingCreate(TriggerMappingBase):
    pass

class TriggerMappingUpdate(BaseModel):
    trigger_name: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    actionable: Optional[str] = None
    jira_group: Optional[str] = None
    recommended_action: Optional[str] = None
    team: Optional[str] = None
    department: Optional[str] = None
    responsible_persons: Optional[str] = None

class TriggerMappingResponse(TriggerMappingBase):
    id: int
    model_config = ConfigDict(from_attributes=True)