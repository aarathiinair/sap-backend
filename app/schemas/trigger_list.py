from pydantic import BaseModel, ConfigDict
 
class TriggerListBase(BaseModel):
    triggername: str
    category: str
    actionable: bool
    priority: str
    enabled: bool
 
class TriggerUpdate(BaseModel):
    triggername: str | None = None
    category: str | None = None
    actionable: bool | None = None
    priority: str | None = None
    enabled: bool | None = None
 
class TriggerListResponse(TriggerListBase):
    model_config = ConfigDict(from_attributes=True)