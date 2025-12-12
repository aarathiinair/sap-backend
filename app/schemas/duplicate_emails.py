from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid
 
class DuplicateEmailBase(BaseModel):
    subject: str
    body: str
    sender: str
    received_at: datetime
    inserted_at: datetime
 
class DuplicateEmailResponse(DuplicateEmailBase):
    email_id: uuid.UUID
 
    model_config = ConfigDict(from_attributes=True)