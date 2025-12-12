from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid
 
class UserBase(BaseModel):
    username: str
    email_id: str
    role: str
 
class UserCreate(UserBase):
    username: str
    email_id: str
    role: str
 
class UserUpdate(BaseModel):
    email_id: str | None = None
    role: str | None = None
 
class UserUpdatePassword(BaseModel):
    current_password: str
    new_password: str

class UserResponse(BaseModel):
    user_id: uuid.UUID
    username: str
    email_id: str
    role: str
    created_at: datetime
    created_by: str
    plain_password: str | None = None   # only filled for SuperAdmins
 
    model_config = ConfigDict(from_attributes=True)