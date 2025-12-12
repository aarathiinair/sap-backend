from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserResponse
 
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
 
    model_config = ConfigDict(from_attributes=True)
 
class LoginRequest(BaseModel):
    username: str
    password: str
 