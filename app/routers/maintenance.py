from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, desc, func
from typing import List, Optional
from decorators import log_function_call

from app.db import get_db
from app.models.maintenance import Maintenance, MaintenanceStatus
from app.schemas.maintenance import MaintenanceCreate, MaintenanceResponse, MaintenanceUpdate, MaintenanceListResponse
 
router = APIRouter(
    prefix="/maintenance",
    tags=["Maintenance Windows"],
)

@log_function_call
def calculate_status(start_dt: datetime, end_dt: datetime) -> MaintenanceStatus:
    now = datetime.utcnow()
    if start_dt <= now and end_dt >= now:
        return MaintenanceStatus.ONGOING
    elif end_dt < now:
        return MaintenanceStatus.COMPLETED
    return MaintenanceStatus.SCHEDULED

@router.get("/", response_model=MaintenanceListResponse)
@log_function_call
def get_all_maintenances(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, gt=0, le=100),
    sort_by: str = Query("start_datetime"),
    sort_dir: str = Query("desc"),
    groups: Optional[List[str]] = Query(None, description="Filter by one or more server groups")
):
    offset = (page - 1) * page_size
    
    sort_column = getattr(Maintenance, sort_by, Maintenance.start_datetime)
    
    if sort_dir.lower() == 'desc':
        sort_expression = desc(sort_column)
    else:
        sort_expression = sort_column
    
    # Base query for counting
    count_stmt = select(func.count()).select_from(Maintenance)
    
    # Apply Group Filter to Count
    if groups:
        count_stmt = count_stmt.where(Maintenance.server_group.in_(groups))
        
    total_rows = db.execute(count_stmt).scalar_one()
    
    # Base query for fetching data
    stmt = select(Maintenance)
    
    # Apply Group Filter to Data Query
    if groups:
        stmt = stmt.where(Maintenance.server_group.in_(groups))
        
    stmt = (
        stmt
        .order_by(sort_expression)
        .offset(offset)
        .limit(page_size)
    )
    maintenances = db.execute(stmt).scalars().all()

    return {
        "items": maintenances,
        "total_rows": total_rows,
        "page": page,
        "page_size": page_size
    }
 
@router.post("/", response_model=List[MaintenanceResponse], status_code=status.HTTP_201_CREATED)
@log_function_call
def create_maintenance(
    maintenance_data: MaintenanceCreate,
    db: Session = Depends(get_db)
):
    #Validation
    if maintenance_data.start_datetime >= maintenance_data.end_datetime:
        raise HTTPException(status_code=400, detail="Start time must be before end time.")
        
    start_dt = maintenance_data.start_datetime.replace(microsecond=0)
    end_dt = maintenance_data.end_datetime.replace(microsecond=0)
    initial_status = calculate_status(start_dt, end_dt)

    new_records = []

    if maintenance_data.server_group.lower() == 'other':
        if not maintenance_data.other_server:
             raise HTTPException(status_code=400, detail="Other server name is required.")
             
        record = Maintenance(
            server_group=maintenance_data.server_group,
            server_name=None,
            other_server=maintenance_data.other_server,
            comments=maintenance_data.comments,
            start_datetime=start_dt,
            end_datetime=end_dt,
            status=initial_status
        )
        new_records.append(record)
    else:
        if not maintenance_data.servers:
             raise HTTPException(status_code=400, detail="At least one server must be selected.")
             
        for server in maintenance_data.servers:
            record = Maintenance(
                server_group=maintenance_data.server_group,
                server_name=server,
                other_server=None,
                comments=maintenance_data.comments,
                start_datetime=start_dt,
                end_datetime=end_dt,
                status=initial_status
            )
            new_records.append(record)

    db.add_all(new_records)
    db.commit()

    for r in new_records:
        db.refresh(r)
        
    return new_records

@router.put("/{maintenance_id}", response_model=MaintenanceResponse)
@log_function_call
def update_maintenance(
    maintenance_id: int,
    maintenance_data: MaintenanceUpdate,
    db: Session = Depends(get_db)
):
    db_maintenance = db.get(Maintenance, maintenance_id)
    if not db_maintenance:
        raise HTTPException(status_code=404, detail="Maintenance not found")
 
    update_data = maintenance_data.model_dump(exclude_unset=True)
    
    if 'start_datetime' in update_data:
        update_data['start_datetime'] = update_data['start_datetime'].replace(microsecond=0)
    if 'end_datetime' in update_data:
        update_data['end_datetime'] = update_data['end_datetime'].replace(microsecond=0)

    for key, value in update_data.items():
        setattr(db_maintenance, key, value)
 
    # Recalculate status
    db_maintenance.status = calculate_status(db_maintenance.start_datetime, db_maintenance.end_datetime)

    db.commit()
    db.refresh(db_maintenance)
    return db_maintenance
 
@router.delete("/{maintenance_id}", status_code=status.HTTP_204_NO_CONTENT)
@log_function_call
def delete_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db)
):
    stmt = delete(Maintenance).where(Maintenance.id == maintenance_id)
    result = db.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    db.commit()
    return {"ok": True}