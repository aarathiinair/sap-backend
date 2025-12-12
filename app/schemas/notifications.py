from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
import uuid

class NotificationBase(BaseModel):
    text: str

class NotificationCreate(NotificationBase):
    user_id: uuid.UUID

class NotificationResponse(BaseModel):
    id: int
    message: str
    timeAgo: str
    read: bool
    
    model_config = ConfigDict(from_attributes=True)

class NotificationStatusUpdate(BaseModel):
    read: bool