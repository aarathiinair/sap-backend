from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from decorators import log_function_call
import uuid
from app.db import get_db
from app.models.notifications import Notification
from app.auth_utils import verify_token
from app.schemas.notifications import NotificationResponse 

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Helper function to convert DB model to Pydantic response, including timeAgo calculation
def create_notification_response(notification: Notification) -> NotificationResponse:
    time_diff = datetime.utcnow() - notification.timestamp
    time_ago = ""
    if time_diff.total_seconds() < 60:
        time_ago = f"{int(time_diff.total_seconds())} seconds ago"
    elif time_diff.total_seconds() < 3600:
        time_ago = f"{int(time_diff.total_seconds() / 60)} minutes ago"
    elif time_diff.total_seconds() < 86400:
        time_ago = f"{int(time_diff.total_seconds() / 3600)} hours ago"
    else:
        time_ago = f"{int(time_diff.total_seconds() / 86400)} days ago"

    return NotificationResponse(
        id=notification.id,
        message=notification.text,
        timeAgo=time_ago,
        read=notification.read
    )

@router.get("/", response_model=List[NotificationResponse])
@log_function_call
def get_user_notifications(db: Session = Depends(get_db), payload: dict = Depends(verify_token)):
    user_id_str = payload.get("sub")
    
    # Convert string to UUID for the DB query
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        # Fallback if the sub isn't a standard UUID
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id_str)

    notifications = db.query(Notification).filter(
        Notification.user_id == user_uuid, # Use the UUID object here
        Notification.read == False
    ).order_by(Notification.timestamp.desc()).all()
    
    return [create_notification_response(n) for n in notifications]


@router.delete("/{notification_id}")
@log_function_call
def dismiss_notification(notification_id: int, db: Session = Depends(get_db), payload: dict = Depends(verify_token)):
    user_id = payload.get("sub")
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id, 
        Notification.user_id == user_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found or access denied")

    notification.read = True
    db.commit()
    
    return {"message": "Notification dismissed successfully"}