# app/routers/webhooks.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db import get_db
from app.models.config import WebhookMapping
from app.schemas.config import WebhookBase, WebhookResponse
from app.auth_utils import verify_token
import uuid
from typing import List

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.get("/", response_model=list[WebhookResponse])
async def get_webhooks(db: Session = Depends(get_db), payload: dict = Depends(verify_token)):
    return db.query(WebhookMapping).all()

@router.get("/channels", response_model=List[str])
def get_channel_names(db: Session = Depends(get_db)):
    # Returns a simple list of strings for the dropdown
    stmt = select(WebhookMapping.channel_name).order_by(WebhookMapping.channel_name)
    channels = db.execute(stmt).scalars().all()
    return channels

@router.post("/", response_model=WebhookResponse)
async def create_webhook(mapping: WebhookBase, db: Session = Depends(get_db), payload: dict = Depends(verify_token)):
    new_map = WebhookMapping(
        id=uuid.uuid4(),
        channel_name=mapping.channel_name,
        webhook_url=mapping.webhook_url
    )
    db.add(new_map)
    db.commit()
    db.refresh(new_map)
    return new_map

@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(webhook_id: uuid.UUID, mapping: WebhookBase, db: Session = Depends(get_db), payload: dict = Depends(verify_token)):
    db_map = db.query(WebhookMapping).filter(WebhookMapping.id == webhook_id).first()
    if not db_map:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    db_map.channel_name = mapping.channel_name
    db_map.webhook_url = mapping.webhook_url
    db.commit()
    db.refresh(db_map)
    return db_map

@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(webhook_id: uuid.UUID, db: Session = Depends(get_db), payload: dict = Depends(verify_token)):
    db_map = db.query(WebhookMapping).filter(WebhookMapping.id == webhook_id).first()
    if not db_map:
        raise HTTPException(status_code=404, detail="Mapping not found")
    db.delete(db_map)
    db.commit()
    return None