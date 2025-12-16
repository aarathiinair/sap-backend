from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
import httpx

from app.db import get_db
from app.models.config import Config
from app.models.notifications import Notification
from app.schemas.config import ConfigUpdate, ConfigResponse
from app.auth_utils import verify_token
from datetime import datetime
from decorators import log_function_call
import uuid

router = APIRouter(prefix="/parameters", tags=["parameters"])

API_BASE_URL = "http://127.0.0.1:8000" 

def get_interval_config(frequency_value: int) -> tuple[str, int]:
    """Returns the config unit and value based on numeric frequency."""
    config_unit = "minutes"
    return config_unit, frequency_value

async def call_update_interval_api(frequency_value: int):
    """
    Asynchronously calls the /config/interval API endpoint on :8000.
    """
    
    config_unit, config_value = get_interval_config(frequency_value)
    payload = {"unit": config_unit, "value": config_value}
    
    async with httpx.AsyncClient(base_url=API_BASE_URL) as client:
        try:
            response = await client.put(
                "/config/interval",
                json=payload
            )
            response.raise_for_status() 
            print(f"Scheduler update successful: {response.json()}")
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Scheduler API returned error: {e.response.text}")
            raise HTTPException(status_code=503, detail=f"Scheduler update API failed: {e.response.text}")
        except httpx.RequestError as e:
            print(f"Error connecting to Scheduler API on {API_BASE_URL}: {e}")
            raise HTTPException(status_code=503, detail="Could not connect to the Scheduler service.")

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
async def create_parameters(
    request: ConfigUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(verify_token),
):
    if payload.get("role") not in ["Admin", "Super Admin"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    new_job_frequency = request.job_frequency if isinstance(request.job_frequency, int) else None
    
    new_config = Config(
        id=uuid.uuid4(),
        user_id=uuid.UUID(payload.get("sub")),
        created_at=datetime.utcnow(),
        job_frequency=new_job_frequency, 
        outlook_email=request.outlook_email or "",
        jira_base_url=request.jira_base_url or "",
        jira_api_token=request.jira_api_token or "",
        teams_webhook=request.teams_webhook or "",
    )

    current_config = await run_in_threadpool(
        db.query(Config).order_by(Config.created_at.desc()).first
    )
    
    current_job_frequency = current_config.job_frequency if current_config else None

    if (new_job_frequency is not None) and (new_job_frequency != current_job_frequency):
        
        if new_job_frequency <= 0:
            raise HTTPException(status_code=400, detail="Job frequency must be a positive number.")
            
        try:
            await call_update_interval_api(new_job_frequency) 
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update scheduler: {str(e)}")

    def save_config(db_session, config_object):
        db_session.add(config_object)
        db_session.commit()
        db_session.refresh(config_object)
        return config_object

    final_config = await run_in_threadpool(save_config, db, new_config)
    
    return final_config