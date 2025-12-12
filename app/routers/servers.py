from fastapi import APIRouter, Depends, Query, status, HTTPException
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct
from decorators import log_function_call

from app.db import get_db
from app.models.servers import Server
from app.schemas.servers import ServerGroupNameList, ServerComputernameResponse

router = APIRouter(
    prefix="/servers",
    tags=["Server Data"],
)

# --- GET Unique Groups ---
@router.get("/groups", response_model=ServerGroupNameList)
@log_function_call
def get_unique_server_groups(db: Session = Depends(get_db)):
    """
    Retrieves a list of all unique server group names from the 'servers' table.
    """
    try:
        stmt = select(distinct(Server.group)).order_by(Server.group)
        groups = db.execute(stmt).scalars().all()
        return {"groups": groups}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve server groups: {e}"
        )

# --- GET Computer Names by Group ---
@router.get("/by_group", response_model=List[ServerComputernameResponse])
@log_function_call
def get_computer_names_by_group(
    group_name: str = Query(..., description="The name of the server group to filter by."),
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of all computer names belonging to a specific group.
    """
    if not group_name:
        return []
    
    try:
        stmt = select(Server.computername).where(Server.group == group_name).order_by(Server.computername)
        computernames = db.execute(stmt).scalars().all()
        
        # Map to the response schema (needed for FastAPI response_model validation)
        response_data = [{"computername": name} for name in computernames]
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve computer names for group '{group_name}': {e}"
        )