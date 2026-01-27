import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
import httpx

from app.db import get_db
from app.models.config import Config
from app.models.notifications import Notification
from app.schemas.config import ConfigUpdate, ConfigResponse
from app.auth_utils import verify_token
from decorators import log_function_call

router = APIRouter(prefix="/parameters", tags=["parameters"])

API_BASE_URL = "http://127.0.0.1:8000"

def get_interval_config(frequency_value: int) -> tuple[str, int]:
    """Returns the config unit and value based on numeric frequency."""
    return "minutes", frequency_value

async def call_update_interval_api(frequency_value: int):
    """Asynchronously updates the Scheduler service interval."""
    config_unit, config_value = get_interval_config(frequency_value)
    payload = {"unit": config_unit, "value": config_value}
    
    async with httpx.AsyncClient(base_url=API_BASE_URL) as client:
        try:
            response = await client.put("/config/interval", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=503, detail=f"Scheduler update failed: {e.response.text}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to the Scheduler service.")

def get_uuid_from_sub(sub: str) -> uuid.UUID:
    """Converts string sub to UUID, using uuid5 fallback for non-standard SSO IDs."""
    try:
        return uuid.UUID(sub)
    except (ValueError, TypeError):
        # Fallback for Azure/OIDC strings that aren't native UUIDs
        return uuid.uuid5(uuid.NAMESPACE_DNS, sub)

@router.get("/", response_model=ConfigResponse)
@log_function_call
def get_parameters(db: Session = Depends(get_db), payload: dict = Depends(verify_token)):
    user_id = get_uuid_from_sub(payload.get("sub"))
    username = payload.get("username", "Unknown User")
    
    config = db.query(Config).order_by(Config.created_at.desc()).first()
    
    if not config:
        # Create default configuration if none exists
        config = Config(
            id=uuid.uuid4(),
            user_id=user_id,
            created_at=datetime.utcnow(),
            job_frequency=10, 
            outlook_email="",
            jira_base_url="",
            jira_api_token=""
            # teams_webhook removed
        )
        db.add(config)

        # Log initial creation in notifications
        new_notification = Notification(
            user_id=user_id,
            text=f"System initialized with default configuration by {username}.",
            timestamp=datetime.utcnow(),
            read=False
        )
        db.add(new_notification)
        db.commit()
        db.refresh(config)
    
    return config

@router.post("/", response_model=ConfigResponse)
@log_function_call
async def create_parameters(
    request: ConfigUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(verify_token),
):
    user_id = get_uuid_from_sub(payload.get("sub"))
    username = payload.get("username", "Unknown User")

    new_job_frequency = request.job_frequency
    
    # 1. Fetch current config to check for frequency changes
    current_config = await run_in_threadpool(
        db.query(Config).order_by(Config.created_at.desc()).first
    )
    current_freq = current_config.job_frequency if current_config else None

    # 2. Handle Scheduler API update if frequency changed
    if new_job_frequency is not None and new_job_frequency != current_freq:
        if new_job_frequency <= 0:
            raise HTTPException(status_code=400, detail="Frequency must be a positive number.")
        await call_update_interval_api(new_job_frequency)

    # 3. Prepare new config object
    new_config = Config(
        id=uuid.uuid4(),
        user_id=user_id,
        created_at=datetime.utcnow(),
        job_frequency=new_job_frequency, 
        outlook_email=request.outlook_email or "",
        jira_base_url=request.jira_base_url or "",
        jira_api_token=request.jira_api_token or ""
    )

    # 4. Save and create notification
    def save_and_notify(db_session):
        db_session.add(new_config)
        
        notification = Notification(
            user_id=user_id,
            text=f"Configuration parameters updated by {username}.",
            timestamp=datetime.utcnow(),
            read=False
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(new_config)
        return new_config

    final_config = await run_in_threadpool(save_and_notify, db)
    return final_config