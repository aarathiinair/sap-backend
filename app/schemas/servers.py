from pydantic import BaseModel, Field
from typing import List

class ServerGroupResponse(BaseModel):
    """Schema for a single unique server group name."""
    group: str = Field(..., description="Unique name of the server group.")

class ServerComputernameResponse(BaseModel):
    """Schema for a single computer name."""
    computername: str = Field(..., description="Computer name within a group.")

class ServerGroupNameList(BaseModel):
    """Schema for a list of all unique server groups."""
    groups: List[str] = Field(..., description="List of all unique server group names.")