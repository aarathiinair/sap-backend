from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid
 
class EmailProcessingBase(BaseModel):
    email_id: uuid.UUID
    classification_result: str
    processed_at: datetime
    machine_details: str
    extracted_details: str
    category: str | None = None
    priority: str | None = None
    triggername: str | None = None
 
class EmailProcessingResponse(EmailProcessingBase):
    process_id: uuid.UUID
 
    model_config = ConfigDict(from_attributes=True)