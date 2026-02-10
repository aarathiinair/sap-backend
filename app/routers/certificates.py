from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, desc, func
from typing import List, Optional
from datetime import datetime
from decorators import log_function_call

from app.db import get_db
from app.models.certificates import Certificate, CertificateStatus
from app.models.config import WebhookMapping
from app.schemas.certificates import CertificateCreate, CertificateResponse, CertificateUpdate, CertificateListResponse

router = APIRouter(
    prefix="/certificates",
    tags=["Certificates"],
)

# --- HELPER FUNCTIONS ---

def validate_mapping_value(value: str, field_label: str, db: Session):
    """
    Checks if a value exists in the WebhookMapping table's channel_name column.
    Used for both Teams Channel and Responsible Group validation.
    """
    stmt = select(WebhookMapping).where(WebhookMapping.channel_name == value)
    mapping = db.execute(stmt).scalar_one_or_none()
    
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{value}' is an unknown {field_label}. Please add it on the Configuration screen first."
        )

def calculate_status(expiry_dt: datetime) -> CertificateStatus:
    now = datetime.now().replace(microsecond=0)
    if expiry_dt.tzinfo is not None:
        expiry_dt = expiry_dt.astimezone().replace(tzinfo=None)
    
    if expiry_dt < now:
        return CertificateStatus.EXPIRED
    elif (expiry_dt - now).days <= 14:
        return CertificateStatus.EXPIRING_SOON
    
    return CertificateStatus.ACTIVE

# --- ROUTES ---

@router.get("/", response_model=CertificateListResponse)
@log_function_call
def get_certificates(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, gt=0),
    status_filter: Optional[CertificateStatus] = Query(None),
):
    offset = (page - 1) * page_size
    stmt = select(Certificate)
    count_stmt = select(func.count()).select_from(Certificate)
    
    # Apply Status Filter (Hybrid Property logic)
    if status_filter:
        stmt = stmt.where(Certificate.status == status_filter)
        count_stmt = count_stmt.where(Certificate.status == status_filter)
        
    total_rows = db.execute(count_stmt).scalar_one()
    stmt = stmt.order_by(Certificate.expiration_date.asc()).offset(offset).limit(page_size)
    certs = db.execute(stmt).scalars().all()

    return {
        "items": certs,
        "total_rows": total_rows,
        "page": page,
        "page_size": page_size
    }

@router.post("/", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
def create_certificate(cert_data: CertificateCreate, db: Session = Depends(get_db)):
    # Validate both dropdown values against the WebhookMapping table
    validate_mapping_value(cert_data.teams_channel, "Teams Channel", db)
    validate_mapping_value(cert_data.responsible_group, "Responsible Group", db)
    
    expiry_dt = cert_data.expiration_date.replace(microsecond=0)
    
    # impacted_servers is included via **cert_data.model_dump()
    new_cert = Certificate(
        **cert_data.model_dump(),
        calculated_status=calculate_status(expiry_dt)
    )
    
    db.add(new_cert)
    db.commit()
    db.refresh(new_cert)
    return new_cert

@router.put("/{cert_id}", response_model=CertificateResponse)
def update_certificate(cert_id: int, cert_data: CertificateUpdate, db: Session = Depends(get_db)):
    db_cert = db.get(Certificate, cert_id)
    if not db_cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    update_dict = cert_data.model_dump(exclude_unset=True)
    
    # Validate dropdowns if they are being updated
    if 'teams_channel' in update_dict:
        validate_mapping_value(update_dict['teams_channel'], "Teams Channel", db)
    
    if 'responsible_group' in update_dict:
        validate_mapping_value(update_dict['responsible_group'], "Responsible Group", db)
    
    for key, value in update_dict.items():
        if key == 'expiration_date':
            value = value.replace(microsecond=0)
        setattr(db_cert, key, value)
    
    # Recalculate status
    db_cert.calculated_status = calculate_status(db_cert.expiration_date)
    
    db.commit()
    db.refresh(db_cert)
    return db_cert

@router.delete("/{cert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certificate(cert_id: int, db: Session = Depends(get_db)):
    db_cert = db.get(Certificate, cert_id)
    if not db_cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    db.delete(db_cert)
    db.commit()
    return {"ok": True}