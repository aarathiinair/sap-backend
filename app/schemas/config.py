from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid
 
class ConfigBase(BaseModel):
    user_id: uuid.UUID
    created_at: datetime
    job_frequency: int
    outlook_email: str
    jira_base_url: str
    jira_api_token: str
    teams_webhook: str
 
class ConfigUpdate(BaseModel):
    job_frequency: int | None = None
    outlook_email: str | None = None
    jira_base_url: str | None = None
    jira_api_token: str | None = None
    teams_webhook: str | None = None
 
class ConfigResponse(ConfigBase):
    id: uuid.UUID
 
    model_config = ConfigDict(from_attributes=True)