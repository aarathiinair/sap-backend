from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid
 
class EmailBase(BaseModel):
    subject: str
    body: str
    sender: str
    received_at: datetime
    inserted_at: datetime
    status: str
 
class EmailResponse(EmailBase):
    email_id: uuid.UUID
 
    model_config = ConfigDict(from_attributes=True)