from pydantic import BaseModel, ConfigDict
 
class ErrorCodeMappingBase(BaseModel):
    error_code: str
    machine: str
    description: str
 
class ErrorCodeMappingResponse(ErrorCodeMappingBase):
    model_config = ConfigDict(from_attributes=True)