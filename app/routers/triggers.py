from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.trigger_mappings import TriggerMapping, TriggerCategory
from app.schemas.trigger_list import TriggerMappingCreate, TriggerMappingUpdate, TriggerMappingResponse

router = APIRouter(prefix="/triggers", tags=["triggers"])

def sync_category(category_name: str, db: Session):
    """Helper to add category to trigger_categories if it doesn't exist."""
    if not category_name:
        return
    
    exists = db.query(TriggerCategory).filter(TriggerCategory.category == category_name).first()
    if not exists:
        new_cat = TriggerCategory(category=category_name)
        db.add(new_cat)
        db.flush()

@router.get("/", response_model=list[TriggerMappingResponse])
def get_triggers(db: Session = Depends(get_db)):
    return db.query(TriggerMapping).all()

@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return db.query(TriggerCategory).all()

@router.post("/", response_model=TriggerMappingResponse)
def create_trigger(request: TriggerMappingCreate, db: Session = Depends(get_db)):
    if request.category:
        sync_category(request.category, db)

    new_trigger = TriggerMapping(**request.model_dump())
    db.add(new_trigger)
    db.commit()
    db.refresh(new_trigger)
    return new_trigger

@router.put("/{trigger_id}", response_model=TriggerMappingResponse)
def update_trigger(trigger_id: int, request: TriggerMappingUpdate, db: Session = Depends(get_db)):
    trigger = db.query(TriggerMapping).filter(TriggerMapping.id == trigger_id).first()
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    if "category" in data and data["category"]:
        sync_category(data["category"], db)

    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(trigger, field, value)
    
    db.commit()
    db.refresh(trigger)
    return trigger

@router.delete("/{trigger_id}")
def delete_trigger(trigger_id: int, db: Session = Depends(get_db)):
    trigger = db.query(TriggerMapping).filter(TriggerMapping.id == trigger_id).first()
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    db.delete(trigger)
    db.commit()
    return Response(status_code=204)