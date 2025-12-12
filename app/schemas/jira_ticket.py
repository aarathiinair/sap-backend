from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid
 
class JiraTicketBase(BaseModel):
    jira_ticket_id: str
    machine: str
    created_at: datetime
    priority: str
 
class JiraTicketResponse(JiraTicketBase):
    jira_id: uuid.UUID
 
    model_config = ConfigDict(from_attributes=True)