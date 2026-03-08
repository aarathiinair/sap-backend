from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional
from decorators import log_function_call

from app.db import get_db
from app.models.sap_system_priority import SapSystemPriority
from app.schemas.sap_system import SapSystemCreate, SapSystemUpdate, SapSystemResponse, SapSystemListResponse

router = APIRouter(
    prefix="/sap-systems",
    tags=["SAP Systems"],
)


# --- ROUTES ---

@router.get("/", response_model=SapSystemListResponse)
@log_function_call
def get_sap_systems(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, gt=0),
):
    offset = (page - 1) * page_size
    stmt = select(SapSystemPriority)
    count_stmt = select(func.count()).select_from(SapSystemPriority)

    total_rows = db.execute(count_stmt).scalar_one()
    stmt = stmt.order_by(SapSystemPriority.system_name).offset(offset).limit(page_size)
    systems = db.execute(stmt).scalars().all()

    return {
        "items": systems,
        "total_rows": total_rows,
        "page": page,
        "page_size": page_size,
    }


@router.post("/", response_model=SapSystemResponse, status_code=status.HTTP_201_CREATED)
@log_function_call
def create_sap_system(data: SapSystemCreate, db: Session = Depends(get_db)):
    existing = db.get(SapSystemPriority, data.system_number)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"System with system_number '{data.system_number}' already exists.",
        )

    new_system = SapSystemPriority(**data.model_dump())
    db.add(new_system)
    db.commit()
    db.refresh(new_system)
    return new_system


@router.put("/{system_number}", response_model=SapSystemResponse)
@log_function_call
def update_sap_system(system_number: str, data: SapSystemUpdate, db: Session = Depends(get_db)):
    db_system = db.get(SapSystemPriority, system_number)
    if not db_system:
        raise HTTPException(status_code=404, detail="SAP system not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_system, key, value)

    db.commit()
    db.refresh(db_system)
    return db_system


@router.delete("/{system_number}", status_code=status.HTTP_204_NO_CONTENT)
@log_function_call
def delete_sap_system(system_number: str, db: Session = Depends(get_db)):
    db_system = db.get(SapSystemPriority, system_number)
    if not db_system:
        raise HTTPException(status_code=404, detail="SAP system not found")
    db.delete(db_system)
    db.commit()
    return {"ok": True}