from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decorators import log_function_call
from app.db import get_db
from app.models import TriggerList
from app.schemas import TriggerListBase as TriggerCreate, TriggerUpdate, TriggerListResponse as TriggerResponse
from app.auth_utils import verify_token
 
router = APIRouter(prefix="/triggers", tags=["triggers"])

@router.post("/", response_model=TriggerResponse)
@log_function_call
def create_trigger(
    request: TriggerCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(verify_token)
):
    if payload.get("role") not in ["Admin", "Super Admin"]:
        raise HTTPException(status_code=403, detail="Not allowed")
    
    exists = (
        db.query(TriggerList)
        .filter(
            TriggerList.triggername == request.triggername,
            TriggerList.category == request.category,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Trigger already exists")
 
    new_trigger = TriggerList(**request.dict())
    db.add(new_trigger)
    db.commit()
    db.refresh(new_trigger)
    return new_trigger
 
@router.get("/", response_model=list[TriggerResponse])
@log_function_call
def get_triggers(db: Session = Depends(get_db), payload: dict = Depends(verify_token)):
    return db.query(TriggerList).all()
 
@router.get("/{trigger_name}/{category}", response_model=TriggerResponse)
@log_function_call
def get_trigger(
    trigger_name: str,
    category: str,
    db: Session = Depends(get_db),
    payload: dict = Depends(verify_token)
):
    trigger = (
        db.query(TriggerList)
        .filter(
            TriggerList.triggername == trigger_name,
            TriggerList.category == category,
        )
        .first()
    )
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    return trigger
 
@router.put("/{trigger_name}/{category}", response_model=TriggerResponse)
@log_function_call
def update_trigger(
    trigger_name: str,
    category: str,
    request: TriggerUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(verify_token)
):
    if payload.get("role") not in ["Admin", "Super Admin"]:
        raise HTTPException(status_code=403, detail="Not allowed")
 
    trigger = (
        db.query(TriggerList)
        .filter(
            TriggerList.triggername == trigger_name,
            TriggerList.category == category,
        )
        .first()
    )
 
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
 
    for field, value in request.dict(exclude_unset=True).items():
        setattr(trigger, field, value)
 
    db.commit()
    db.refresh(trigger)
    return trigger