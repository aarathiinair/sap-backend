from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.config import Config
from app.models.notifications import Notification
from app.schemas.config import ConfigUpdate, ConfigResponse
from app.auth_utils import verify_token
from datetime import datetime
from decorators import log_function_call
import uuid
 
router = APIRouter(prefix="/parameters", tags=["parameters"])
 
 
@router.get("/", response_model=ConfigResponse)
@log_function_call
def get_parameters(db: Session = Depends(get_db), payload: dict = Depends(verify_token)):
    if payload.get("role") not in ["Super Admin"]:
        raise HTTPException(status_code=403, detail="Not allowed")
    
    user_id = uuid.UUID(payload.get("sub"))
    username = payload.get("username")
 
    config = db.query(Config).order_by(Config.created_at.desc()).first()
    if not config:
        config = Config(
            id=uuid.uuid4(),
            user_id=user_id,
            created_at=datetime.utcnow(),
            job_frequency=10,
            outlook_email="",
            jira_base_url="",
            jira_api_token="",
            teams_webhook="",
        )
        db.add(config)

        notification_text = f"Configuration updated by {username}."

        new_notification = Notification(
            user_id=user_id,
            text=notification_text,
            timestamp=datetime.utcnow(),
            read=False
        )
        db.add(new_notification)

        db.commit()
        db.refresh(config)
 
    return config
 
 
@router.post("/", response_model=ConfigResponse)
@log_function_call
def create_parameters(
    request: ConfigUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(verify_token),
):
    if payload.get("role") not in ["Admin", "Super Admin"]:
        raise HTTPException(status_code=403, detail="Not allowed")
 
    new_config = Config(
        id=uuid.uuid4(),
        user_id=uuid.UUID(payload.get("sub")),
        created_at=datetime.utcnow(),
        job_frequency=request.job_frequency or "",
        outlook_email=request.outlook_email or "",
        jira_base_url=request.jira_base_url or "",
        jira_api_token=request.jira_api_token or "",
        teams_webhook=request.teams_webhook or "",
    )
 
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    return new_config